"""
Automated Security Integration Script
======================================
Automatically integrates network security into existing codebase by:
1. Scanning for network-related imports and usage
2. Adding security imports where needed
3. Generating integration report
4. Providing recommendations for manual adjustments

Usage:
    python security/integrate_security.py --scan       # Scan codebase
    python security/integrate_security.py --integrate  # Apply patches
    python security/integrate_security.py --report     # Generate report
"""

import argparse
import ast
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


class NetworkUsageScanner(ast.NodeVisitor):
    """AST visitor to detect network-related code."""

    def __init__(self):
        self.imports = []
        self.network_calls = []
        self.websocket_usage = []
        self.current_function = None

    def visit_Import(self, node):
        for alias in node.names:
            if any(
                lib in alias.name
                for lib in [
                    "requests",
                    "httpx",
                    "aiohttp",
                    "urllib",
                    "socket",
                    "websocket",
                ]
            ):
                self.imports.append(
                    {"name": alias.name, "asname": alias.asname, "line": node.lineno}
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and any(
            lib in node.module
            for lib in [
                "requests",
                "httpx",
                "aiohttp",
                "urllib",
                "socket",
                "websocket",
                "fastapi",
            ]
        ):
            for alias in node.names:
                self.imports.append(
                    {
                        "module": node.module,
                        "name": alias.name,
                        "asname": alias.asname,
                        "line": node.lineno,
                    }
                )
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None

    def visit_AsyncFunctionDef(self, node):
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        # Detect network calls
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in [
                "get",
                "post",
                "put",
                "delete",
                "patch",
                "request",
                "urlopen",
                "connect",
            ]:
                self.network_calls.append(
                    {
                        "function": self.current_function,
                        "method": node.func.attr,
                        "line": node.lineno,
                    }
                )

        # Detect WebSocket usage
        if isinstance(node.func, ast.Name):
            if "websocket" in node.func.id.lower():
                self.websocket_usage.append(
                    {"function": self.current_function, "line": node.lineno}
                )

        self.generic_visit(node)


class SecurityIntegrator:
    """Integrates security system into codebase."""

    def __init__(self, root_path: str = "E:\\"):
        self.root_path = Path(root_path)
        self.security_path = self.root_path / "security"
        self.scan_results = defaultdict(list)
        self.integration_points = []
        self.exclude_dirs = {
            "__pycache__",
            ".git",
            ".pytest_cache",
            "node_modules",
            "venv",
            "env",
            ".venv",
            "security",  # Don't scan security itself
            "$RECYCLE.BIN",
        }

    def scan_codebase(self) -> dict:
        """Scan entire codebase for network usage."""
        print("🔍 Scanning codebase for network usage...")
        print(f"   Root: {self.root_path}")
        print()

        python_files = []
        for root, dirs, files in os.walk(self.root_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        total_files = len(python_files)
        print(f"📁 Found {total_files} Python files")
        print()

        for i, filepath in enumerate(python_files, 1):
            if i % 50 == 0:
                print(f"   Progress: {i}/{total_files} files scanned...")

            try:
                self._scan_file(filepath)
            except Exception as e:
                self.scan_results["errors"].append(
                    {"file": str(filepath), "error": str(e)}
                )

        print(f"✅ Scan complete: {total_files} files analyzed")
        print()
        return self._summarize_results()

    def _scan_file(self, filepath: Path):
        """Scan a single Python file."""
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content, filename=str(filepath))
            scanner = NetworkUsageScanner()
            scanner.visit(tree)

            # Record findings
            relative_path = filepath.relative_to(self.root_path)

            if scanner.imports:
                self.scan_results["files_with_network_imports"].append(
                    {
                        "file": str(relative_path),
                        "imports": scanner.imports,
                        "network_calls": scanner.network_calls,
                        "websocket_usage": scanner.websocket_usage,
                    }
                )

            if scanner.network_calls:
                self.scan_results["files_with_network_calls"].append(
                    {"file": str(relative_path), "calls": scanner.network_calls}
                )

            if scanner.websocket_usage:
                self.scan_results["files_with_websockets"].append(
                    {"file": str(relative_path), "usage": scanner.websocket_usage}
                )

            # Check for main/entry points
            if "main" in filepath.name or "__main__" in content:
                self.scan_results["entry_points"].append(str(relative_path))

        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception:
            raise

    def _summarize_results(self) -> dict:
        """Summarize scan results."""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_files_scanned": sum(
                len(v) for k, v in self.scan_results.items() if k.startswith("files_")
            ),
            "files_with_network_imports": len(
                self.scan_results["files_with_network_imports"]
            ),
            "files_with_network_calls": len(
                self.scan_results["files_with_network_calls"]
            ),
            "files_with_websockets": len(self.scan_results["files_with_websockets"]),
            "entry_points": len(self.scan_results["entry_points"]),
            "errors": len(self.scan_results["errors"]),
            "details": dict(self.scan_results),
        }

        return summary

    def generate_report(self, output_file: str = None) -> str:
        """Generate integration report."""
        if output_file is None:
            output_file = (
                self.security_path
                / "logs"
                / f"integration_report_{int(datetime.utcnow().timestamp())}.json"
            )

        summary = self._summarize_results()

        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"📄 Report saved to: {output_file}")
        return str(output_file)

    def print_report(self):
        """Print human-readable report."""
        summary = self._summarize_results()

        print("=" * 80)
        print("🔒 NETWORK SECURITY INTEGRATION REPORT")
        print("=" * 80)
        print()

        print("📊 SUMMARY:")
        print(f"   Files with network imports: {summary['files_with_network_imports']}")
        print(f"   Files with network calls:   {summary['files_with_network_calls']}")
        print(f"   Files with WebSockets:      {summary['files_with_websockets']}")
        print(f"   Entry points found:         {summary['entry_points']}")
        print(f"   Errors during scan:         {summary['errors']}")
        print()

        # Top files by network usage
        if self.scan_results["files_with_network_imports"]:
            print("🌐 TOP FILES WITH NETWORK USAGE:")
            for item in self.scan_results["files_with_network_imports"][:10]:
                file = item["file"]
                imports = len(item["imports"])
                calls = len(item["network_calls"])
                print(f"   {file}")
                print(f"      Imports: {imports}, Calls: {calls}")
            print()

        # Entry points
        if self.scan_results["entry_points"]:
            print("🚀 RECOMMENDED INTEGRATION POINTS:")
            print("   Add security import to these files:")
            for entry_point in self.scan_results["entry_points"][:10]:
                print(f"   - {entry_point}")
            print()

        # WebSocket usage
        if self.scan_results["files_with_websockets"]:
            print("🔌 FILES WITH WEBSOCKET USAGE:")
            for item in self.scan_results["files_with_websockets"][:10]:
                print(f"   - {item['file']}")
            print()

        print("=" * 80)
        print()
        print("📋 NEXT STEPS:")
        print()
        print("1. Review the scan results above")
        print("2. Add 'import security' to main entry points")
        print("3. Configure whitelist in security/network_access_control.yaml")
        print("4. Test with: python security/monitor_network.py dashboard")
        print("5. Gradually whitelist trusted domains")
        print()
        print("=" * 80)

    def suggest_integration_points(self) -> list[str]:
        """Suggest where to integrate security."""
        suggestions = []

        # Entry points
        for entry_point in self.scan_results["entry_points"]:
            suggestions.append(
                {
                    "file": entry_point,
                    "action": "Add 'import security' at the top",
                    "priority": "HIGH",
                    "reason": "Application entry point",
                }
            )

        # Files with heavy network usage
        for item in self.scan_results["files_with_network_imports"]:
            if len(item["network_calls"]) > 5:
                suggestions.append(
                    {
                        "file": item["file"],
                        "action": "Review network calls and add @enforce_network_policy decorator",
                        "priority": "MEDIUM",
                        "reason": f"High network usage ({len(item['network_calls'])} calls)",
                    }
                )

        # WebSocket handlers
        for item in self.scan_results["files_with_websockets"]:
            suggestions.append(
                {
                    "file": item["file"],
                    "action": "Configure WebSocket policy in network_access_control.yaml",
                    "priority": "MEDIUM",
                    "reason": "WebSocket usage detected",
                }
            )

        return suggestions

    def create_integration_template(self, filepath: str) -> str:
        """Create integration code template for a file."""
        template = f'''"""
SECURITY INTEGRATION
====================
This file has been identified as using network resources.
Security monitoring has been integrated.

File: {filepath}
Date: {datetime.utcnow().isoformat()}
"""

# ============================================================================
# ADD THIS IMPORT AT THE TOP OF YOUR FILE
# ============================================================================
import security  # Network security monitoring
# from security import enforce_network_policy  # For function decorators

# ============================================================================
# OPTIONAL: Protect specific functions
# ============================================================================
# @enforce_network_policy
# def your_network_function():
#     # Network calls here will be monitored
#     pass

# ============================================================================
# AFTER INTEGRATION
# ============================================================================
# 1. Test your application
# 2. Check blocked requests: python security/monitor_network.py blocked
# 3. Whitelist trusted domains: python security/monitor_network.py add <domain>
# 4. Monitor continuously: python security/monitor_network.py dashboard
'''
        return template


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Network Security Integration Tool")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan codebase for network usage",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate integration report",
    )
    parser.add_argument(
        "--integrate",
        action="store_true",
        help="Suggest integration points",
    )
    parser.add_argument(
        "--root",
        type=str,
        default="E:\\",
        help="Root directory to scan (default: E:\\)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for report (default: auto-generated)",
    )

    args = parser.parse_args()

    integrator = SecurityIntegrator(root_path=args.root)

    if args.scan or args.report or args.integrate:
        # Scan codebase
        print("🔒 Network Security Integration Tool")
        print("=" * 80)
        print()

        integrator.scan_codebase()

        if args.report:
            integrator.generate_report(output_file=args.output)
            integrator.print_report()

        if args.integrate:
            suggestions = integrator.suggest_integration_points()

            print("💡 INTEGRATION SUGGESTIONS:")
            print()
            for i, suggestion in enumerate(suggestions[:20], 1):
                print(f"{i}. {suggestion['file']}")
                print(f"   Priority: {suggestion['priority']}")
                print(f"   Action: {suggestion['action']}")
                print(f"   Reason: {suggestion['reason']}")
                print()

            # Save suggestions
            suggestions_file = (
                integrator.security_path / "logs" / "integration_suggestions.json"
            )
            with open(suggestions_file, "w") as f:
                json.dump(suggestions, f, indent=2)
            print(f"💾 Suggestions saved to: {suggestions_file}")

        if args.scan:
            integrator.print_report()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
