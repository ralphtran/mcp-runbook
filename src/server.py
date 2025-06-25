import asyncio
import keyring
import os
from typing import Any, Callable, Coroutine, Dict
from mcp.server.fastmcp import FastMCP
from src.models import ConfigFile, Tool, Step

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

    async def tool_logic_inner(**parameters: Dict[str, str]) -> None:
        """Execute the steps for a tool with given parameters."""
        secrets_env = _fetch_secrets(tool)
        base_env = {**os.environ, **secrets_env}

        for i, step in enumerate(tool.steps, start=1):
            await _execute_step(
                tool,
                step,
                i,
                base_env,
                parameters,
                stream_output=False
            )

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
        stdout_pipe = asyncio.subprocess.DEVNULL
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
        stdout_lines = []
        stderr_lines = []

        async def read_stream(stream, buffer, console_identifier=''):
            """Read lines from stream and buffer/print them."""
            output_lines = []
            while True:
                line = await stream.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                output_lines.append(line_str)
                buffer.append(line_str)
                print(f"{console_identifier}{line_str}")
            return output_lines

        # Start reading both streams concurrently
        stdout_task = asyncio.create_task(
            read_stream(proc.stdout, stdout_lines, '[stdout] ')
        )
        stderr_task = asyncio.create_task(
            read_stream(proc.stderr, stderr_lines, '[stderr] ')
        )

        # Wait for both stread to finish
        await asyncio.wait(
            [stdout_task, stderr_task],
            return_when=asyncio.ALL_COMPLETED
        )

        # Wait for process to exit after streams
        returncode = await proc.wait()
    else:
        # Non-streaming mode: wait for process to complete and capture output
        stdout, stderr = await proc.communicate()
        returncode = proc.returncode

    if returncode != 0:
        if stream_output:
            # Collect complete stderr from buffer
            error_msg = '\n'.join(stderr_lines) \
                if stderr_lines else f"exit code {returncode}"
        else:
            # Capture stderr from non-streaming mode
            error_msg = stderr.decode() \
                if stderr else f"exit code {returncode}"
        raise RuntimeError(
            f"⛔ Step {step_index} failed: {error_msg}"
        )


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
    return decorated_func


async def run_single_tool(tool: Tool) -> str:
    """
    Execute all steps in a single tool without MCP server and return output.
    """
    secrets_env = _fetch_secrets(tool)
    # Build parameters dictionary from tool's parameters with default values
    parameters = {}
    if tool.parameters:
        for name, param in tool.parameters.items():
            if param.default is not None:
                parameters[name] = param.default
    base_env = {**os.environ, **secrets_env}
    # We run each step, and the output is printed to stdout in real-time.
    for step_index, step in enumerate(tool.steps, start=1):
        await _execute_step(
            tool,
            step,
            step_index,
            base_env,
            parameters,
            stream_output=True
        )
    # Return an empty string because the output has already been printed.
    return ""
