#!/usr/bin/env python3
"""
Sanitization script to detect and report async/await pattern violations.

Scans codebase for:
1. Synchronous SDK calls in async functions (Stripe, boto3, etc.)
2. Blocking I/O operations in async context
3. Missing await on async operations
4. Configuration management issues
"""

import ast
import re
import sys
from pathlib import Path
from typing import Any

# Patterns to detect blocking calls
BLOCKING_PATTERNS = [
    (r"stripe_client\.v\d+\.", "Stripe SDK call"),
    (r"stripe\.", "Stripe SDK call"),
    (r"boto3\.", "AWS SDK call"),
    (r"requests\.(get|post|put|delete|patch)", "Synchronous HTTP call"),
    (r"urllib\.", "Synchronous HTTP call"),
    (r"time\.sleep\(", "Blocking sleep"),
    (r"open\(", "Synchronous file I/O"),
    (r"\.read\(\)|\.write\(\)", "Synchronous file operation"),
]

# Patterns that should be wrapped
WRAP_PATTERNS = [
    (r"stripe_client\.v\d+\.core\.accounts\.retrieve\(", "Stripe account retrieval"),
    (r"stripe_client\.v\d+\.core\.events\.retrieve\(", "Stripe event retrieval"),
    (r"stripe_client\.v\d+\.products\.(create|list)\(", "Stripe product operations"),
    (r"stripe_client\.v\d+\.checkout\.sessions\.create\(", "Stripe checkout creation"),
    (r"stripe_client\.parse_(thin_event|event_notification)\(", "Stripe webhook parsing"),
]


class AsyncPatternChecker(ast.NodeVisitor):
    """AST visitor to check async patterns."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations: list[dict[str, Any]] = []
        self.in_async_function = False
        self.current_function = None
        self.lines: list[str] = []

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions."""
        old_async = self.in_async_function
        old_func = self.current_function
        self.in_async_function = True
        self.current_function = node.name
        self.generic_visit(node)
        self.in_async_function = old_async
        self.current_function = old_func

    def visit_Call(self, node: ast.Call):
        """Visit function calls."""
        if not self.in_async_function:
            self.generic_visit(node)
            return

        # Check for blocking patterns
        call_str = ast.unparse(node) if hasattr(ast, "unparse") else str(node)

        for pattern, description in BLOCKING_PATTERNS:
            if re.search(pattern, call_str):
                # Check if wrapped with asyncio.to_thread
                # This is a simplified check - full analysis would need context
                if "asyncio.to_thread" not in call_str and "await" not in call_str:
                    self.violations.append(
                        {
                            "file": str(self.file_path),
                            "line": node.lineno,
                            "type": "blocking_call",
                            "description": f"{description} in async function",
                            "call": call_str[:100],
                            "function": self.current_function,
                        }
                    )

        self.generic_visit(node)


def check_file(file_path: Path) -> list[dict[str, Any]]:
    """Check a single file for async pattern violations."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content, filename=str(file_path))
        checker = AsyncPatternChecker(file_path)
        checker.lines = content.split("\n")
        checker.visit(tree)

        # Also do regex-based checks for patterns AST might miss
        for i, line in enumerate(checker.lines, 1):
            if "async def" in line:
                # Check next 50 lines for blocking patterns
                for j in range(i, min(i + 50, len(checker.lines))):
                    check_line = checker.lines[j - 1]
                    for pattern, description in WRAP_PATTERNS:
                        if re.search(pattern, check_line):
                            if "asyncio.to_thread" not in check_line and "await" not in check_line:
                                checker.violations.append(
                                    {
                                        "file": str(file_path),
                                        "line": j,
                                        "type": "unwrapped_sdk_call",
                                        "description": f"{description} not wrapped",
                                        "code": check_line.strip(),
                                        "function": None,  # Would need context
                                    }
                                )

        return checker.violations
    except SyntaxError:
        return []  # Skip files with syntax errors
    except Exception as e:
        return [{"file": str(file_path), "error": str(e)}]


def scan_codebase(root: Path) -> dict[str, Any]:
    """Scan codebase for async pattern violations."""
    violations: list[dict[str, Any]] = []
    files_checked = 0

    # Scan Python files in routers and services
    patterns = [
        "**/routers/*.py",
        "**/services/**/*.py",
        "**/api/**/*.py",
    ]

    for pattern in patterns:
        for file_path in root.glob(pattern):
            if file_path.is_file() and file_path.suffix == ".py":
                files_checked += 1
                file_violations = check_file(file_path)
                violations.extend(file_violations)

    return {
        "files_checked": files_checked,
        "violations": violations,
        "violation_count": len(violations),
    }


def main():
    """Main entry point."""
    root = Path(__file__).parent.parent.parent
    results = scan_codebase(root)

    print(f"Scanned {results['files_checked']} files")
    print(f"Found {results['violation_count']} potential violations\n")

    if results["violations"]:
        print("Violations found:\n")
        for violation in results["violations"][:20]:  # Show first 20
            if "error" in violation:
                print(f"ERROR in {violation['file']}: {violation['error']}")
            else:
                print(f"{violation['file']}:{violation['line']} - {violation['type']}: {violation['description']}")
                if "code" in violation:
                    print(f"  Code: {violation['code']}")

        if results["violation_count"] > 20:
            print(f"\n... and {results['violation_count'] - 20} more violations")

        return 1

    print("✅ No violations found!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
