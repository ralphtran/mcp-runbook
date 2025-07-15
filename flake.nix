{
  description = "A MCP Server to run user-defined runbook in commandline";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... } @ inputs:
    # Use flake-utils to generate outputs for common systems
    flake-utils.lib.eachDefaultSystem (system:
      let
        # Import packages for the specific system
        pkgs = import nixpkgs {
          inherit system;
        };
        # Define the Python version to use
        pythonPkgs = pkgs.python313.pkgs;
        # Create custom scripts
        checkScript = pkgs.writeShellScriptBin "check" ''
          ruff format
          ruff check --fix
          pytest -v
        '';
        aiScript = pkgs.writeShellScriptBin "ai" ''
          aider --test-cmd "nix develop -c check" --read docs/notes.org flake.nix
        '';
        ghPushScript = pkgs.writeShellScriptBin "push" ''
          git push gh proj/mcp-runbook:main
        '';
        buildScript = pkgs.writeShellScriptBin "build" ''
          uv build
        '';
      in {
        # Development Shell accessible via `nix develop`
        devShells.default = pkgs.mkShell {
          name = "mcp-server-runbook-dev";
          # buildInputs provides packages needed for the shell environment.
          buildInputs = [
            pythonPkgs.python        # Python 3.13
            pkgs.uv                  # For dependencies management
            pkgs.nodejs_22           # For MCP Inspector
            checkScript              # Add custom check script
            aiScript                 # Add AI assistant script
            ghPushScript             # Add push to Github script
            buildScript              # Add build script
          ];
          # Run shellHook to create virtual env and install dependencies with uv
          shellHook = ''
            uv sync
            source .venv/bin/activate
          '';
        };
      });
}
