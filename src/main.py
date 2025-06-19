import argparse
from pathlib import Path
from src.parser import Parser
from src.server import setup_server, mcp


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
    args = parser.parse_args()

    # Process config file
    config = Parser.parse_config(Path(args.file))

    if args.server:
        setup_server(config)
        print(f"🛫 Starting MCP server with {len(config.tools)} tools...")
        mcp.run()
    else:
        print(
            "✅ Successfully parsed config: Version "
            f"{config.version}, {len(config.tools)} tools found"
        )


if __name__ == "__main__":
    main()
