"""
Environment Hardening Startup Module.

Provides startup hooks for environment hardening that can be integrated
into FastAPI lifespan, CLI entry points, and module imports.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .environment import sanitize_environment, sanitize_path
from .path_manager import PathManagerReport, SecurePathManager

logger = logging.getLogger(__name__)


class HardeningLevel(str, Enum):
    """Level of environment hardening to apply."""

    NONE = "none"
    MINIMAL = "minimal"  # Only critical security issues
    STANDARD = "standard"  # Default - clean paths, validate environment
    STRICT = "strict"  # Full validation with fail-fast on issues


@dataclass
class EnvironmentReport:
    """Report from environment hardening."""

    level: HardeningLevel
    success: bool
    has_critical_issues: bool
    path_cleanup: PathManagerReport | None = None
    pythonpath_cleaned: list[str] = field(default_factory=list)
    sys_path_cleaned: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "success": self.success,
            "has_critical_issues": self.has_critical_issues,
            "pythonpath_cleaned_count": len(self.pythonpath_cleaned),
            "sys_path_cleaned_count": len(self.sys_path_cleaned),
            "warnings": self.warnings,
            "errors": self.errors,
            "details": self.details,
        }


def harden_environment(
    level: HardeningLevel = HardeningLevel.STANDARD,
    base_dir: Path | None = None,
    fail_on_critical: bool = False,
) -> EnvironmentReport:
    """
    Harden the Python environment at startup.

    Performs comprehensive environment sanitization and validation:
    - Sanitizes PATH and PYTHONPATH
    - Validates and cleans sys.path
    - Removes non-existent paths
    - Validates path permissions

    Args:
        level: Hardening level to apply
        base_dir: Base directory for path resolution (defaults to cwd)
        fail_on_critical: If True, raise exception on critical issues

    Returns:
        EnvironmentReport with hardening results

    Raises:
        SecurityError: If fail_on_critical=True and critical issues found
    """
    if level == HardeningLevel.NONE:
        return EnvironmentReport(
            level=level,
            success=True,
            has_critical_issues=False,
        )

    report = EnvironmentReport(level=level, success=True, has_critical_issues=False)

    try:
        # Step 1: Sanitize PATH and PYTHONPATH
        if level in [HardeningLevel.STANDARD, HardeningLevel.STRICT]:
            try:
                sanitize_path()
                logger.debug("PATH sanitized")
            except Exception as e:
                report.warnings.append(f"PATH sanitization warning: {e}")

            # Clean PYTHONPATH
            try:
                removed = SecurePathManager.clean_pythonpath()
                report.pythonpath_cleaned = removed
                if removed:
                    logger.info(f"Cleaned {len(removed)} non-existent paths from PYTHONPATH")
            except Exception as e:
                report.warnings.append(f"PYTHONPATH cleanup warning: {e}")

        # Step 2: Validate and clean sys.path
        if level in [HardeningLevel.STANDARD, HardeningLevel.STRICT]:
            try:
                manager = SecurePathManager(base_dir=base_dir or Path.cwd())
                path_report = manager.validate_and_clean()
                report.path_cleanup = path_report
                report.sys_path_cleaned = path_report.removed_paths

                if path_report.removed_paths:
                    logger.info(f"Cleaned {len(path_report.removed_paths)} invalid paths from sys.path")

                if path_report.warnings:
                    report.warnings.extend(path_report.warnings)

            except Exception as e:
                report.warnings.append(f"sys.path cleanup warning: {e}")

        # Step 3: Full environment sanitization
        if level == HardeningLevel.STRICT:
            try:
                changes = sanitize_environment()
                if changes:
                    report.details["environment_changes"] = changes
                    logger.info("Full environment sanitization completed")
            except Exception as e:
                report.warnings.append(f"Environment sanitization warning: {e}")

        # Step 4: Validate critical paths
        if level == HardeningLevel.STRICT:
            try:
                manager = SecurePathManager(base_dir=base_dir or Path.cwd())
                path_report = manager.get_path_report()
                report.details["path_report"] = path_report

                # Check for critical issues
                if path_report["non_existent_paths"] > 0:
                    report.warnings.append(f"Found {path_report['non_existent_paths']} non-existent paths in sys.path")

                if path_report["writable_paths"] > 5:  # Threshold for warning
                    report.warnings.append(f"Found {path_report['writable_paths']} writable paths in sys.path")

            except Exception as e:
                report.warnings.append(f"Path validation warning: {e}")

        # Determine if there are critical issues
        report.has_critical_issues = len(report.errors) > 0

        if report.has_critical_issues and fail_on_critical:
            from .path_validator import SecurityError

            raise SecurityError(f"Environment hardening failed with critical issues: {', '.join(report.errors)}")

        if report.warnings:
            logger.warning(f"Environment hardening completed with {len(report.warnings)} warnings")

        logger.info(f"Environment hardening completed (level: {level.value})")

    except Exception as e:
        report.success = False
        report.errors.append(str(e))
        logger.error(f"Environment hardening failed: {e}", exc_info=True)

        if fail_on_critical:
            raise

    return report


def get_environment_status() -> dict[str, Any]:
    """
    Get current environment status without making changes.

    Returns:
        Dictionary with environment status information
    """
    manager = SecurePathManager()
    path_report = manager.get_path_report()

    pythonpath = os.environ.get("PYTHONPATH", "")
    pythonpath_paths = pythonpath.split(os.pathsep) if pythonpath else []

    return {
        "sys_path": {
            "total": path_report["total_paths"],
            "valid": path_report["valid_paths"],
            "invalid": path_report["invalid_paths"],
            "non_existent": path_report["non_existent_paths"],
            "writable": path_report["writable_paths"],
        },
        "pythonpath": {
            "total": len(pythonpath_paths),
            "paths": pythonpath_paths,
        },
        "python": {
            "executable": sys.executable,
            "version": sys.version,
        },
    }


# Feature flag for environment hardening
ENABLE_HARDENING = os.getenv("GRID_ENABLE_ENV_HARDENING", "1").lower() in ("1", "true", "yes")


def should_harden_environment() -> bool:
    """
    Check if environment hardening should be enabled.

    Returns:
        True if hardening should be applied
    """
    return ENABLE_HARDENING


def get_hardening_level() -> HardeningLevel:
    """
    Get hardening level from environment variable.

    Returns:
        HardeningLevel enum value
    """
    level_str = os.getenv("GRID_ENV_HARDENING_LEVEL", "standard").lower()
    try:
        return HardeningLevel(level_str)
    except ValueError:
        logger.warning(f"Invalid hardening level '{level_str}', using 'standard'")
        return HardeningLevel.STANDARD
