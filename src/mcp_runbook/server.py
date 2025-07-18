import asyncio
import inspect
import logging
import keyring
import os
from typing import Any, Callable, Coroutine, Dict, List
from mcp.server.fastmcp import FastMCP
from mcp_runbook.models import ConfigFile, Tool, Step
from jinja2 import Environment, StrictUndefined

# Set up logger for this module
logger = logging.getLogger(__name__)

mcp = FastMCP("MCP Server Runbook")


def _prepare_execution_env(tool: Tool) -> Dict[str, str]:
    """Create execution environment by combining OS env and tool secrets"""
    secrets_env = _fetch_secrets(tool)
    return {**os.environ, **secrets_env}


def setup_server(config_file: ConfigFile) -> None:
    """Create decorated functions for each tool in the config file."""
    for tool in config_file.tools:
        tool_logic = _create_tool_logic(tool)
        _decorate_and_register_tool(tool, tool_logic)


def _create_tool_function_with_signature(
    tool: Tool, tool_logic_inner: Callable[..., Coroutine[Any, Any, str]]
) -> Callable[..., Coroutine[Any, Any, str]]:
    """Create a tool function with the correct signature based on
    the tool's parameters.

    If the tool has parameters, build a wrapper function with the
    correct signature and annotations. Otherwise, return the inner
    function as-is.
    """
    # Build the list of Parameter objects for the function signature
    param_list: List[inspect.Parameter] = []
    if tool.parameters:
        for param_name, param in tool.parameters.items():
            default = (
                param.default if param.default is not None else inspect.Parameter.empty
            )
            parameter = inspect.Parameter(
                param_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=str,
            )
            param_list.append(parameter)

    signature = inspect.Signature(param_list)

    async def wrapper(*args, **kwargs) -> str:
        # Bind parameters to the signature
        bound = signature.bind(*args, **kwargs)
        # Apply default for missing values
        bound.apply_defaults()
        parameters_dict = bound.arguments
        # Call the inner function with the collected arguments
        return await tool_logic_inner(**parameters_dict)

    # Set details on wrapper
    wrapper.__name__ = tool_logic_inner.__name__
    wrapper.__doc__ = tool.description
    wrapper.__signature__ = signature

    return wrapper


def _create_tool_logic(tool: Tool) -> Callable[..., Coroutine[Any, Any, str]]:
    """Create the tool logic function for a given tool configuration."""
    normalized_name = tool.name.replace("-", "_")

    async def tool_logic_inner(**parameters: Dict[str, str]) -> str:
        """
        Execute the steps for a tool with given parameters and return output.
        """
        logger.info(f"🔧 Starting tool {tool.name} with parameters: {parameters}")
        base_env = _prepare_execution_env(tool)
        output_lines = []
        for i, step in enumerate(tool.steps, start=1):
            step_output = await _execute_step(
                tool, step, i, base_env, parameters, stream_output=False
            )
            # In non-streaming mode, we've captured stdout_output as a string
            if step_output:
                output_lines.append(str(step_output))

        result = "\n".join(output_lines)

        # Log the first 100 characters of output to avoid flooding logs
        result_preview = result[:100] + ("..." if len(result) > 100 else "")
        msg = f"✅ Completed tool {tool.name}. Output: {result_preview}"
        logger.info(msg)

        return result

    # Set the function's __name__ before decoration
    tool_logic_inner.__name__ = f"tool_logic_{normalized_name}"

    # Create a wrapper that has the correct signature for the tool parameters
    # If there are no parameters in the tool, tool_logic_inner will get called
    # with an empty dict.
    return _create_tool_function_with_signature(tool, tool_logic_inner)


def _fetch_secrets(tool: Tool) -> Dict[str, str]:
    """Fetch secrets for a tool from keyring."""
    secrets_env = {}
    if tool.secrets is None:
        return secrets_env
    for s in tool.secrets:
        secret_val = keyring.get_password("mcp-tools", s.source)
        if not secret_val:
            raise RuntimeError(f"❌ Secret '{s.source}' not found in keyring")
        secrets_env[s.target] = secret_val
    return secrets_env


