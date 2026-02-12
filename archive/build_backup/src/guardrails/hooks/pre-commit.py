#!/usr/bin/env python3
"""
Pre-commit hook for Guardrail System

Integrates guardrail checks into the git workflow to prevent issues
from being committed.

Usage:
    1. Copy this file to .git/hooks/pre-commit
    2. Make it executable: chmod +x .git/hooks/pre-commit
    3. Or use with pre-commit framework by adding to .pre-commit-config.yaml
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from typing import List, Tuple, Optional

# Configuration
GUARDRAIL_CONFIG = {
    "fail_on": ["critical", "high"],  # Severity levels that cause commit to fail
    "warn_on": ["medium"],             # Severity levels that just warn
    "max_violations": 10,              # Max violations allowed per commit
    "check_staged_only": True,         # Only check staged files
    "auto_fix": False,                 # Try to auto-fix issues (not implemented)
    "verbose": False,                  # Show detailed output
}


def get_staged_python_files() -> List[str]:
    """Get list of Python files staged for commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True
        )
        
        files = result.stdout.strip().split("\n")
        python_files = [f for f in files if f.endswith(".py")]
        
        return python_files
    except subprocess.CalledProcessError:
        return []


def load_config() -> dict:
    """Load guardrail configuration from file."""
    config_paths = [
        ".guardrailrc",
        ".guardrailrc.json",
        "pyproject.toml",  # Could add support for [tool.guardrail] section
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                if config_path.endswith(".json"):
                    with open(config_path, 'r') as f:
                        return {**GUARDRAIL_CONFIG, **json.load(f)}
            except Exception:
                pass
                
    return GUARDRAIL_CONFIG


def check_file_with_guardrail(file_path: str) -> Tuple[bool, List[dict]]:
    """Check a single file with the guardrail system."""
    try:
        # Import guardrail system
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from guardrails.profiler.module_profiler import analyze_module
        
        personality = analyze_module(file_path)
        
        violations = []
        
        # Check for hardcoded paths
        if personality.is_path_dependent:
            for path in personality.hardcoded_paths:
                violations.append({
                    "type": "hardcoded_path",
                    "severity": "high",
                    "message": f"Hardcoded path: {path}",
                    "file": file_path,
                    "suggestion": "Use environment variables or pathlib.Path"
                })
                
        # Check for conditional imports
        if personality.is_runtime_fragile:
            for imp in personality.conditional_imports:
                violations.append({
                    "type": "conditional_import",
                    "severity": "medium",
                    "message": f"Conditional import: {imp}",
                    "file": file_path,
                    "suggestion": "Add missing dependency to requirements.txt"
                })
                
        # Check for circular imports
        if personality.is_circular_prone:
            for circular in personality.circular_dependencies:
                violations.append({
                    "type": "circular_import",
                    "severity": "high",
                    "message": f"Circular import with: {circular}",
                    "file": file_path,
                    "suggestion": "Refactor to remove circular dependency"
                })
                
        return len(violations) == 0, violations
        
    except Exception as e:
        return False, [{
            "type": "error",
            "severity": "critical",
            "message": f"Failed to analyze: {str(e)}",
            "file": file_path,
            "suggestion": "Check guardrail system installation"
        }]


def format_violation(violation: dict) -> str:
    """Format a violation for display."""
    severity_colors = {
        "critical": "\033[91m",  # Red
        "high": "\033[91m",      # Red
        "medium": "\033[93m",    # Yellow
        "low": "\033[94m",       # Blue
        "reset": "\033[0m"
    }
    
    color = severity_colors.get(violation["severity"], "")
    reset = severity_colors["reset"]
    
    return f"""
{color}[{violation['severity'].upper()}]{reset} {violation['type']}
  File: {violation['file']}
  Message: {violation['message']}
  Suggestion: {violation['suggestion']}
"""


def main():
    """Main pre-commit hook logic."""
    print("🔍 Running Guardrail pre-commit checks...")
    
    config = load_config()
    
    # Get files to check
    if config.get("check_staged_only", True):
        files = get_staged_python_files()
    else:
        # Check all Python files in repo
        files = [
            str(p) for p in Path(".").rglob("*.py")
            if ".git" not in str(p) and "__pycache__" not in str(p)
        ]
        
    if not files:
        print("✓ No Python files to check")
        return 0
        
    print(f"Checking {len(files)} file(s)...")
    
    all_violations = []
    failed_files = []
    
    for file_path in files:
        if not os.path.exists(file_path):
            continue
            
        success, violations = check_file_with_guardrail(file_path)
        
        if not success:
            failed_files.append(file_path)
            all_violations.extend(violations)
            
        if config.get("verbose", False):
            if violations:
                print(f"  {file_path}: {len(violations)} violation(s)")
            else:
                print(f"  {file_path}: ✓ clean")
                
    # Check if we should fail the commit
    should_fail = False
    
    # Count violations by severity
    severity_counts = {}
    for v in all_violations:
        sev = v["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
    # Check fail conditions
    for fail_severity in config.get("fail_on", ["critical", "high"]):
        if severity_counts.get(fail_severity, 0) > 0:
            should_fail = True
            break
            
    # Check max violations
    if len(all_violations) > config.get("max_violations", 10):
        should_fail = True
        
    # Report results
    if all_violations:
        print(f"\n⚠️  Found {len(all_violations)} violation(s) in {len(failed_files)} file(s)")
        
        # Show critical/high first
        for severity in ["critical", "high", "medium", "low"]:
            severity_violations = [v for v in all_violations if v["severity"] == severity]
            if severity_violations:
                print(f"\n{severity.upper()} ({len(severity_violations)}):")
                for v in severity_violations[:5]:  # Show max 5 per severity
                    print(format_violation(v))
                    
                if len(severity_violations) > 5:
                    print(f"  ... and {len(severity_violations) - 5} more")
                    
        if should_fail:
            print("\n❌ Commit blocked due to guardrail violations")
            print("\nTo bypass (not recommended):")
            print("  git commit --no-verify")
            print("\nTo fix issues:")
            print("  1. Review the violations above")
            print("  2. Apply the suggested fixes")
            print("  3. Stage your changes and commit again")
            return 1
        else:
            print("\n⚠️  Warnings present but commit allowed")
            return 0
    else:
        print("\n✓ All files passed guardrail checks")
        return 0


if __name__ == "__main__":
    sys.exit(main())
