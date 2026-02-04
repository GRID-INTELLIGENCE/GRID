#!/usr/bin/env python3
"""
GRID Code Analysis MCP Server
Provides static analysis, code quality checks, and security scanning
"""
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List


def run_command(cmd: List[str], cwd: str = None) -> Dict[str, Any]:
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def analyze_code(file_path: str) -> Dict[str, Any]:
    """Analyze a Python file for code quality issues"""
    path = Path(file_path)
    if not path.exists():
        return {"error": "File not found"}

    results = {
        "file": str(path),
        "ruff": None,
        "mypy": None,
        "black_check": None
    }

    # Ruff linting
    ruff_result = run_command(["ruff", "check", str(path)])
    results["ruff"] = ruff_result

    # MyPy type checking
    mypy_result = run_command(["mypy", str(path), "--ignore-missing-imports"])
    results["mypy"] = mypy_result

    # Black format check
    black_result = run_command(["black", "--check", str(path)])
    results["black_check"] = black_result

    return results


def check_security(file_path: str) -> Dict[str, Any]:
    """Check for security issues in a file"""
    path = Path(file_path)
    if not path.exists():
        return {"error": "File not found"}

    content = path.read_text()
    issues = []

    # Check for hardcoded secrets
    secret_patterns = [
        "api_key",
        "secret_key",
        "password",
        "token",
        "private_key"
    ]

    for pattern in secret_patterns:
        if pattern in content.lower():
            issues.append({
                "type": "potential_secret",
                "pattern": pattern,
                "severity": "high"
            })

    # Check for dangerous imports
    dangerous_imports = [
        "eval(",
        "exec(",
        "os.system(",
        "subprocess.call(",
        "pickle.loads("
    ]

    for imp in dangerous_imports:
        if imp in content:
            issues.append({
                "type": "dangerous_function",
                "function": imp,
                "severity": "medium"
            })

    return {
        "file": str(path),
        "issues": issues,
        "total_issues": len(issues)
    }


def get_complexity(file_path: str) -> Dict[str, Any]:
    """Get code complexity metrics"""
    path = Path(file_path)
    if not path.exists():
        return {"error": "File not found"}

    content = path.read_text()
    lines = content.split('\n')

    return {
        "file": str(path),
        "total_lines": len(lines),
        "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
        "blank_lines": len([l for l in lines if not l.strip()]),
        "comment_lines": len([l for l in lines if l.strip().startswith('#')])
    }


def main():
    """Main MCP server loop"""
    while True:
        try:
            line = input()
            if not line:
                continue

            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})

            response = {
                "jsonrpc": "2.0",
                "id": request.get("id")
            }

            if method == "tools/list":
                response["result"] = {
                    "tools": [
                        {
                            "name": "analyze_code",
                            "description": "Analyze Python code for quality issues",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {"type": "string"}
                                },
                                "required": ["file_path"]
                            }
                        },
                        {
                            "name": "check_security",
                            "description": "Check for security issues",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {"type": "string"}
                                },
                                "required": ["file_path"]
                            }
                        },
                        {
                            "name": "get_complexity",
                            "description": "Get code complexity metrics",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {"type": "string"}
                                },
                                "required": ["file_path"]
                            }
                        }
                    ]
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

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
                response["result"] = {
                    "capabilities": {
                        "tools": {}
                    }
                }

            elif method == "shutdown":
                break

            else:
                response["error"] = {"code": -32601, "message": "Method not found"}

            print(json.dumps(response))
            sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
