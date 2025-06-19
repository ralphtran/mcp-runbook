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


def _create_tool_logic(tool: Tool) -> Callable[..., Coroutine[Any, Any, None]]:
    """Create the tool logic function for a given tool configuration."""
    async def tool_logic(**parameters: Dict[str, str]) -> None:
        """Execute the steps for a tool with given parameters."""
        secrets_env = _fetch_secrets(tool)
        base_env = {**os.environ, **secrets_env}

        for i, step in enumerate(tool.steps, start=1):
            await _execute_step(tool, step, i, base_env, parameters)

    return tool_logic


def _fetch_secrets(tool: Tool) -> Dict[str, str]:
    """Fetch secrets for a tool from keyring."""
    secrets_env = {}
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
    parameters: Dict[str, str]
) -> None:
    """Execute a single step of a tool."""
    step_env = base_env.copy()
    if step.env:
        step_env.update(step.env)

    resolved_cmd = step.command.format(**parameters)

    cwd = step.cwd or tool.cwd or os.getcwd()

    print(f"Step [{step_index}/{len(tool.steps)}] {step.name} is running")

    proc = await asyncio.create_subprocess_shell(
        resolved_cmd,
        cwd=cwd,
        env=step_env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        if stderr:
            error_msg = stderr.decode()
        else:
            error_msg = f"exit code {proc.returncode}"
        raise RuntimeError(f"⛔ Step {step_index} failed: {error_msg}")


def _decorate_and_register_tool(
    tool: Tool,
    tool_logic: Callable[..., Coroutine[Any, Any, None]]
) -> None:
    """Decorate the tool function and register it in the module."""
    decorator = mcp.tool(name=tool.name, description=tool.description)
    decorated_func = decorator(tool_logic)

    sanitized_name = tool.name.replace("-", "_")
    decorated_func.__name__ = sanitized_name
    globals()[sanitized_name] = decorated_func
    return decorated_func
