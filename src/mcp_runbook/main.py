import argparse
import asyncio
import sys
from pathlib import Path
from typing import Dict

from .parser import Parser
from .server import setup_server, mcp, run_single_tool


async def run_tool_async(config, tool_name: str, parameters: Dict[str, str]) -> None:
    tool = next((t for t in config.tools if t.name == tool_name), None)
    if not tool:
        print(f"❌ Tool '{tool_name}' not found in configuration")
        sys.exit(1)

    try:
        output = await run_single_tool(tool, parameters)
        print(output)
        print(f"✅ Successfully executed tool '{tool_name}'")
    except Exception as e:
        print(f"⛔ Error running tool: {str(e)}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Runbook Config Processor")
    parser.add_argument("-f", "--file", required=True, help="Path to YAML config file")
    # Server mode is now the default behavior without --run
    parser.add_argument("--run", type=str, help="Run a specific tool by name")
    parser.add_argument(
        "--args", nargs="*", help="Arguments for the tool in key=value format"
    )
    args = parser.parse_args()

    # Process config file
    config = Parser.parse_config(Path(args.file))

    if args.run:
        # Parse key-value arguments
        params = {}
        if args.args:
            for arg in args.args:
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    params[key] = value
                else:
                    print(f"⚠️ Ignoring invalid argument: {arg}.")
                    print("Use key=value format")
        asyncio.run(run_tool_async(config, args.run, params))

    else:
        setup_server(config)
        print(f"🛫 Starting MCP server with {len(config.tools)} tools...")
        try:
            mcp.run(transport="stdio")
        except Exception as e:
            print(f"⛔ Server error: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
