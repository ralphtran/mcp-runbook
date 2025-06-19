import pytest
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from src.server import setup_server, mcp
from src.models import ConfigFile, Tool, Step, Secret


@pytest.fixture(autouse=True)
def mock_mcp():
    # Mock the mcp module for all tests
    sys.modules['mcp'] = MagicMock()
    sys.modules['mcp.server'] = MagicMock()
    sys.modules['mcp.server.fastmcp'] = MagicMock()
    yield


@pytest.fixture
def mock_keyring():
    with patch("keyring.get_password") as mock_get:
        mock_get.return_value = "test_secret"
        yield mock_get


@pytest.fixture
def mock_subprocess():
    with patch("asyncio.create_subprocess_shell") as mock_sub:
        process = MagicMock()
        # Mock communicate as a coroutine that returns (b"out", b"err")
        process.communicate = AsyncMock(return_value=(b"out", b"err"))
        process.returncode = 0
        mock_sub.return_value = process
        yield mock_sub


@pytest.fixture
def minimal_config() -> ConfigFile:
    secret = Secret(source="test_secret", target="TEST_SECRET")
    step = Step(name="test_step", command="echo hello")
    tool = Tool(
        name="test-tool",
        description="Test tool",
        secrets=[secret],
        steps=[step]
    )
    return ConfigFile(version="0.1", tools=[tool])


@patch.object(mcp, "tool")
def test_setup_server_registration(mock_tool, minimal_config) -> None:
    """Test server registers decorated tools"""
    setup_server(minimal_config)

    # mock_tool is the decorator
    mock_tool.assert_called_once()
    # Tools are registered in src.server module
    import src.server
    assert hasattr(src.server, "test_tool")


@pytest.mark.asyncio
async def test_tool_execution(
    minimal_config,
    mock_keyring,
    mock_subprocess
) -> None:
    """Test tool logic executes without errors"""
    setup_server(minimal_config)
    import src.server
    test_tool = getattr(src.server, "test_tool")

    await test_tool(filename="test.txt", content="data")

    mock_keyring.assert_called_once_with("mcp-tools", "test_secret")
    mock_subprocess.assert_called_once_with(
        "echo hello",
        cwd=os.getcwd(),
        env={**os.environ, "TEST_SECRET": "test_secret"},
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
