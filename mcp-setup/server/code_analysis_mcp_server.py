#!/usr/bin/env python3
"""
GRID Code Analysis MCP Server
Provides static analysis, code quality checks, and security scanning
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

# Path containment: all file operations restricted to GRID workspace root
# plus any extra roots declared via EXTRA_ALLOWED_ROOTS (colon-separated).
GRID_ROOT = grid_root
_extra = os.environ.get("EXTRA_ALLOWED_ROOTS", "")
ALLOWED_ROOTS: list[Path] = [GRID_ROOT] + [Path(p).resolve() for p in _extra.split(":") if p.strip()]

# Initialize MCP server
server = Server("code-analysis")


def _is_under(path: Path, root: Path) -> bool:
    """Return True if *path* is equal to or a child of *root*."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_path(file_path: str) -> Path:
    """Validate that a path resolves within allowed workspace roots.

    Raises ValueError if the path escapes the boundary.
    """
    if not file_path:
        raise ValueError("file_path is required")
    original = Path(file_path)
    # Check symlink target before resolving
    if original.is_symlink():
        target = original.resolve()
        if not any(_is_under(target, root) for root in ALLOWED_ROOTS):
            raise ValueError(f"Symlink '{file_path}' targets outside allowed workspace roots. Access denied.")
    resolved = original.resolve()
    if not any(_is_under(resolved, root) for root in ALLOWED_ROOTS):
        raise ValueError(
            f"Path '{file_path}' resolves outside allowed workspace roots ({ALLOWED_ROOTS}). Access denied."
        )
    return resolved


def run_command(cmd: list[str], cwd: str = None) -> dict[str, Any]:
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_code(file_path: str) -> dict[str, Any]:
    """Analyze a Python file for code quality issues"""
    try:
        path = _validate_path(file_path)
    except ValueError as e:
        return {"error": str(e)}
    if not path.exists():
        return {"error": "File not found"}

    results = {"file": str(path), "ruff": None, "mypy": None, "black_check": None}

    # Ruff linting
    ruff_result = run_command([sys.executable, "-m", "ruff", "check", str(path)])
    results["ruff"] = ruff_result

    # MyPy type checking
    mypy_result = run_command([sys.executable, "-m", "mypy", str(path), "--ignore-missing-imports"])
    results["mypy"] = mypy_result

    # Black format check
    black_result = run_command([sys.executable, "-m", "black", "--check", str(path)])
    results["black_check"] = black_result

    return results


def check_security(file_path: str) -> dict[str, Any]:
    """Check for security issues in a file"""
    try:
        path = _validate_path(file_path)
    except ValueError as e:
        return {"error": str(e)}
    if not path.exists():
        return {"error": "File not found"}

    content = path.read_text()
    issues = []

    # Check for hardcoded secrets
    secret_patterns = ["api_key", "secret_key", "password", "token", "private_key"]

    for pattern in secret_patterns:
        if pattern in content.lower():
            issues.append({"type": "potential_secret", "pattern": pattern, "severity": "high"})

    # Check for dangerous imports
    dangerous_imports = ["eval(", "exec(", "os.system(", "subprocess.call(", "pickle.loads("]

    for imp in dangerous_imports:
        if imp in content:
            issues.append({"type": "dangerous_function", "function": imp, "severity": "medium"})

    return {"file": str(path), "issues": issues, "total_issues": len(issues)}


def get_complexity(file_path: str) -> dict[str, Any]:
    """Get code complexity metrics"""
    try:
        path = _validate_path(file_path)
    except ValueError as e:
        return {"error": str(e)}
    if not path.exists():
        return {"error": "File not found"}

    content = path.read_text()
    lines = content.split("\n")

    return {
        "file": str(path),
        "total_lines": len(lines),
        "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith("#")]),
        "blank_lines": len([l for l in lines if not l.strip()]),
        "comment_lines": len([l for l in lines if l.strip().startswith("#")]),
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="analyze_code",
            description="Analyze Python code for quality issues",
            inputSchema={
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "Path to the Python file to analyze"}},
                "required": ["file_path"],
            },
        ),
        Tool(
            name="check_security",
            description="Check for security issues",
            inputSchema={
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "Path to the file to scan"}},
                "required": ["file_path"],
            },
        ),
        Tool(
            name="get_complexity",
            description="Get code complexity metrics",
            inputSchema={
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "Path to the file to measure"}},
                "required": ["file_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "analyze_code":
            result = analyze_code(arguments.get("file_path"))
        elif name == "check_security":
            result = check_security(arguments.get("file_path"))
        elif name == "get_complexity":
            result = get_complexity(arguments.get("file_path"))
        else:
            raise ValueError(f"Unknown tool: {name}")

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def main():
    """Main server entry point."""
    logger.info("Starting GRID Code Analysis MCP Server...")

    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
