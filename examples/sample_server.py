#!/usr/bin/env python
"""Run the MCP server with the sample runbook for local testing.

This script is intended to be used with the MCP CLI:

    mcp dev examples/sample_server.py

It sets up the server and exposes it as a global variable 'server'.
"""

from pathlib import Path
import os
import sys

# Add parent directory to Python path to import src modules
current_dir = Path(__file__).parent.resolve()
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from src.parser import Parser
from src.server import mcp, setup_server

# Change working directory to repository root
os.chdir(parent_dir)

# Load the configuration
config_file = Path("test/data/sample-runbook.yaml")
config = Parser.parse_config(config_file)

# Set up the server
setup_server(config)

# Expose the server object for MCP CLI as "server"
server = mcp
