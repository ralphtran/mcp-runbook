#!/usr/bin/env python
"""Run the MCP server with the sample runbook for local testing.

This script is intended to be used with the MCP CLI:

    mcp dev examples/sample_server.py

It sets up the server and exposes it as a global variable 'server'.
"""

from pathlib import Path
import os
import sys
import asyncio


def main():
    """Main function to run the sample server."""
    current_dir = Path(__file__).parent.resolve()
    parent_dir = current_dir.parent

    # Add parent directory to sys.path for imports
    sys.path.insert(0, str(parent_dir))

    # Change working directory to repository root
    os.chdir(parent_dir)

    # Import after setting base directory
    from src.parser import Parser
    from src.server import mcp, setup_server

    # Load the configuration using absolute path
    config_file = Path("examples/sample-runbook.yaml")
    config = Parser.parse_config(config_file)

    # Set up the server
    setup_server(config)

    # Expose the server object for MCP CLI as "server"
    server = mcp
    return server


# Expose server as global
server = main()

# When run directly, start the server
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server.serve())
