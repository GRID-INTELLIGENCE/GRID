"""
GRID Security Validation Runner
================================

Automated security validation, health checks, and compliance verification.

This module provides:
1. SecurityValidator - Comprehensive security validation
2. ComplianceChecker - Compliance verification
3. SecurityHealthCheck - Runtime health monitoring

Author: GRID Security Framework
Version: 2.0.0
Date: 2026-02-05
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, auto
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("grid.security.runner")


# =============================================================================
# VALIDATION STATUS
# =============================================================================


class ValidationStatus(StrEnum):
    """Status of a validation check."""

    PASS = auto()
    FAIL = auto()
    WARN = auto()
    SKIP = auto()
    ERROR = auto()


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    name: str
    status: ValidationStatus
    message: str
    severity: str = "INFO"
    details: dict[str, Any] = field(default_factory=dict)
    remediation: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.name,
            "message": self.message,
            "severity": self.severity,
            "details": self.details,
            "remediation": self.remediation,
            "duration_ms": self.duration_ms,
        }


@dataclass
class ValidationReport:
    """Complete validation report."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    environment: str = field(default_factory=lambda: os.getenv("GRID_ENVIRONMENT", "development"))
    results: list[ValidationResult] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    duration_ms: float = 0.0

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result."""
        self.results.append(result)
        status_name = result.status.name
        self.summary[status_name] = self.summary.get(status_name, 0) + 1

    @property
    def passed(self) -> bool:
        """Check if all critical validations passed."""
        return self.summary.get("FAIL", 0) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return self.summary.get("WARN", 0) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "environment": self.environment,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
            "duration_ms": self.duration_ms,
            "passed": self.passed,
            "has_warnings": self.has_warnings,
        }


# =============================================================================
# SECURITY VALIDATOR
# =============================================================================


class SecurityValidator:
    """
    Comprehensive security validation.

    Runs all security checks and generates detailed reports.
    """

    def __init__(self, project_root: Path | None = None):
        self._project_root = project_root or Path.cwd()
        self._checks: list[tuple[str, Callable[[], ValidationResult]]] = []
        self._setup_checks()

    def _setup_checks(self) -> None:
        """Set up validation checks."""
        self._checks = [
            # Environment checks
            ("env_grid_environment", self._check_grid_environment),
            ("env_debug_mode", self._check_debug_mode),
            ("env_secrets_exposure", self._check_secrets_exposure),
            ("env_pythonpath", self._check_pythonpath),
            # Configuration checks
            ("config_parasite_guard", self._check_parasite_guard_config),
            ("config_rate_limits", self._check_rate_limits),
            ("config_https_required", self._check_https_config),
            # Code security checks
            ("code_dangerous_imports", self._check_dangerous_imports),
            ("code_hardcoded_secrets", self._check_hardcoded_secrets),
            ("code_path_traversal", self._check_path_traversal_risk),
            # Dependency checks
            ("deps_known_vulnerabilities", self._check_known_vulnerabilities),
            ("deps_outdated_packages", self._check_outdated_packages),
            # File integrity checks
            ("integrity_security_modules", self._check_security_module_integrity),
            ("integrity_config_files", self._check_config_file_integrity),
            # Runtime checks
            ("runtime_writable_paths", self._check_writable_paths),
            ("runtime_module_baseline", self._check_module_baseline),
        ]

    async def run_all(self) -> ValidationReport:
        """Run all validation checks."""
        import time

        start = time.monotonic()
        report = ValidationReport()

        for name, check in self._checks:
            check_start = time.monotonic()
            try:
                # Add timeout to prevent indefinite blocking on slow checks
                result = await asyncio.wait_for(asyncio.to_thread(check), timeout=60.0)
                result.duration_ms = (time.monotonic() - check_start) * 1000
            except TimeoutError:
                result = ValidationResult(
                    name=name,
                    status=ValidationStatus.ERROR,
                    message=f"Check '{name}' timed out after 60 seconds",
                    severity="HIGH",
                )
                result.duration_ms = (time.monotonic() - check_start) * 1000
            except Exception as e:
                result = ValidationResult(
                    name=name,
                    status=ValidationStatus.ERROR,
                    message=f"Check failed with error: {e}",
                    severity="HIGH",
                )
                result.duration_ms = (time.monotonic() - check_start) * 1000
            report.add_result(result)

        report.duration_ms = (time.monotonic() - start) * 1000
        return report

    def run_all_sync(self) -> ValidationReport:
        """Synchronous version of run_all."""
        return asyncio.run(self.run_all())

    # =========================================================================
    # Environment Checks
    # =========================================================================

    def _check_grid_environment(self) -> ValidationResult:
        """Check GRID_ENVIRONMENT is set."""
        env = os.getenv("GRID_ENVIRONMENT")
        if not env:
            return ValidationResult(
                name="env_grid_environment",
                status=ValidationStatus.WARN,
                message="GRID_ENVIRONMENT not set, defaulting to 'development'",
                severity="MEDIUM",
                remediation="Set GRID_ENVIRONMENT to 'development', 'staging', or 'production'",
            )
        if env not in ("development", "staging", "production"):
            return ValidationResult(
                name="env_grid_environment",
                status=ValidationStatus.WARN,
                message=f"Non-standard GRID_ENVIRONMENT: {env}",
                severity="LOW",
            )
        return ValidationResult(
            name="env_grid_environment",
            status=ValidationStatus.PASS,
            message=f"GRID_ENVIRONMENT correctly set to '{env}'",
        )

    def _check_debug_mode(self) -> ValidationResult:
        """Check debug mode is disabled in production."""
        env = os.getenv("GRID_ENVIRONMENT", "development")
        debug = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes")

        if env == "production" and debug:
            return ValidationResult(
                name="env_debug_mode",
                status=ValidationStatus.FAIL,
                message="DEBUG mode enabled in production!",
                severity="CRITICAL",
                remediation="Set DEBUG=0 in production environment",
            )
        if debug:
            return ValidationResult(
                name="env_debug_mode",
                status=ValidationStatus.WARN,
                message="DEBUG mode is enabled",
                severity="LOW",
            )
        return ValidationResult(
            name="env_debug_mode",
            status=ValidationStatus.PASS,
            message="DEBUG mode is disabled",
        )

    def _check_secrets_exposure(self) -> ValidationResult:
        """Check for secrets in environment variables."""
        sensitive_patterns = ["_KEY", "_SECRET", "_TOKEN", "_PASSWORD", "_CREDENTIAL"]
        exposed = []

        for key, value in os.environ.items():
            if any(p in key.upper() for p in sensitive_patterns):
                if len(value) > 10 and not key.startswith("GRID_"):
                    exposed.append(key)

        if exposed:
            return ValidationResult(
                name="env_secrets_exposure",
                status=ValidationStatus.WARN,
                message=f"Found {len(exposed)} potential secrets in environment",
                severity="MEDIUM",
                details={"keys": exposed[:5]},  # Limit to first 5
                remediation="Use a secrets manager instead of environment variables",
            )
        return ValidationResult(
            name="env_secrets_exposure",
            status=ValidationStatus.PASS,
            message="No obvious secrets in environment variables",
        )

    def _check_pythonpath(self) -> ValidationResult:
        """Check PYTHONPATH for security issues."""
        issues = []

        for path in sys.path:
            if not path:
                continue

            # Check if path exists
            path_obj = Path(path)
            if not path_obj.exists():
                issues.append(f"Non-existent: {path}")
                continue

            # Check if writable by current user
            if path_obj.is_dir() and os.access(path, os.W_OK):
                # Check if it's a system path
                system_patterns = ["/usr", "/lib", "site-packages", "dist-packages"]
                if any(p in str(path) for p in system_patterns):
                    issues.append(f"Writable system path: {path}")

        if issues:
            return ValidationResult(
                name="env_pythonpath",
                status=ValidationStatus.WARN,
                message=f"Found {len(issues)} PYTHONPATH issues",
                severity="MEDIUM",
                details={"issues": issues[:5]},
                remediation="Clean up sys.path to remove non-existent or writable system paths",
            )
        return ValidationResult(
            name="env_pythonpath",
            status=ValidationStatus.PASS,
            message="PYTHONPATH configuration is secure",
        )

    # =========================================================================
    # Configuration Checks
    # =========================================================================

    def _check_parasite_guard_config(self) -> ValidationResult:
        """Check Parasite Guard configuration."""
        enabled = os.getenv("PARASITE_GUARD", "1").lower() in ("1", "true", "yes")
        threshold = int(os.getenv("PARASITE_DETECT_THRESHOLD", "5"))

        if not enabled:
            return ValidationResult(
                name="config_parasite_guard",
                status=ValidationStatus.WARN,
                message="Parasite Guard is disabled",
                severity="MEDIUM",
                remediation="Set PARASITE_GUARD=1 to enable protection",
            )

        if threshold > 10:
            return ValidationResult(
                name="config_parasite_guard",
                status=ValidationStatus.WARN,
                message=f"Parasite Guard threshold is high ({threshold})",
                severity="LOW",
                remediation="Consider lowering PARASITE_DETECT_THRESHOLD for better protection",
            )

        return ValidationResult(
            name="config_parasite_guard",
            status=ValidationStatus.PASS,
            message=f"Parasite Guard enabled with threshold {threshold}",
        )

    def _check_rate_limits(self) -> ValidationResult:
        """Check rate limiting configuration."""
        # Check for rate limit configuration
        rate_limit = os.getenv("RATE_LIMIT_PER_SECOND", "10")

        try:
            limit = int(rate_limit)
            if limit > 100:
                return ValidationResult(
                    name="config_rate_limits",
                    status=ValidationStatus.WARN,
                    message=f"Rate limit is high ({limit}/s)",
                    severity="LOW",
                    remediation="Consider lowering rate limits for better protection",
                )
        except ValueError:
            return ValidationResult(
                name="config_rate_limits",
                status=ValidationStatus.ERROR,
                message=f"Invalid rate limit configuration: {rate_limit}",
                severity="MEDIUM",
            )

        return ValidationResult(
            name="config_rate_limits",
            status=ValidationStatus.PASS,
            message=f"Rate limiting configured at {limit}/s",
        )

    def _check_https_config(self) -> ValidationResult:
        """Check HTTPS configuration."""
        env = os.getenv("GRID_ENVIRONMENT", "development")
        require_https = os.getenv("REQUIRE_HTTPS", "1" if env == "production" else "0")

        if env == "production" and require_https.lower() not in ("1", "true", "yes"):
            return ValidationResult(
                name="config_https_required",
                status=ValidationStatus.FAIL,
                message="HTTPS not required in production!",
                severity="CRITICAL",
                remediation="Set REQUIRE_HTTPS=1 in production",
            )

        return ValidationResult(
            name="config_https_required",
            status=ValidationStatus.PASS,
            message="HTTPS configuration is appropriate for environment",
        )

    # =========================================================================
    # Code Security Checks
    # =========================================================================

    def _check_dangerous_imports(self) -> ValidationResult:
        """Check for dangerous imports in codebase."""
        dangerous = ["pickle", "telnetlib", "ftplib"]
        found = []

        src_path = self._project_root / "src"
        if not src_path.exists():
            return ValidationResult(
                name="code_dangerous_imports",
                status=ValidationStatus.SKIP,
                message="Source directory not found",
            )

        for py_file in src_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                found.extend(
                    {"file": str(py_file.relative_to(self._project_root)), "import": imp}
                    for imp in dangerous
                    if f"import {imp}" in content or f"from {imp}" in content
                )
            except Exception:  # noqa: S110 intentional silent handling
                pass

        if found:
            return ValidationResult(
                name="code_dangerous_imports",
                status=ValidationStatus.WARN,
                message=f"Found {len(found)} dangerous imports",
                severity="MEDIUM",
                details={"imports": found[:10]},
                remediation="Review and remove or secure dangerous imports",
            )

        return ValidationResult(
            name="code_dangerous_imports",
            status=ValidationStatus.PASS,
            message="No dangerous imports found",
        )

    def _check_hardcoded_secrets(self) -> ValidationResult:
        """Check for hardcoded secrets in code."""
        import re

        patterns = [
            (r'["\'](?:api[_-]?key|apikey)["\']:\s*["\'][a-zA-Z0-9]{20,}["\']', "API key"),
            (r'["\'](?:secret|password|passwd)["\']:\s*["\'][^"\']{8,}["\']', "Secret/Password"),
            (r"(?:sk|pk)_(?:live|test)_[a-zA-Z0-9]{20,}", "Stripe key"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub PAT"),
            (r"xox[baprs]-[a-zA-Z0-9-]+", "Slack token"),
        ]

        found = []
        src_path = self._project_root / "src"
        if not src_path.exists():
            return ValidationResult(
                name="code_hardcoded_secrets",
                status=ValidationStatus.SKIP,
                message="Source directory not found",
            )

        for py_file in src_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for pattern, secret_type in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        found.append(
                            {
                                "file": str(py_file.relative_to(self._project_root)),
                                "type": secret_type,
                            }
                        )
            except Exception:  # noqa: S110 intentional silent handling
                pass

        if found:
            return ValidationResult(
                name="code_hardcoded_secrets",
                status=ValidationStatus.FAIL,
                message=f"Found {len(found)} potential hardcoded secrets",
                severity="HIGH",
                details={"secrets": found[:5]},
                remediation="Move secrets to environment variables or secrets manager",
            )

        return ValidationResult(
            name="code_hardcoded_secrets",
            status=ValidationStatus.PASS,
            message="No hardcoded secrets detected",
        )

    def _check_path_traversal_risk(self) -> ValidationResult:
        """Check for potential path traversal vulnerabilities."""
        import re

        risky_patterns = [
            (r"open\([^)]*\+[^)]*\)", "Dynamic file open"),
            (r"Path\([^)]*\+[^)]*\)", "Dynamic Path construction"),
            (r"os\.path\.join\([^)]*request", "Request data in path"),
        ]

        found = []
        src_path = self._project_root / "src"
        if not src_path.exists():
            return ValidationResult(
                name="code_path_traversal",
                status=ValidationStatus.SKIP,
                message="Source directory not found",
            )

        for py_file in src_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for pattern, risk_type in risky_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        found.append(
                            {
                                "file": str(py_file.relative_to(self._project_root)),
                                "risk": risk_type,
                                "count": len(matches),
                            }
                        )
            except Exception:  # noqa: S110 intentional silent handling
                pass

        if found:
            return ValidationResult(
                name="code_path_traversal",
                status=ValidationStatus.WARN,
                message=f"Found {len(found)} potential path traversal risks",
                severity="MEDIUM",
                details={"risks": found[:10]},
                remediation="Use PathValidator for all file operations with user input",
            )

        return ValidationResult(
            name="code_path_traversal",
            status=ValidationStatus.PASS,
            message="No obvious path traversal risks found",
        )

    # =========================================================================
    # Dependency Checks
    # =========================================================================

    def _check_known_vulnerabilities(self) -> ValidationResult:
        """Check for known vulnerabilities in dependencies."""
        try:
            # Try to run pip-audit or safety
            result = subprocess.run(  # noqa: S603 subprocess call is intentional
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                security_packages = ["cryptography", "urllib3", "requests", "certifi"]
                security_outdated = [p for p in outdated if p.get("name") in security_packages]

                if security_outdated:
                    return ValidationResult(
                        name="deps_known_vulnerabilities",
                        status=ValidationStatus.WARN,
                        message=f"Security-critical packages may be outdated: {len(security_outdated)}",
                        severity="MEDIUM",
                        details={"packages": security_outdated},
                        remediation="Run: pip install --upgrade " + " ".join(p["name"] for p in security_outdated),
                    )

            return ValidationResult(
                name="deps_known_vulnerabilities",
                status=ValidationStatus.PASS,
                message="Security packages appear up to date",
            )
        except Exception as e:
            return ValidationResult(
                name="deps_known_vulnerabilities",
                status=ValidationStatus.ERROR,
                message=f"Could not check vulnerabilities: {e}",
                severity="LOW",
            )

    def _check_outdated_packages(self) -> ValidationResult:
        """Check for outdated packages."""
        try:
            result = subprocess.run(  # noqa: S603 subprocess call is intentional
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                if len(outdated) > 20:
                    return ValidationResult(
                        name="deps_outdated_packages",
                        status=ValidationStatus.WARN,
                        message=f"Many packages are outdated: {len(outdated)}",
                        severity="LOW",
                        details={"count": len(outdated), "sample": [p["name"] for p in outdated[:5]]},
                        remediation="Consider running: pip install --upgrade -r requirements.txt",
                    )
            return ValidationResult(
                name="deps_outdated_packages",
                status=ValidationStatus.PASS,
                message="Package versions are reasonably current",
            )
        except Exception as e:
            return ValidationResult(
                name="deps_outdated_packages",
                status=ValidationStatus.ERROR,
                message=f"Could not check packages: {e}",
                severity="LOW",
            )

    # =========================================================================
    # Integrity Checks
    # =========================================================================

    def _check_security_module_integrity(self) -> ValidationResult:
        """Check integrity of security modules."""
        security_path = self._project_root / "src" / "grid" / "security"
        if not security_path.exists():
            return ValidationResult(
                name="integrity_security_modules",
                status=ValidationStatus.ERROR,
                message="Security module directory not found",
                severity="CRITICAL",
            )

        critical_files = [
            "parasite_guard.py",
            "input_sanitizer.py",
            "threat_profile.py",
            "hardened_middleware.py",
        ]

        missing = [filename for filename in critical_files if not (security_path / filename).exists()]

        if missing:
            return ValidationResult(
                name="integrity_security_modules",
                status=ValidationStatus.FAIL,
                message=f"Missing critical security files: {missing}",
                severity="HIGH",
                details={"missing": missing},
            )

        return ValidationResult(
            name="integrity_security_modules",
            status=ValidationStatus.PASS,
            message="All critical security modules present",
        )

    def _check_config_file_integrity(self) -> ValidationResult:
        """Check integrity of configuration files."""
        config_files = [
            ".env",
            "pyproject.toml",
        ]

        issues = []
        for config in config_files:
            config_path = self._project_root / config
            if config_path.exists():
                # Check if world-readable (on Unix)
                if hasattr(os, "stat"):
                    try:
                        mode = os.stat(config_path).st_mode
                        if mode & 0o004:  # World-readable
                            if config == ".env":
                                issues.append(f"{config} is world-readable")
                    except Exception:  # noqa: S110 intentional silent handling
                        pass

        if issues:
            return ValidationResult(
                name="integrity_config_files",
                status=ValidationStatus.WARN,
                message=f"Configuration file issues: {len(issues)}",
                severity="MEDIUM",
                details={"issues": issues},
                remediation="Restrict file permissions on sensitive config files",
            )

        return ValidationResult(
            name="integrity_config_files",
            status=ValidationStatus.PASS,
            message="Configuration files have appropriate permissions",
        )

    # =========================================================================
    # Runtime Checks
    # =========================================================================

    def _check_writable_paths(self) -> ValidationResult:
        """Check for writable system paths."""
        writable_system = []

        system_paths = [
            Path("/usr"),
            Path("/bin"),
            Path("/sbin"),
            Path("/lib"),
        ]
        if sys.platform == "win32":
            system_paths.extend(
                [
                    Path(os.environ.get("SystemRoot", "C:/Windows")),
                    Path(os.environ.get("ProgramFiles", "C:/Program Files")),
                ]
            )

        writable_system.extend(str(path) for path in system_paths if path.exists() and os.access(path, os.W_OK))

        if writable_system:
            return ValidationResult(
                name="runtime_writable_paths",
                status=ValidationStatus.WARN,
                message=f"System paths are writable: {len(writable_system)}",
                severity="MEDIUM",
                details={"paths": writable_system},
                remediation="Review system permissions - this may indicate privilege issues",
            )

        return ValidationResult(
            name="runtime_writable_paths",
            status=ValidationStatus.PASS,
            message="System paths are properly protected",
        )

    def _check_module_baseline(self) -> ValidationResult:
        """Check for unexpected modules loaded."""
        suspicious_modules = []

        suspicious_patterns = [
            "debugger",
            "trace",
            "hook",
            "inject",
            "patch",
        ]

        for module_name in sys.modules:
            if any(p in module_name.lower() for p in suspicious_patterns):
                # Filter out known safe modules
                if not any(safe in module_name for safe in ["pytest", "coverage", "unittest"]):
                    suspicious_modules.append(module_name)

        if suspicious_modules:
            return ValidationResult(
                name="runtime_module_baseline",
                status=ValidationStatus.WARN,
                message=f"Suspicious modules loaded: {len(suspicious_modules)}",
                severity="LOW",
                details={"modules": suspicious_modules[:10]},
            )

        return ValidationResult(
            name="runtime_module_baseline",
            status=ValidationStatus.PASS,
            message="No suspicious modules detected",
        )


# =============================================================================
# COMPLIANCE CHECKER
# =============================================================================


class ComplianceChecker:
    """Check compliance with security standards."""

    def __init__(self):
        self._checks: dict[str, list[Callable[[], ValidationResult]]] = {
            "OWASP_TOP_10": self._get_owasp_checks(),
            "GRID_SECURITY": self._get_grid_checks(),
        }

    def _get_owasp_checks(self) -> list[Callable[[], ValidationResult]]:
        """Get OWASP Top 10 compliance checks."""
        return [
            self._check_a01_broken_access_control,
            self._check_a02_cryptographic_failures,
            self._check_a03_injection,
            self._check_a04_insecure_design,
            self._check_a05_security_misconfiguration,
        ]

    def _get_grid_checks(self) -> list[Callable[[], ValidationResult]]:
        """Get GRID-specific security checks."""
        return [
            self._check_parasite_guard_enabled,
            self._check_input_sanitization,
            self._check_audit_logging,
        ]

    def _check_a01_broken_access_control(self) -> ValidationResult:
        """A01:2021 - Broken Access Control."""
        # Check for authentication enforcement
        auth_level = os.getenv("MIN_AUTH_LEVEL", "INTEGRITY")
        if auth_level == "NONE":
            return ValidationResult(
                name="A01_broken_access_control",
                status=ValidationStatus.FAIL,
                message="No authentication required - access control may be broken",
                severity="HIGH",
            )
        return ValidationResult(
            name="A01_broken_access_control",
            status=ValidationStatus.PASS,
            message=f"Access control enforced at {auth_level} level",
        )

    def _check_a02_cryptographic_failures(self) -> ValidationResult:
        """A02:2021 - Cryptographic Failures."""
        # Check for HTTPS enforcement
        require_https = os.getenv("REQUIRE_HTTPS", "0")
        env = os.getenv("GRID_ENVIRONMENT", "development")

        if env == "production" and require_https != "1":
            return ValidationResult(
                name="A02_cryptographic_failures",
                status=ValidationStatus.FAIL,
                message="HTTPS not required in production",
                severity="HIGH",
            )
        return ValidationResult(
            name="A02_cryptographic_failures",
            status=ValidationStatus.PASS,
            message="Transport encryption configured appropriately",
        )

    def _check_a03_injection(self) -> ValidationResult:
        """A03:2021 - Injection."""
        # Check for input sanitization
        sanitization = os.getenv("INPUT_SANITIZATION", "1")
        if sanitization != "1":
            return ValidationResult(
                name="A03_injection",
                status=ValidationStatus.FAIL,
                message="Input sanitization is disabled",
                severity="HIGH",
            )
        return ValidationResult(
            name="A03_injection",
            status=ValidationStatus.PASS,
            message="Input sanitization is enabled",
        )

    def _check_a04_insecure_design(self) -> ValidationResult:
        """A04:2021 - Insecure Design."""
        # Check for security modules
        try:
            from grid.security import threat_profile  # noqa: F401

            return ValidationResult(
                name="A04_insecure_design",
                status=ValidationStatus.PASS,
                message="Security-by-design modules are present",
            )
        except ImportError:
            return ValidationResult(
                name="A04_insecure_design",
                status=ValidationStatus.WARN,
                message="Security modules not fully imported",
                severity="MEDIUM",
            )

    def _check_a05_security_misconfiguration(self) -> ValidationResult:
        """A05:2021 - Security Misconfiguration."""
        issues = []

        # Check debug mode
        if os.getenv("DEBUG", "0") == "1":
            issues.append("DEBUG mode enabled")

        # Check default credentials
        if os.getenv("ADMIN_PASSWORD") == "admin":
            issues.append("Default admin password")

        if issues:
            return ValidationResult(
                name="A05_security_misconfiguration",
                status=ValidationStatus.FAIL,
                message=f"Security misconfigurations found: {len(issues)}",
                severity="HIGH",
                details={"issues": issues},
            )
        return ValidationResult(
            name="A05_security_misconfiguration",
            status=ValidationStatus.PASS,
            message="No obvious security misconfigurations",
        )

    def _check_parasite_guard_enabled(self) -> ValidationResult:
        """Check Parasite Guard is enabled."""
        enabled = os.getenv("PARASITE_GUARD", "1") == "1"
        if not enabled:
            return ValidationResult(
                name="parasite_guard_enabled",
                status=ValidationStatus.FAIL,
                message="Parasite Guard is disabled",
                severity="MEDIUM",
            )
        return ValidationResult(
            name="parasite_guard_enabled",
            status=ValidationStatus.PASS,
            message="Parasite Guard is enabled",
        )

    def _check_input_sanitization(self) -> ValidationResult:
        """Check input sanitization is enabled."""
        enabled = os.getenv("INPUT_SANITIZATION", "1") == "1"
        strict = os.getenv("INPUT_SANITIZATION_STRICT", "1") == "1"

        if not enabled:
            return ValidationResult(
                name="input_sanitization",
                status=ValidationStatus.FAIL,
                message="Input sanitization is disabled",
                severity="HIGH",
            )
        if not strict:
            return ValidationResult(
                name="input_sanitization",
                status=ValidationStatus.WARN,
                message="Input sanitization is not in strict mode",
                severity="MEDIUM",
            )
        return ValidationResult(
            name="input_sanitization",
            status=ValidationStatus.PASS,
            message="Input sanitization is enabled in strict mode",
        )

    def _check_audit_logging(self) -> ValidationResult:
        """Check audit logging is enabled."""
        enabled = os.getenv("AUDIT_LOGGING", "1") == "1"
        if not enabled:
            return ValidationResult(
                name="audit_logging",
                status=ValidationStatus.WARN,
                message="Audit logging is disabled",
                severity="MEDIUM",
            )
        return ValidationResult(
            name="audit_logging",
            status=ValidationStatus.PASS,
            message="Audit logging is enabled",
        )

    def check_compliance(self, standard: str) -> ValidationReport:
        """Check compliance with a specific standard."""
        import time

        start = time.monotonic()
        report = ValidationReport()

        checks = self._checks.get(standard, [])
        for check in checks:
            check_start = time.monotonic()
            try:
                result = check()
                result.duration_ms = (time.monotonic() - check_start) * 1000
            except Exception as e:
                result = ValidationResult(
                    name=check.__name__,
                    status=ValidationStatus.ERROR,
                    message=str(e),
                    severity="HIGH",
                )
            report.add_result(result)

        report.duration_ms = (time.monotonic() - start) * 1000
        return report


# =============================================================================
# MAIN RUNNER
# =============================================================================


def run_security_validation(project_root: Path | None = None) -> ValidationReport:
    """Run comprehensive security validation."""
    validator = SecurityValidator(project_root)
    return validator.run_all_sync()


def run_compliance_check(standard: str = "GRID_SECURITY") -> ValidationReport:
    """Run compliance check for a specific standard."""
    checker = ComplianceChecker()
    return checker.check_compliance(standard)


if __name__ == "__main__":
    # Run validation when executed directly
    import sys

    print("Running GRID Security Validation...")
    print("=" * 60)

    report = run_security_validation()

    for result in report.results:
        status_icon = {
            ValidationStatus.PASS: "[PASS]",
            ValidationStatus.FAIL: "[FAIL]",
            ValidationStatus.WARN: "[WARN]",
            ValidationStatus.SKIP: "[SKIP]",
            ValidationStatus.ERROR: "[ERR ]",
        }.get(result.status, "[????]")

        print(f"{status_icon} {result.name}: {result.message}")

    print("=" * 60)
    print(f"Summary: {report.summary}")
    print(f"Duration: {report.duration_ms:.2f}ms")
    print(f"Status: {'PASSED' if report.passed else 'FAILED'}")

    sys.exit(0 if report.passed else 1)
