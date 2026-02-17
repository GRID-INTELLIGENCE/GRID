#!/usr/bin/env python3
"""
MCP Configuration Path Validator.

Validates that all paths in mcp_config.json are valid and secure.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from grid.security.path_manager import SecurePathManager

    PATH_MANAGER_AVAILABLE = True
except ImportError:
    PATH_MANAGER_AVAILABLE = False
    print("Warning: SecurePathManager not available, using basic validation")


def validate_mcp_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    Validate MCP configuration file paths.

    Args:
        config_path: Path to mcp_config.json (defaults to mcp-setup/mcp_config.json)

    Returns:
        Dictionary with validation results
    """
    if config_path is None:
        config_path = project_root / "mcp-setup" / "mcp_config.json"

    if not config_path.exists():
        return {
            "success": False,
            "error": f"MCP config file not found: {config_path}",
        }

    results: dict[str, Any] = {
        "success": True,
        "config_path": str(config_path),
        "servers_validated": 0,
        "servers_with_issues": 0,
        "issues": [],
        "warnings": [],
    }

    try:
        with open(config_path) as f:
            config = json.load(f)

        if "servers" not in config:
            return {
                "success": False,
                "error": "MCP config missing 'servers' key",
            }

        manager = SecurePathManager(base_dir=project_root) if PATH_MANAGER_AVAILABLE else None

        for server in config.get("servers", []):
            server_name = server.get("name", "unknown")
            results["servers_validated"] += 1
            server_issues: list[str] = []

            # Validate cwd
            cwd = server.get("cwd")
            if cwd:
                try:
                    cwd_path = Path(cwd)
                    if not cwd_path.exists():
                        server_issues.append(f"cwd does not exist: {cwd}")
                    elif not cwd_path.is_dir():
                        server_issues.append(f"cwd is not a directory: {cwd}")
                except Exception as e:
                    server_issues.append(f"Invalid cwd path '{cwd}': {e}")

            # Validate PYTHONPATH entries
            env = server.get("env", {})
            pythonpath = env.get("PYTHONPATH", "")
            if pythonpath:
                # Split by platform-appropriate separator
                import os

                if os.name == "nt":  # Windows
                    paths = pythonpath.split(";")
                else:  # Unix-like
                    paths = pythonpath.split(":")

                for path_str in paths:
                    if not path_str.strip():
                        continue

                    try:
                        path = Path(path_str.strip())
                        if manager:
                            # Use SecurePathManager for validation
                            result = manager.validate_path(path)
                            if not result.is_valid:
                                server_issues.append(f"Invalid PYTHONPATH entry '{path_str}': {result.reason}")
                        else:
                            # Basic validation
                            if not path.exists():
                                server_issues.append(f"PYTHONPATH entry does not exist: {path_str}")
                            elif not path.is_dir():
                                server_issues.append(f"PYTHONPATH entry is not a directory: {path_str}")
                    except Exception as e:
                        server_issues.append(f"Error validating PYTHONPATH entry '{path_str}': {e}")

            # Validate command path
            command = server.get("command")
            if command:
                try:
                    cmd_path = Path(command)
                    if not cmd_path.exists():
                        server_issues.append(f"Command executable does not exist: {command}")
                    elif not cmd_path.is_file():
                        server_issues.append(f"Command is not a file: {command}")
                except Exception as e:
                    server_issues.append(f"Invalid command path '{command}': {e}")

            if server_issues:
                results["servers_with_issues"] += 1
                results["issues"].append(
                    {
                        "server": server_name,
                        "issues": server_issues,
                    }
                )

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON in config file: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error validating config: {e}",
        }

    return results


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate MCP configuration paths")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to mcp_config.json (defaults to mcp-setup/mcp_config.json)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    results = validate_mcp_config(args.config)

    if args.json:
        import json

        print(json.dumps(results, indent=2))
    else:
        print("=" * 70)
        print("MCP Configuration Path Validation")
        print("=" * 70)
        print()

        if not results["success"]:
            print(f"❌ Validation failed: {results.get('error', 'Unknown error')}")
            return 1

        print(f"Config file: {results['config_path']}")
        print(f"Servers validated: {results['servers_validated']}")
        print(f"Servers with issues: {results['servers_with_issues']}")
        print()

        if results["issues"]:
            print("Issues found:")
            print("-" * 70)
            for issue_group in results["issues"]:
                print(f"Server: {issue_group['server']}")
                for issue in issue_group["issues"]:
                    print(f"  ⚠️  {issue}")
                print()
        else:
            print("✅ All paths validated successfully!")
            print()

        if results.get("warnings"):
            print("Warnings:")
            for warning in results["warnings"]:
                print(f"  ⚠️  {warning}")

        print("=" * 70)

    return 0 if results["success"] and results["servers_with_issues"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
