import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import Parser  # noqa: E402
from src.server import setup_server, mcp, run_single_tool  # noqa: E402


async def run_tool_async(config, tool_name: str) -> None:
    tool = next((t for t in config.tools if t.name == tool_name), None)
    if not tool:
        print(f"❌ Tool '{tool_name}' not found in configuration")
        sys.exit(1)

    try:
        output = await run_single_tool(tool)
        print(output)
        print(f"✅ Successfully executed tool '{tool_name}'")
    except Exception as e:
        print(f"⛔ Error running tool: {str(e)}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Runbook Config Processor"
    )
    parser.add_argument(
        '-f',
        '--file',
        required=True,
        help='Path to YAML config file'
    )
    parser.add_argument(
        '--server',
        action='store_true',
        help='Start MCP server mode'
    )
    parser.add_argument(
        '--run',
        type=str,
        help='Run a specific tool by name'
    )
    args = parser.parse_args()

    # Process config file
    config = Parser.parse_config(Path(args.file))

    if args.server:
        setup_server(config)
        print(f"🛫 Starting MCP server with {len(config.tools)} tools...")
        try:
            mcp.run(transport='stdio')
        except Exception as e:
            print(f"⛔ Server error: {str(e)}")
            sys.exit(1)

    elif args.run:
        asyncio.run(run_tool_async(config, args.run))

    else:
        print(
            "✅ Successfully parsed config: Version "
            f"{config.version}, {len(config.tools)} tools found"
        )


if __name__ == "__main__":
    main()
