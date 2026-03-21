#!/usr/bin/env python3
"""
GRID Code Analysis MCP Server
Provides static analysis, code quality checks, and security scanning
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "code-analysis"
SERVER_VERSION = "1.0.0"

# Path containment: all file operations restricted to GRID workspace root
GRID_ROOT = Path(__file__).resolve().parent.parent.parent


def _validate_path(file_path: str) -> Path:
    """Validate that a path resolves within the GRID workspace root.

    Raises ValueError if the path escapes the boundary.
    """
    if not file_path:
        raise ValueError("file_path is required")
    resolved = Path(file_path).resolve()
    try:
        resolved.relative_to(GRID_ROOT)
    except ValueError:
        raise ValueError(
            f"Path '{file_path}' resolves outside GRID workspace root ({GRID_ROOT}). Access denied."
        )
    if resolved.is_symlink():
        target = resolved.readlink().resolve()
        try:
            target.relative_to(GRID_ROOT)
        except ValueError:
            raise ValueError(
                f"Symlink '{file_path}' targets outside GRID workspace root. Access denied."
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


def build_initialize_result() -> dict[str, Any]:
    """Return a spec-compliant MCP initialize payload."""
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }


def main():
    """Main MCP server loop"""
    while True:
        try:
            line = sys.stdin.readline()
            if line == "":
                break

            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            method = request.get("method")
            params = request.get("params") or {}
            request_id = request.get("id")
            is_notification = request_id is None
            response = None

            if method == "notifications/initialized":
                continue

            if method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "analyze_code",
                                "description": "Analyze Python code for quality issues",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"file_path": {"type": "string"}},
                                    "required": ["file_path"],
                                },
                            },
                            {
                                "name": "check_security",
                                "description": "Check for security issues",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"file_path": {"type": "string"}},
                                    "required": ["file_path"],
                                },
                            },
                            {
                                "name": "get_complexity",
                                "description": "Get code complexity metrics",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"file_path": {"type": "string"}},
                                    "required": ["file_path"],
                                },
                            },
                        ]
                    },
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                response = {"jsonrpc": "2.0", "id": request_id}

                if tool_name == "analyze_code":
                    result = analyze_code(arguments.get("file_path"))
                    response["result"] = {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

                elif tool_name == "check_security":
                    result = check_security(arguments.get("file_path"))
                    response["result"] = {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

                elif tool_name == "get_complexity":
                    result = get_complexity(arguments.get("file_path"))
                    response["result"] = {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

                else:
                    response["error"] = {"code": -32601, "message": "Method not found"}

            elif method == "initialize":
                response = {"jsonrpc": "2.0", "id": request_id, "result": build_initialize_result()}

            elif method == "ping":
                response = {"jsonrpc": "2.0", "id": request_id, "result": {}}

            elif method == "shutdown":
                response = {"jsonrpc": "2.0", "id": request_id, "result": {}}
                print(json.dumps(response))
                sys.stdout.flush()
                break

            elif not is_notification:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": "Method not found"},
                }

            if response is not None:
                print(json.dumps(response))
                sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
