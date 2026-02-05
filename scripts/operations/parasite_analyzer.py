#!/usr/bin/env python3
"""
Advanced AST-Based Parasite Analyzer
====================================

A high-precision static analysis tool for detecting security vulnerabilities,
parasitic code patterns, and suspicious functions using Python's AST.
"""

import argparse
import ast
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("parasite_analyzer")

# =============================================================================
# Configuration & Knowledge Base
# =============================================================================

DANGEROUS_FUNCTIONS = {
    'eval', 'exec', 'compile',
    'subprocess.call', 'subprocess.Popen', 'subprocess.run', 'os.system', 'os.popen',
    'input',  # In some contexts
}

SUSPICIOUS_IMPORTS = {
    'telnetlib', 'ftplib', 'pickle', 'xmlrpc', 'subprocess', 'shlex',
    'http.server', 'wsgiref.simple_server',
}

PARASITIC_PATTERNS = {
    'hook', 'intercept', 'monkey_patch', 'inject', 'proxy',
    'bypass', 'override', 'hide', 'mask',
}

# Whitelist to reduce false positives
# Format: { 'module_name': {'allowed_function', ...} }
whitelist: dict[str, set[str]] = {
    'subprocess': {'run', 'call', 'Popen', 'check_output'},  # Often used legitimately in scripts
    'os': {'system', 'popen'},  # Often used legitimately
}

# =============================================================================
# AST Visitor
# =============================================================================

class SecurityVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.findings = []
        self.current_function = None

    def _add_finding(self, risk: str, category: str, message: str, node: ast.AST):
        self.findings.append({
            'file': self.filename,
            'line': getattr(node, 'lineno', 0),
            'risk': risk,
            'category': category,
            'message': message,
            'context': self.current_function or '<module>'
        })

    def visit_FunctionDef(self, node: ast.FunctionDef):
        previous_function = self.current_function
        self.current_function = node.name

        # Check for suspicious naming
        name_lower = node.name.lower()
        for pattern in PARASITIC_PATTERNS:
            if pattern in name_lower:
                self._add_finding(
                    'MEDIUM', 'suspicious_name',
                    f"Function name '{node.name}' contains suspicious pattern '{pattern}'",
                    node
                )

        self.generic_visit(node)
        self.current_function = previous_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # reuse logic for sync functions
        self.visit_FunctionDef(node)

    def visit_Call(self, node: ast.Call):
        # Look for dangerous function calls
        func_name = self._get_func_name(node.func)

        if func_name:
            # Check DANGEROUS_FUNCTIONS
            if func_name in DANGEROUS_FUNCTIONS:
                self._add_finding(
                    'HIGH', 'dangerous_execution',
                    f"Call to dangerous function '{func_name}'",
                    node
                )

            # Check specific dangerous patterns (e.g., subprocess with shell=True)
            if 'subprocess' in func_name and self._has_keyword_arg(node, 'shell', True):
                 self._add_finding(
                    'CRITICAL', 'shell_injection',
                    "Subprocess call with shell=True",
                    node
                )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name in SUSPICIOUS_IMPORTS:
                self._add_finding(
                    'MEDIUM', 'suspicious_import',
                    f"Importing suspicious module '{alias.name}'",
                    node
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module in SUSPICIOUS_IMPORTS:
            self._add_finding(
                'MEDIUM', 'suspicious_import',
                f"Importing from suspicious module '{node.module}'",
                node
            )
        self.generic_visit(node)

    def _get_func_name(self, node: ast.AST) -> str | None:
        """Helper to extract function name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_func_name(node.value)}.{node.attr}"
        return None

    def _has_keyword_arg(self, node: ast.Call, arg_name: str, arg_value: Any) -> bool:
        """Helper to check for specific keyword arguments."""
        for keyword in node.keywords:
            if keyword.arg == arg_name:
                # Simple check for Constant values (Python 3.8+)
                if isinstance(keyword.value, ast.Constant):
                     val = getattr(keyword.value, 'value', None)
                     if val == arg_value:
                         return True
                # Check for NameConstant (True/False/None in older python)
                # But ast.Constant handles True/False in newer python
        return False

# =============================================================================
# Main Analysis Logic
# =============================================================================

def analyze_file(filepath: Path) -> list[dict[str, Any]]:
    try:
        with open(filepath, encoding='utf-8', errors='ignore') as f:
            content = f.read()

        tree = ast.parse(content, filename=str(filepath))
        visitor = SecurityVisitor(str(filepath))
        visitor.visit(tree)
        return visitor.findings
    except SyntaxError as e:
        log.warning(f"Syntax error in {filepath}: {e}")
        return []
    except Exception as e:
        log.error(f"Failed to analyze {filepath}: {e}")
        return []

def should_skip(path: Path) -> bool:
    """Check if a path should be skipped."""
    skip_dirs = {'.venv', 'venv', '__pycache__', '.git', '.pytest_cache', '.mypy_cache', 'node_modules'}
    return any(part in skip_dirs for part in path.parts)

def analyze_directory(root_path: Path) -> list[dict[str, Any]]:
    all_findings = []
    for py_file in root_path.rglob('*.py'):
        if should_skip(py_file):
            continue
        findings = analyze_file(py_file)
        all_findings.extend(findings)
    return all_findings

# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Advanced AST-Based Parasite Analyzer")
    parser.add_argument("path", help="Path to file or directory to analyze")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    target_path = Path(args.path)

    print(f"🔍 Starting analysis of: {target_path}")

    if target_path.is_file():
        findings = analyze_file(target_path)
    elif target_path.is_dir():
        findings = analyze_directory(target_path)
    else:
        log.error(f"Path not found: {target_path}")
        sys.exit(1)

    # Stats
    severity_counts = defaultdict(int)
    for f in findings:
        severity_counts[f['risk']] += 1

    print("\n=== Analysis Summary ===")
    print(f"Total Findings: {len(findings)}")
    print(f"Critical: {severity_counts['CRITICAL']}")
    print(f"High:     {severity_counts['HIGH']}")
    print(f"Medium:   {severity_counts['MEDIUM']}")
    print(f"Low:      {severity_counts['LOW']}")

    # Save Report
    report = {
        'summary': dict(severity_counts),
        'findings': findings
    }

    output_path = args.output or 'parasite_analysis_report.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: {output_path}")

    # Return non-zero exit code if critical/high issues found
    if severity_counts['CRITICAL'] > 0 or severity_counts['HIGH'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
