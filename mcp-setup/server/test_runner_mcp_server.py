#!/usr/bin/env python3
"""
GRID Test Runner MCP Server
Provides test execution, coverage analysis, and test discovery
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add GRID to path using SecurePathManager
grid_root = Path(__file__).resolve().parent.parent.parent
try:
    from grid.security.path_manager import SecurePathManager

    manager = SecurePathManager(base_dir=grid_root)
    manager.add_path(grid_root / "src", validate=True)
except ImportError:
    # Fallback to direct sys.path manipulation if SecurePathManager unavailable
    sys.path.insert(0, str(grid_root / "src"))

# Also add the global Python site-packages to path
import site

site.main()

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import CallToolResult, TextContent, Tool
except ImportError:
    sys.stderr.write("MCP library not found. Please install: pip install mcp\n")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path containment: all operations restricted to GRID workspace root
# plus any extra roots declared via EXTRA_ALLOWED_ROOTS (colon-separated).
GRID_ROOT = grid_root
_extra = os.environ.get("EXTRA_ALLOWED_ROOTS", "")
ALLOWED_ROOTS: list[Path] = [GRID_ROOT] + [Path(p).resolve() for p in _extra.split(":") if p.strip()]

# Initialize MCP server
server = Server("test-runner")


def _validate_path(target_path: str) -> Path:
    """Validate that a path resolves within the GRID workspace root.

    Raises ValueError if the path escapes the boundary.
    """
    if not target_path:
        raise ValueError("path is required")
    original = Path(target_path)
    # Check symlink target before resolving
    if original.is_symlink():
        target = original.resolve()
        if not any(_is_under(target, root) for root in ALLOWED_ROOTS):
            raise ValueError(f"Symlink '{target_path}' targets outside allowed workspace roots. Access denied.")
    resolved = original.resolve()
    if not any(_is_under(resolved, root) for root in ALLOWED_ROOTS):
        raise ValueError(
            f"Path '{target_path}' resolves outside allowed workspace roots ({ALLOWED_ROOTS}). Access denied."
        )
    return resolved


def _is_under(path: Path, root: Path) -> bool:
    """Return True if *path* is equal to or a child of *root*."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def run_pytest(args: list[str], cwd: str = None) -> dict[str, Any]:
    """Run pytest with given arguments"""
    cmd = [sys.executable, "-m", "pytest"] + args
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Test execution timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_tests(test_path: str = None, verbose: bool = False) -> dict[str, Any]:
    """Run tests"""
    if test_path:
        try:
            _validate_path(test_path)
        except ValueError as e:
            return {"success": False, "error": str(e)}
    args = []
    if test_path:
        args.append(test_path)
    if verbose:
        args.append("-v")

    result = run_pytest(args)
    return result


def run_coverage(test_path: str = None, output_format: str = "term") -> dict[str, Any]:
    """Run tests with coverage"""
    if test_path:
        try:
            _validate_path(test_path)
        except ValueError as e:
            return {"success": False, "error": str(e)}
    args = ["--cov=src", f"--cov-report={output_format}"]
    if test_path:
        args.append(test_path)

    result = run_pytest(args)
    return result


def discover_tests(test_dir: str = "tests/") -> dict[str, Any]:
    """Discover available tests"""
    try:
        test_path = _validate_path(test_dir)
    except ValueError as e:
        return {"error": str(e)}
    if not test_path.exists():
        return {"error": "Test directory not found"}

    test_files = list(test_path.rglob("test_*.py"))
    test_count = len(test_files)

    return {
        "test_directory": str(test_path),
        "test_files": [str(f) for f in test_files],
        "total_test_files": test_count,
    }


def get_test_summary(test_path: str = None) -> dict[str, Any]:
    """Get test summary without running"""
    if test_path:
        try:
            _validate_path(test_path)
        except ValueError as e:
            return {"test_count": 0, "output": "", "error": str(e)}
    args = ["--collect-only"]
    if test_path:
        args.append(test_path)

    result = run_pytest(args)

    # Parse output to extract test count
    test_count = 0
    if result["stdout"]:
        lines = result["stdout"].split("\n")
        for line in lines:
            if "collected" in line.lower():
                try:
                    test_count = int(line.split()[0])
                except Exception:
                    pass

    return {"test_count": test_count, "output": result["stdout"]}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="run_tests",
            description="Run pytest tests",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_path": {"type": "string", "description": "Path to test file or directory"},
                    "verbose": {"type": "boolean", "description": "Enable verbose output"},
                },
            },
        ),
        Tool(
            name="run_coverage",
            description="Run tests with coverage report",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_path": {"type": "string", "description": "Path to test file or directory"},
                    "output_format": {
                        "type": "string",
                        "enum": ["term", "json", "html"],
                        "description": "Coverage report format",
                    },
                },
            },
        ),
        Tool(
            name="discover_tests",
            description="Discover available test files",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_dir": {"type": "string", "description": "Test directory to scan (default: tests/)"},
                },
            },
        ),
        Tool(
            name="get_test_summary",
            description="Get test summary without running",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_path": {"type": "string", "description": "Path to test file or directory"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "run_tests":
            result = run_tests(test_path=arguments.get("test_path"), verbose=arguments.get("verbose", False))
        elif name == "run_coverage":
            result = run_coverage(
                test_path=arguments.get("test_path"), output_format=arguments.get("output_format", "term")
            )
        elif name == "discover_tests":
            result = discover_tests(test_dir=arguments.get("test_dir", "tests/"))
        elif name == "get_test_summary":
            result = get_test_summary(test_path=arguments.get("test_path"))
        else:
            raise ValueError(f"Unknown tool: {name}")

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def main():
    """Main server entry point."""
    logger.info("Starting GRID Test Runner MCP Server...")

    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
