#!/usr/bin/env python3
"""
Environment Security Validation Script

Validates the Python environment for security issues:
- Writable system paths in PATH
- Python installation permissions
- Non-existent PYTHONPATH entries
- Security configuration issues

Usage:
    python scripts/security/validate_environment.py
    python scripts/security/validate_environment.py --json
    python scripts/security/validate_environment.py --fix
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import SecurePathManager for auto-fix functionality
try:
    from grid.security.path_manager import SecurePathManager

    PATH_MANAGER_AVAILABLE = True
except ImportError:
    PATH_MANAGER_AVAILABLE = False


class EnvironmentValidator:
    """Validates environment security configuration."""

    def __init__(self):
        self.issues: list[dict[str, Any]] = []
        self.recommendations: list[str] = []

    def check_writable_paths(self) -> list[dict[str, Any]]:
        """
        Check for writable paths in PATH environment variable.

        Returns:
            List of issues found
        """
        issues = []
        path_env = os.environ.get("PATH", "")

        # Split PATH by platform
        if os.name == "nt":  # Windows
            paths = path_env.split(";")
        else:  # Unix-like
            paths = path_env.split(":")

        for path_str in paths:
            if not path_str.strip():
                continue

            try:
                path = Path(path_str.strip())
                if not path.exists():
                    continue

                # Check if path is writable
                if path.is_dir():
                    # Check write permission
                    if os.access(path, os.W_OK):
                        # Check if it's a system path
                        is_system_path = self._is_system_path(path)

                        if is_system_path:
                            issues.append(
                                {
                                    "type": "writable_system_path",
                                    "severity": "medium",
                                    "path": str(path),
                                    "description": f"System path '{path}' is writable",
                                    "recommendation": "Review write permissions on system directories",
                                }
                            )
                        else:
                            # User/application paths are typically OK to be writable
                            pass

            except (OSError, ValueError):
                # Skip invalid paths
                continue

        return issues

    def _is_system_path(self, path: Path) -> bool:
        """Check if path is a system path."""
        path_str = str(path).lower()

        # Windows system paths
        if os.name == "nt":
            system_indicators = [
                "\\windows\\",
                "\\windows\\system32",
                "\\program files\\",
                "\\program files (x86)\\",
            ]
            return any(indicator in path_str for indicator in system_indicators)

        # Unix system paths
        else:
            system_indicators = ["/usr/", "/bin/", "/sbin/", "/etc/", "/lib/"]
            return any(path_str.startswith(indicator) for indicator in system_indicators)

    def check_python_installation(self) -> list[dict[str, Any]]:
        """
        Check Python installation permissions.

        Returns:
            List of issues found
        """
        issues = []
        python_exe = Path(sys.executable)

        # Check if Python executable is writable
        if python_exe.exists() and os.access(python_exe.parent, os.W_OK):
            issues.append(
                {
                    "type": "writable_python_installation",
                    "severity": "high",
                    "path": str(python_exe.parent),
                    "description": f"Python installation directory '{python_exe.parent}' is writable",
                    "recommendation": "Use virtual environments or restrict Python installation permissions",
                }
            )

        # Check Python library directory
        python_lib = Path(sys.executable).parent.parent / "Lib"
        if python_lib.exists() and os.access(python_lib, os.W_OK):
            issues.append(
                {
                    "type": "writable_python_lib",
                    "severity": "high",
                    "path": str(python_lib),
                    "description": f"Python library directory '{python_lib}' is writable",
                    "recommendation": "Restrict write access to Python library directory",
                }
            )

        return issues

    def check_pythonpath(self) -> list[dict[str, Any]]:
        """
        Check PYTHONPATH for non-existent entries.

        Returns:
            List of issues found
        """
        issues = []
        pythonpath = os.environ.get("PYTHONPATH", "")

        if not pythonpath:
            return issues

        # Split PYTHONPATH
        if os.name == "nt":  # Windows
            paths = pythonpath.split(";")
        else:  # Unix-like
            paths = pythonpath.split(":")

        for path_str in paths:
            if not path_str.strip():
                continue

            try:
                path = Path(path_str.strip())
                if not path.exists():
                    issues.append(
                        {
                            "type": "non_existent_pythonpath",
                            "severity": "low",
                            "path": str(path),
                            "description": f"PYTHONPATH entry '{path}' does not exist",
                            "recommendation": "Remove non-existent paths from PYTHONPATH",
                        }
                    )
            except (OSError, ValueError):
                # Skip invalid paths
                continue

        return issues

    def check_sys_path(self) -> list[dict[str, Any]]:
        """
        Check sys.path for issues.

        Returns:
            List of issues found
        """
        issues = []

        for path_str in sys.path:
            if not path_str:
                continue

            try:
                path = Path(path_str)
                if not path.exists():
                    issues.append(
                        {
                            "type": "non_existent_sys_path",
                            "severity": "low",
                            "path": str(path),
                            "description": f"sys.path entry '{path}' does not exist",
                            "recommendation": "Review Python path configuration",
                        }
                    )
            except (OSError, ValueError):
                # Skip invalid paths
                continue

        return issues

    def validate(self) -> dict[str, Any]:
        """
        Run all validation checks.

        Returns:
            Dictionary with validation results
        """
        self.issues = []

        # Run all checks
        self.issues.extend(self.check_writable_paths())
        self.issues.extend(self.check_python_installation())
        self.issues.extend(self.check_pythonpath())
        self.issues.extend(self.check_sys_path())

        # Generate recommendations
        self.recommendations = self._generate_recommendations()

        # Count issues by severity
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for issue in self.issues:
            severity_counts[issue["severity"]] += 1

        return {
            "total_issues": len(self.issues),
            "severity_counts": severity_counts,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "python_version": sys.version,
            "python_executable": str(Path(sys.executable)),
            "platform": os.name,
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on found issues."""
        recommendations = []

        has_writable_system = any(issue["type"] == "writable_system_path" for issue in self.issues)
        has_writable_python = any(
            issue["type"] in ["writable_python_installation", "writable_python_lib"] for issue in self.issues
        )
        has_non_existent_paths = any(
            issue["type"] in ["non_existent_pythonpath", "non_existent_sys_path"] for issue in self.issues
        )

        if has_writable_system:
            recommendations.append("Review and restrict write permissions on system directories in PATH")

        if has_writable_python:
            recommendations.append(
                "Use virtual environments for project isolation. Consider restricting Python installation permissions."
            )

        if has_non_existent_paths:
            recommendations.append("Clean up PYTHONPATH and sys.path to remove non-existent entries")

        if not recommendations:
            recommendations.append("No critical security issues found. Continue using best practices.")

        return recommendations

    def fix_pythonpath(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Fix PYTHONPATH by removing non-existent entries.

        Args:
            dry_run: If True, only report what would be fixed without making changes

        Returns:
            Dictionary with fix results
        """
        if not PATH_MANAGER_AVAILABLE:
            return {
                "success": False,
                "error": "SecurePathManager not available",
                "fixed": [],
            }

        pythonpath_issues = [i for i in self.issues if i["type"] == "non_existent_pythonpath"]
        if not pythonpath_issues:
            return {"success": True, "fixed": [], "message": "No PYTHONPATH issues to fix"}

        removed_paths: list[str] = []
        if not dry_run:
            removed_paths = SecurePathManager.clean_pythonpath()
        else:
            # Dry run: just collect what would be removed
            pythonpath = os.environ.get("PYTHONPATH", "")
            if pythonpath:
                if os.name == "nt":
                    paths = pythonpath.split(";")
                else:
                    paths = pythonpath.split(":")

                for path_str in paths:
                    if path_str.strip():
                        try:
                            path = Path(path_str.strip())
                            if not path.exists():
                                removed_paths.append(path_str)
                        except (OSError, ValueError):
                            removed_paths.append(path_str)

        return {
            "success": True,
            "fixed": removed_paths,
            "count": len(removed_paths),
            "dry_run": dry_run,
        }

    def fix_sys_path(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Fix sys.path by removing invalid entries.

        Args:
            dry_run: If True, only report what would be fixed without making changes

        Returns:
            Dictionary with fix results
        """
        if not PATH_MANAGER_AVAILABLE:
            return {
                "success": False,
                "error": "SecurePathManager not available",
                "fixed": [],
            }

        sys_path_issues = [i for i in self.issues if i["type"] == "non_existent_sys_path"]
        if not sys_path_issues:
            return {"success": True, "fixed": [], "message": "No sys.path issues to fix"}

        manager = SecurePathManager()
        if not dry_run:
            report = manager.validate_and_clean()
            removed = report.removed_paths
        else:
            # Dry run: collect what would be removed
            removed = []
            for path_str in sys.path:
                if not path_str:
                    removed.append(path_str)
                    continue
                try:
                    path = Path(path_str)
                    if not path.exists():
                        removed.append(path_str)
                except (OSError, ValueError):
                    pass

        return {
            "success": True,
            "fixed": removed,
            "count": len(removed),
            "dry_run": dry_run,
        }

    def fix_all(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Attempt to fix all fixable issues.

        Args:
            dry_run: If True, only report what would be fixed without making changes

        Returns:
            Dictionary with comprehensive fix results
        """
        results: dict[str, Any] = {
            "dry_run": dry_run,
            "fixes_applied": {},
            "warnings": [],
            "errors": [],
        }

        # Fix PYTHONPATH
        pythonpath_result = self.fix_pythonpath(dry_run=dry_run)
        results["fixes_applied"]["pythonpath"] = pythonpath_result
        if pythonpath_result.get("error"):
            results["errors"].append(f"PYTHONPATH fix failed: {pythonpath_result['error']}")

        # Fix sys.path
        sys_path_result = self.fix_sys_path(dry_run=dry_run)
        results["fixes_applied"]["sys_path"] = sys_path_result
        if sys_path_result.get("error"):
            results["errors"].append(f"sys.path fix failed: {sys_path_result['error']}")

        # Warn about issues that cannot be auto-fixed
        writable_issues = [
            i
            for i in self.issues
            if i["type"] in ["writable_system_path", "writable_python_installation", "writable_python_lib"]
        ]
        if writable_issues:
            results["warnings"].append(
                f"Found {len(writable_issues)} permission issues that require manual intervention"
            )

        total_fixed = pythonpath_result.get("count", 0) + sys_path_result.get("count", 0)
        results["total_fixed"] = total_fixed
        results["success"] = total_fixed > 0 and not results["errors"]

        return results

    def print_report(self, json_output: bool = False) -> None:
        """Print validation report."""
        results = self.validate()

        if json_output:
            print(json.dumps(results, indent=2))
            return

        # Print formatted report
        print("=" * 70)
        print("Environment Security Validation Report")
        print("=" * 70)
        print()

        print(f"Python Version: {results['python_version']}")
        print(f"Python Executable: {results['python_executable']}")
        print(f"Platform: {results['platform']}")
        print()

        print(f"Total Issues Found: {results['total_issues']}")
        print(f"  High Severity: {results['severity_counts']['high']}")
        print(f"  Medium Severity: {results['severity_counts']['medium']}")
        print(f"  Low Severity: {results['severity_counts']['low']}")
        print()

        if results["issues"]:
            print("Issues:")
            print("-" * 70)
            for i, issue in enumerate(results["issues"], 1):
                severity_symbol = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢",
                }.get(issue["severity"], "⚪")

                print(f"{i}. {severity_symbol} [{issue['severity'].upper()}] {issue['type']}")
                print(f"   Path: {issue['path']}")
                print(f"   Description: {issue['description']}")
                print(f"   Recommendation: {issue['recommendation']}")
                print()
        else:
            print("✅ No security issues found!")
            print()

        print("Recommendations:")
        print("-" * 70)
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"{i}. {rec}")

        print()
        print("=" * 70)
        print("For detailed information, see: docs/security/ENVIRONMENT_HARDENING.md")
        print("=" * 70)


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate environment security configuration")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues automatically",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes (use with --fix)",
    )

    args = parser.parse_args()

    validator = EnvironmentValidator()

    if args.fix:
        if not PATH_MANAGER_AVAILABLE:
            print("⚠️  Auto-fix requires SecurePathManager (not available)")
            print("Please ensure grid.security.path_manager is importable")
            print()
        else:
            print("=" * 70)
            print("Environment Auto-Fix")
            print("=" * 70)
            print()

            if args.dry_run:
                print("🔍 DRY RUN MODE - No changes will be made")
                print()

            # Run validation first to identify issues
            validator.validate()

            # Apply fixes
            fix_results = validator.fix_all(dry_run=args.dry_run)

            if fix_results["success"]:
                total_fixed = fix_results["total_fixed"]
                if total_fixed > 0:
                    print(f"✅ Fixed {total_fixed} issues:")
                    if "pythonpath" in fix_results["fixes_applied"]:
                        py_result = fix_results["fixes_applied"]["pythonpath"]
                        if py_result.get("count", 0) > 0:
                            print(f"  - Removed {py_result['count']} invalid PYTHONPATH entries")
                    if "sys_path" in fix_results["fixes_applied"]:
                        sp_result = fix_results["fixes_applied"]["sys_path"]
                        if sp_result.get("count", 0) > 0:
                            print(f"  - Removed {sp_result['count']} invalid sys.path entries")
                else:
                    print("ℹ️  No fixable issues found")
            else:
                print("❌ Some fixes failed:")
                for error in fix_results.get("errors", []):
                    print(f"  - {error}")

            if fix_results.get("warnings"):
                print()
                print("⚠️  Warnings:")
                for warning in fix_results["warnings"]:
                    print(f"  - {warning}")

            print()
            print("=" * 70)
            print()

    validator.print_report(json_output=args.json)

    # Return exit code based on issues found
    results = validator.validate()
    if results["severity_counts"]["high"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
