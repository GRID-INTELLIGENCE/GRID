#!/usr/bin/env python3
"""
GRID Security Validation Script

Validate your GRID development environment security setup.

Usage:
    python scripts/validate_security.py              # Full validation
    python scripts/validate_security.py --quick      # Quick check
    python scripts/validate_security.py --secrets    # Secrets only
    python scripts/validate_security.py --env        # Environment only
    python scripts/validate_security.py --report     # Generate report
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Use ASCII-safe characters for Windows compatibility
CHECK_MARK = "[OK]"
WARNING_MARK = "[WARN]"
FAIL_MARK = "[FAIL]"
INFO_MARK = "[INFO]"


def print_header(text: str) -> None:
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")


def print_pass(text: str) -> None:
    print(f"{GREEN}{CHECK_MARK} {text}{RESET}")


def print_fail(text: str) -> None:
    print(f"{RED}{FAIL_MARK} {text}{RESET}")


def print_warn(text: str) -> None:
    print(f"{YELLOW}{WARNING_MARK} {text}{RESET}")


def print_info(text: str) -> None:
    print(f"{BLUE}{INFO_MARK} {text}{RESET}")


class SecurityValidator:
    """Validate GRID security setup."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.project_root = Path(__file__).resolve().parent.parent
        self.grid_home = Path.home() / ".grid"
        self.results: List[Dict[str, Any]] = []

    def run(self) -> int:
        """Run validation."""
        print_header("GRID Security Validation")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Environment: {os.getenv('GRID_ENVIRONMENT', 'development')}")

        if self.args.quick:
            return self._quick_validation()

        if self.args.secrets:
            return self._validate_secrets()

        if self.args.env:
            return self._validate_environment()

        return self._full_validation()

    def _quick_validation(self) -> int:
        """Quick validation - just check if things exist."""
        print_header("Quick Validation")

        checks = [
            ("Secrets directory exists", self._check_file_exists(self.grid_home / "secrets" / "secrets.db")),
            ("Environment file exists", self._check_file_exists(self.project_root / ".env")),
            ("Secrets manager can read", self._test_secrets_read()),
            ("Python version OK", sys.version_info >= (3, 10)),
        ]

        passed = sum(1 for _, result in checks if result)
        total = len(checks)

        print(f"\n{BOLD}Results: {passed}/{total} checks passed{RESET}")

        return 0 if passed == total else 1

    def _full_validation(self) -> int:
        """Full security validation."""
        checks = []

        # 1. Environment validation
        print_header("1. Environment Configuration")
        checks.extend(self._validate_environment())

        # 2. Secrets validation
        print_header("2. Secrets Management")
        checks.extend(self._validate_secrets())

        # 3. Dependencies validation
        print_header("3. Dependencies")
        checks.extend(self._validate_dependencies())

        # 4. Security patterns validation
        print_header("4. Security Patterns")
        checks.extend(self._validate_security_patterns())

        # Print summary
        print_header("Validation Summary")

        passed = sum(1 for c in checks if c["status"] == "pass")
        failed = sum(1 for c in checks if c["status"] == "fail")
        warnings = sum(1 for c in checks if c["status"] == "warn")

        print(f"Passed: {GREEN}{passed}{RESET}")
        print(f"Failed: {RED}{failed}{RESET}")
        print(f"Warnings: {YELLOW}{warnings}{RESET}")

        if self.args.report:
            self._generate_report(checks)

        return 0 if failed == 0 else 1

    def _validate_environment(self) -> List[Dict]:
        """Validate environment configuration."""
        checks = []

        # Check GRID_ENVIRONMENT
        env = os.getenv("GRID_ENVIRONMENT", "development")
        checks.append(
            {
                "category": "environment",
                "name": "GRID_ENVIRONMENT set",
                "status": "pass" if env else "fail",
                "message": f"GRID_ENVIRONMENT={env}",
            }
        )

        # Check .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            checks.append(
                {"category": "environment", "name": ".env file exists", "status": "pass", "message": str(env_file)}
            )

            # Check for sensitive patterns in .env
            content = env_file.read_text()
            has_real_secrets = any(
                [
                    "actual_api_key" in content and "your-" not in content,
                    "real_password" in content and "change" not in content.lower(),
                    "sk_live" in content,
                ]
            )

            if has_real_secrets:
                checks.append(
                    {
                        "category": "environment",
                        "name": "No real secrets in .env",
                        "status": "fail",
                        "message": "Potential real secrets found in .env",
                    }
                )
            else:
                checks.append(
                    {
                        "category": "environment",
                        "name": "No real secrets in .env",
                        "status": "pass",
                        "message": "No real secrets detected",
                    }
                )
        else:
            checks.append(
                {
                    "category": "environment",
                    "name": ".env file exists",
                    "status": "warn",
                    "message": ".env file not found (optional)",
                }
            )

        # Print results
        for check in checks:
            if check["status"] == "pass":
                print_pass(f"{check['name']}: {check['message']}")
            elif check["status"] == "fail":
                print_fail(f"{check['name']}: {check['message']}")
            else:
                print_warn(f"{check['name']}: {check['message']}")

        return checks

    def _validate_secrets(self) -> List[Dict]:
        """Validate secrets management."""
        checks = []

        try:
            # Add src/ to path for imports
            sys.path.insert(0, str(self.project_root / "src"))
            from grid.security.local_secrets_manager import LocalSecretsManager

            # Check secrets directory
            secrets_db = self.grid_home / "secrets" / "secrets.db"
            if secrets_db.exists():
                checks.append(
                    {
                        "category": "secrets",
                        "name": "Secrets database exists",
                        "status": "pass",
                        "message": str(secrets_db),
                    }
                )
            else:
                checks.append(
                    {
                        "category": "secrets",
                        "name": "Secrets database exists",
                        "status": "fail",
                        "message": "Secrets database not found",
                    }
                )

            # Initialize and test
            manager = LocalSecretsManager(
                storage_path=secrets_db, environment=os.getenv("GRID_ENVIRONMENT", "development")
            )

            # Test write/read/delete
            test_key = "__security_validation_test"
            test_value = "test_" + datetime.now().isoformat()

            if manager.set(test_key, test_value):
                checks.append(
                    {
                        "category": "secrets",
                        "name": "Secrets write",
                        "status": "pass",
                        "message": "Write operation successful",
                    }
                )
            else:
                checks.append(
                    {
                        "category": "secrets",
                        "name": "Secrets write",
                        "status": "fail",
                        "message": "Write operation failed",
                    }
                )

            retrieved = manager.get(test_key)
            if retrieved == test_value:
                checks.append(
                    {
                        "category": "secrets",
                        "name": "Secrets read",
                        "status": "pass",
                        "message": "Read operation successful",
                    }
                )
            else:
                checks.append(
                    {
                        "category": "secrets",
                        "name": "Secrets read",
                        "status": "fail",
                        "message": "Read operation returned unexpected value",
                    }
                )

            manager.delete(test_key)

            # Check required secrets
            required_secrets = ["MOTHERSHIP_SECRET_KEY", "MISTRAL_API_KEY"]
            for secret in required_secrets:
                if manager.exists(secret):
                    if manager.get(secret) != "your-mistral-api-key-here":
                        checks.append(
                            {
                                "category": "secrets",
                                "name": f"{secret} configured",
                                "status": "pass",
                                "message": f"{secret} is set",
                            }
                        )
                    else:
                        checks.append(
                            {
                                "category": "secrets",
                                "name": f"{secret} configured",
                                "status": "warn",
                                "message": f"{secret} is set but appears to be a placeholder",
                            }
                        )
                else:
                    checks.append(
                        {
                            "category": "secrets",
                            "name": f"{secret} configured",
                            "status": "warn",
                            "message": f"{secret} is not set",
                        }
                    )

        except Exception as e:
            checks.append(
                {"category": "secrets", "name": "Secrets manager", "status": "fail", "message": f"Error: {str(e)}"}
            )

        # Print results
        for check in checks:
            if check["status"] == "pass":
                print_pass(f"{check['name']}: {check['message']}")
            elif check["status"] == "fail":
                print_fail(f"{check['name']}: {check['message']}")
            else:
                print_warn(f"{check['name']}: {check['message']}")

        return checks

    def _validate_dependencies(self) -> List[Dict]:
        """Validate security dependencies."""
        checks = []

        # Check cryptography
        try:
            import cryptography

            checks.append(
                {
                    "category": "dependencies",
                    "name": "cryptography installed",
                    "status": "pass",
                    "message": f"version {cryptography.__version__}",
                }
            )
        except ImportError:
            checks.append(
                {
                    "category": "dependencies",
                    "name": "cryptography installed",
                    "status": "fail",
                    "message": "cryptography package not installed",
                }
            )

        # Check GCP packages (optional)
        gcp_packages = ["google-cloud-secretmanager", "google-cloud-logging"]
        for pkg in gcp_packages:
            try:
                __import__(pkg.replace("-", "_"))
                checks.append(
                    {
                        "category": "dependencies",
                        "name": f"{pkg} installed",
                        "status": "pass",
                        "message": f"{pkg} is available",
                    }
                )
            except ImportError:
                checks.append(
                    {
                        "category": "dependencies",
                        "name": f"{pkg} installed",
                        "status": "warn",
                        "message": f"{pkg} not installed (optional)",
                    }
                )

        # Print results
        for check in checks:
            if check["status"] == "pass":
                print_pass(f"{check['name']}: {check['message']}")
            elif check["status"] == "fail":
                print_fail(f"{check['name']}: {check['message']}")
            else:
                print_info(f"{check['name']}: {check['message']}")

        return checks

    def _validate_security_patterns(self) -> List[Dict]:
        """Validate security patterns in code."""
        checks = []

        # Check for hardcoded secrets patterns
        hardcoded_patterns = [
            ("api_key = 'sk_live", "Hardcoded Stripe key"),
            ("password = 'password'", "Hardcoded password"),
            ("secret = 'secret'", "Hardcoded secret"),
        ]

        found_issues = []
        for pattern, description in hardcoded_patterns:
            for py_file in self.project_root.rglob("*.py"):
                if "test" in py_file.name or "venv" in py_file or "site-packages" in py_file:
                    continue
                try:
                    content = py_file.read_text()
                    if pattern in content.lower():
                        found_issues.append((py_file, description))
                except Exception:
                    pass

        if found_issues:
            checks.append(
                {
                    "category": "security_patterns",
                    "name": "No hardcoded secrets",
                    "status": "fail",
                    "message": f"Found {len(found_issues)} potential issues",
                }
            )
            for file, desc in found_issues[:5]:  # Show first 5
                print_fail(f"  {desc}: {file}")
        else:
            checks.append(
                {
                    "category": "security_patterns",
                    "name": "No hardcoded secrets",
                    "status": "pass",
                    "message": "No hardcoded secrets detected",
                }
            )
            print_pass("No hardcoded secrets detected")

        # Check .gitignore has secrets patterns
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            has_secrets_ignore = any(
                [
                    "*.env" in content and ".env" in content,
                    "*.key" in content,
                    "secrets" in content.lower(),
                ]
            )

            if has_secrets_ignore:
                checks.append(
                    {
                        "category": "security_patterns",
                        "name": "Secrets in .gitignore",
                        "status": "pass",
                        "message": "Secrets patterns found in .gitignore",
                    }
                )
                print_pass("Secrets patterns in .gitignore")
            else:
                checks.append(
                    {
                        "category": "security_patterns",
                        "name": "Secrets in .gitignore",
                        "status": "warn",
                        "message": "Consider adding secrets patterns to .gitignore",
                    }
                )
                print_warn("Consider adding secrets patterns to .gitignore")

        return checks

    def _check_file_exists(self, path: Path) -> bool:
        """Check if a file exists."""
        return path.exists()

    def _test_secrets_read(self) -> bool:
        """Test if secrets can be read."""
        try:
            secrets_db = self.grid_home / "secrets" / "secrets.db"
            if not secrets_db.exists():
                return False

            sys.path.insert(0, str(self.project_root / "src"))
            from grid.security.local_secrets_manager import LocalSecretsManager

            manager = LocalSecretsManager(storage_path=secrets_db)

            test_key = "__read_test"
            test_value = "read_test_" + datetime.now().isoformat()
            manager.set(test_key, test_value)
            result = manager.get(test_key) == test_value
            manager.delete(test_key)

            return result
        except Exception:
            return False

    def _generate_report(self, checks: List[Dict]) -> None:
        """Generate a validation report."""
        report_path = self.project_root / "security_validation_report.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv("GRID_ENVIRONMENT", "development"),
            "results": checks,
            "summary": {
                "passed": sum(1 for c in checks if c["status"] == "pass"),
                "failed": sum(1 for c in checks if c["status"] == "fail"),
                "warnings": sum(1 for c in checks if c["status"] == "warn"),
            },
        }

        report_path.write_text(json.dumps(report, indent=2))
        print_info(f"Report saved to: {report_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GRID Security Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate_security.py          # Full validation
  python scripts/validate_security.py --quick  # Quick check
  python scripts/validate_security.py --report # Generate report
        """,
    )

    parser.add_argument("--quick", "-q", action="store_true", help="Quick validation")
    parser.add_argument("--secrets", "-s", action="store_true", help="Validate secrets only")
    parser.add_argument("--env", "-e", action="store_true", help="Validate environment only")
    parser.add_argument("--report", "-r", action="store_true", help="Generate JSON report")

    args = parser.parse_args()

    validator = SecurityValidator(args)
    sys.exit(validator.run())


if __name__ == "__main__":
    main()
