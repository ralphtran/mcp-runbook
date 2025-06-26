import asyncio
import logging
import keyring
import os
from typing import Any, Callable, Coroutine, Dict
from mcp.server.fastmcp import FastMCP
from src.models import ConfigFile, Tool, Step

# Set up logger for this module
logger = logging.getLogger(__name__)

mcp = FastMCP("MCP Server Runbook")


def setup_server(config_file: ConfigFile) -> None:
    """Create decorated functions for each tool in the config file."""
    for tool in config_file.tools:
        tool_logic = _create_tool_logic(tool)
        _decorate_and_register_tool(tool, tool_logic)


def _create_tool_logic(
    tool: Tool
) -> Callable[..., Coroutine[Any, Any, None]]:
    """Create the tool logic function for a given tool configuration."""
    normalized_name = tool.name.replace("-", "_")

    async def tool_logic_inner(
        **parameters: Dict[str, str]
    ) -> str:
        """
        Execute the steps for a tool with given parameters and return output.
        """
        logger.info(f"🔧 Starting tool {tool.name} with parameters: \
                    {parameters}")
        secrets_env = _fetch_secrets(tool)
        base_env = {**os.environ, **secrets_env}
        output_lines = []
        for i, step in enumerate(tool.steps, start=1):
            step_output = await _execute_step(
                tool,
                step,
                i,
                base_env,
                parameters,
                stream_output=False
            )
            # In non-streaming mode, we've captured stdout_output as a string
            if step_output:
                output_lines.append(str(step_output))

        result = '\n'.join(output_lines)

        # Log the first 100 characters of output to avoid flooding logs
        result_preview = result[:100] + ("..." if len(result) > 100 else "")
        logger.info(f"✅ Completed tool {tool.name}. Output: {result_preview}")

        return result

    # Set the function's __name__ before decoration
    tool_logic_inner.__name__ = f"tool_logic_{normalized_name}"
    return tool_logic_inner


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
    stream_output: bool = False
) -> None:
    """Execute a single step of a tool."""
    step_env = base_env.copy()
    if step.env:
        step_env.update(step.env)

    resolved_cmd = step.command.format(**parameters)

    cwd = step.cwd or tool.cwd or os.getcwd()

    print(
        f"Step [{step_index}/{len(tool.steps)}] {step.name} is running"
    )

    if stream_output:
        stdout_pipe = asyncio.subprocess.PIPE
        stderr_pipe = asyncio.subprocess.PIPE
    else:
        stdout_pipe = asyncio.subprocess.PIPE
        stderr_pipe = asyncio.subprocess.PIPE

    proc = await asyncio.create_subprocess_shell(
        resolved_cmd,
        cwd=cwd,
        env=step_env,
        stdout=stdout_pipe,
        stderr=stderr_pipe
    )

    if stream_output:
        # Read stdout and stderr in real-time
        # Capture both stdout and stderr separately
        stdout_io = []
        stderr_io = []

        async def capture_stream(stream, buffer, prefix=''):
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
            capture_stream(proc.stdout, stdout_io, '[stdout] ')
        )
        stderr_task = asyncio.create_task(
            capture_stream(proc.stderr, stderr_io, '[stderr] ')
        )

        # Wait for both streams to finish capturing
        await asyncio.wait([stdout_task, stderr_task])
        returncode = await proc.wait()
        stdout_output = '\n'.join(stdout_io)
    else:
        # Non-streaming mode: wait for process to complete and capture output
        stdout, stderr = await proc.communicate()
        returncode = proc.returncode
        stdout_output = stdout.decode().strip() if stdout else ""

    if returncode != 0:
        if stream_output:
            # Collect complete stderr from buffer
            if stderr_io:
                error_msg = '\n'.join(stderr_io)
            else:
                error_msg = f"exit code {returncode}"
        else:
            # Capture stderr from non-streaming mode
            if stderr:
                error_msg = stderr.decode()
            else:
                error_msg = f"exit code {returncode}"
        raise RuntimeError(
            f"⛔ Step {step_index} failed: {error_msg}"
        )

    return stdout_output


def _decorate_and_register_tool(
    tool: Tool,
    tool_logic: Callable[..., Coroutine[Any, Any, None]]
) -> None:
    """Decorate the tool function and register it in the module."""
    decorator = mcp.tool(name=tool.name, description=tool.description)
    decorated_func = decorator(tool_logic)

    sanitized_name = tool.name.replace("-", "_")
    # Do NOT override the function name - preserve the dynamically set name
    globals()[sanitized_name] = decorated_func

    # Log the tool registration
    logger.info(f"📋 Registered tool: {tool.name} with description: \
                {tool.description}")
    return decorated_func


async def run_single_tool(tool: Tool) -> str:
    """
    Execute all steps in a single tool without MCP server and return output.
    """
    logger.info(f"🔧 Starting CLI execution of tool: {tool.name}")
    secrets_env = _fetch_secrets(tool)
    # Build parameters dictionary from tool's parameters with default values
    parameters = {}
    if tool.parameters:
        for name, param in tool.parameters.items():
            if param.default is not None:
                parameters[name] = param.default
    base_env = {**os.environ, **secrets_env}
    # We run each step, and the output is printed to stdout in real-time.
    output_lines = []
    for step_index, step in enumerate(tool.steps, start=1):
        step_output = await _execute_step(
            tool,
            step,
            step_index,
            base_env,
            parameters,
            stream_output=True
        )
        if step_output:
            output_lines.append(str(step_output))

    result = '\n'.join(output_lines)
    logger.info(f"✅ Completed CLI execution of tool: {tool.name}")
    return result