async def _execute_step(
    tool: Tool,
    step: Step,
    step_index: int,
    base_env: Dict[str, str],
    parameters: Dict[str, str],
    *,
    stream_output: bool = False,
) -> None:
    """Execute a single step of a tool."""
    step_env = base_env.copy()
    if step.env:
        step_env.update(step.env)

    # Render command as Jinja2 template with strict undefined handling
    template = Environment(undefined=StrictUndefined).from_string(step.command)
    resolved_cmd = template.render(parameters)

    cwd = step.cwd or tool.cwd or os.getcwd()

    print(f"Step [{step_index}/{len(tool.steps)}] {step.name} is running")

    if stream_output:
        stdout_pipe = asyncio.subprocess.PIPE
        stderr_pipe = asyncio.subprocess.PIPE
    else:
        stdout_pipe = asyncio.subprocess.PIPE
        stderr_pipe = asyncio.subprocess.PIPE

    proc = await asyncio.create_subprocess_shell(
        resolved_cmd, cwd=cwd, env=step_env, stdout=stdout_pipe, stderr=stderr_pipe
    )

    if stream_output:
        # Read stdout and stderr in real-time
        # Capture both stdout and stderr separately
        stdout_io = []
        stderr_io = []

        async def capture_stream(stream, buffer, prefix=""):
            """Capture and prefix lines from a stream."""
            while True:
                line = await stream.readline()
                if not line:
                    return
                line_str = line.decode().strip()
                buffer.append(line_str)
                print(f"{prefix}{line_str}")

        # Create tasks to concurrently capture both stdout and stderr
        stdout_task = asyncio.create_task(
            capture_stream(proc.stdout, stdout_io, "[stdout] ")
        )
        stderr_task = asyncio.create_task(
            capture_stream(proc.stderr, stderr_io, "[stderr] ")
        )

        # Wait for both streams to finish capturing
        await asyncio.wait([stdout_task, stderr_task])
        returncode = await proc.wait()
        stdout_output = "\n".join(stdout_io)
    else:
        # Non-streaming mode: wait for process to complete and capture output
        stdout, stderr = await proc.communicate()
        returncode = proc.returncode
        stdout_output = stdout.decode().strip() if stdout else ""

    if returncode != 0:
        if stream_output:
            # Collect complete stderr from buffer
            if stderr_io:
                error_msg = "\n".join(stderr_io)
            else:
                error_msg = f"exit code {returncode}"
        else:
            # Capture stderr from non-streaming mode
            if stderr:
                error_msg = stderr.decode()
            else:
                error_msg = f"exit code {returncode}"
        raise RuntimeError(f"⛔ Step {step_index} failed: {error_msg}")

    return stdout_output


def _decorate_and_register_tool(
    tool: Tool, tool_logic: Callable[..., Coroutine[Any, Any, None]]
) -> None:
    """Decorate the tool function and register it in the module."""
    decorator = mcp.tool(name=tool.name, description=tool.description)
    decorated_func = decorator(tool_logic)

    sanitized_name = tool.name.replace("-", "_")
    # Do NOT override the function name - preserve the dynamically set name
    globals()[sanitized_name] = decorated_func

    # Log the tool registration
    logger.info(f"📋 Registered tool: {tool.name} with description: {tool.description}")
    return decorated_func


async def run_single_tool(tool: Tool, user_parameters: Dict[str, str]) -> str:
    """
    Execute all steps in a single tool without MCP server and return output.
    """
    logger.info(f"🔧 Starting CLI execution of tool: {tool.name}")
    # Merge default parameters with user provided parameters
    parameters = {}
    if tool.parameters:
        for name, param in tool.parameters.items():
            # First use user-provided value
            if name in user_parameters:
                parameters[name] = user_parameters[name]
            # Otherwise use default if available
            elif param.default is not None:
                parameters[name] = param.default
    base_env = _prepare_execution_env(tool)
    # We run each step, and the output is printed to stdout in real-time.
    output_lines = []
    for step_index, step in enumerate(tool.steps, start=1):
        step_output = await _execute_step(
            tool, step, step_index, base_env, parameters, stream_output=True
        )
        if step_output:
            output_lines.append(str(step_output))

    result = "\n".join(output_lines)
    logger.info(f"✅ Completed CLI execution of tool: {tool.name}")
    return result
