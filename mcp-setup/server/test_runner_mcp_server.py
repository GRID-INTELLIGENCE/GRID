#!/usr/bin/env python3
"""
GRID Test Runner MCP Server
Provides test execution, coverage analysis, and test discovery
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_pytest(args: list[str], cwd: str = None) -> dict[str, Any]:
    """Run pytest with given arguments"""
    cmd = ["pytest"] + args
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
    args = []
    if test_path:
        args.append(test_path)
    if verbose:
        args.append("-v")

    result = run_pytest(args)
    return result


def run_coverage(test_path: str = None, output_format: str = "term") -> dict[str, Any]:
    """Run tests with coverage"""
    args = ["--cov=src", f"--cov-report={output_format}"]
    if test_path:
        args.append(test_path)

    result = run_pytest(args)
    return result


def discover_tests(test_dir: str = "tests/") -> dict[str, Any]:
    """Discover available tests"""
    test_path = Path(test_dir)
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

            response = {"jsonrpc": "2.0", "id": request.get("id")}

            if method == "tools/list":
                response["result"] = {
                    "tools": [
                        {
                            "name": "run_tests",
                            "description": "Run pytest tests",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"test_path": {"type": "string"}, "verbose": {"type": "boolean"}},
                            },
                        },
                        {
                            "name": "run_coverage",
                            "description": "Run tests with coverage report",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "test_path": {"type": "string"},
                                    "output_format": {"type": "string", "enum": ["term", "json", "html"]},
                                },
                            },
                        },
                        {
                            "name": "discover_tests",
                            "description": "Discover available test files",
                            "inputSchema": {"type": "object", "properties": {"test_dir": {"type": "string"}}},
                        },
                        {
                            "name": "get_test_summary",
                            "description": "Get test summary without running",
                            "inputSchema": {"type": "object", "properties": {"test_path": {"type": "string"}}},
                        },
                    ]
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name == "run_tests":
                    result = run_tests(test_path=arguments.get("test_path"), verbose=arguments.get("verbose", False))
                    response["result"] = {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

                elif tool_name == "run_coverage":
                    result = run_coverage(
                        test_path=arguments.get("test_path"), output_format=arguments.get("output_format", "term")
                    )
                    response["result"] = {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

                elif tool_name == "discover_tests":
                    result = discover_tests(test_dir=arguments.get("test_dir", "tests/"))
                    response["result"] = {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

                elif tool_name == "get_test_summary":
                    result = get_test_summary(test_path=arguments.get("test_path"))
                    response["result"] = {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

                else:
                    response["error"] = {"code": -32601, "message": "Method not found"}

            elif method == "initialize":
                response["result"] = {"capabilities": {"tools": {}}}

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
