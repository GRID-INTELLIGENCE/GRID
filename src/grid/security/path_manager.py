"""
Secure Path Manager for GRID.

Centralized, secure sys.path management with validation and cleanup.
Prevents path traversal attacks and ensures only valid, safe paths are added.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .path_validator import SecurityError

logger = logging.getLogger(__name__)


@dataclass
class PathValidationResult:
    """Result of path validation."""

    path: Path
    is_valid: bool
    exists: bool
    is_directory: bool
    is_writable: bool
    contains_python_files: bool = False
    reason: str | None = None


@dataclass
class PathManagerReport:
    """Report from path management operations."""

    added_paths: list[str] = field(default_factory=list)
    removed_paths: list[str] = field(default_factory=list)
    invalid_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class SecurePathManager:
    """
    Centralized, secure sys.path management.

    Provides safe methods for adding paths to sys.path with validation,
    preventing path traversal attacks and ensuring only valid paths are used.

    Example:
        >>> manager = SecurePathManager()
        >>> report = manager.add_project_paths(Path("/grid"))
        >>> manager.validate_and_clean()
    """

    # Dangerous path patterns that should never be added
    DANGEROUS_PATTERNS: list[str] = [
        "/tmp",
        "/var/tmp",
        ";",
        "&&",
        "|",
        "..",
    ]

    # System paths that should be avoided (Windows)
    SYSTEM_PATH_INDICATORS: list[str] = [
        "\\windows\\system32",
        "\\program files\\",
        "\\program files (x86)\\",  # noqa: RUF001
    ]

    def __init__(self, base_dir: Path | None = None) -> None:
        """
        Initialize path manager.

        Args:
            base_dir: Base directory for relative path resolution
        """
        self.base_dir = base_dir or Path.cwd()
        self._added_paths: set[str] = set()

    def validate_path(self, path: str | Path) -> PathValidationResult:
        """
        Validate a path before adding it to sys.path.

        Args:
            path: Path to validate

        Returns:
            PathValidationResult with validation details
        """
        try:
            path_obj = Path(path)
            if not path_obj.is_absolute():
                # Resolve relative paths against base_dir
                path_obj = (self.base_dir / path_obj).resolve()

            # Check for dangerous patterns
            path_str = str(path_obj).lower()
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern in path_str:
                    return PathValidationResult(
                        path=path_obj,
                        is_valid=False,
                        exists=False,
                        is_directory=False,
                        is_writable=False,
                        reason=f"Path contains dangerous pattern: {pattern}",
                    )

            # Check if path exists
            if not path_obj.exists():
                return PathValidationResult(
                    path=path_obj,
                    is_valid=False,
                    exists=False,
                    is_directory=False,
                    is_writable=False,
                    reason="Path does not exist",
                )

            # Check if it's a directory
            is_dir = path_obj.is_dir()
            if not is_dir:
                return PathValidationResult(
                    path=path_obj,
                    is_valid=False,
                    exists=True,
                    is_directory=False,
                    is_writable=False,
                    reason="Path is not a directory",
                )

            # Check write permissions
            is_writable = os.access(path_obj, os.W_OK)

            # Check if contains Python files
            contains_python = False
            try:
                files = list(path_obj.iterdir())
                contains_python = any(
                    f.suffix in (".py", ".pyd", ".so") or f.name.endswith(".pyc")
                    for f in files[:10]  # Sample first 10 files
                )
            except (PermissionError, OSError):
                pass

            return PathValidationResult(
                path=path_obj,
                is_valid=True,
                exists=True,
                is_directory=True,
                is_writable=is_writable,
                contains_python_files=contains_python,
            )

        except (OSError, ValueError) as e:
            return PathValidationResult(
                path=Path(path) if isinstance(path, str) else path,
                is_valid=False,
                exists=False,
                is_directory=False,
                is_writable=False,
                reason=f"Path validation error: {e}",
            )

    def add_path(
        self,
        path: str | Path,
        validate: bool = True,
        position: int | None = None,
    ) -> PathValidationResult:
        """
        Add a path to sys.path with validation.

        Args:
            path: Path to add
            validate: Whether to validate the path before adding
            position: Position to insert (None = append, 0 = prepend)

        Returns:
            PathValidationResult indicating success or failure

        Raises:
            SecurityError: If path validation fails and validate=True
        """
        if validate:
            result = self.validate_path(path)
            if not result.is_valid:
                raise SecurityError(f"Cannot add invalid path: {result.reason}")

            path_str = str(result.path)
        else:
            path_str = str(Path(path).resolve())

        # Check if already in sys.path
        if path_str in sys.path:
            logger.debug(f"Path already in sys.path: {path_str}")
            return PathValidationResult(
                path=Path(path_str),
                is_valid=True,
                exists=True,
                is_directory=True,
                is_writable=False,
            )

        # Add to sys.path
        if position is None:
            sys.path.append(path_str)
        else:
            sys.path.insert(position, path_str)

        self._added_paths.add(path_str)
        logger.debug(f"Added path to sys.path: {path_str}")

        if validate:
            return self.validate_path(path_str)
        return PathValidationResult(
            path=Path(path_str),
            is_valid=True,
            exists=True,
            is_directory=True,
            is_writable=False,
        )

    def add_project_paths(
        self,
        base_dir: Path | None = None,
        include_src: bool = True,
        include_tools: bool = True,
        include_root: bool = True,
    ) -> PathManagerReport:
        """
        Add standard GRID project paths with validation.

        Args:
            base_dir: Base directory (defaults to self.base_dir)
            include_src: Whether to include src/ directory
            include_tools: Whether to include tools/ directory
            include_root: Whether to include project root

        Returns:
            PathManagerReport with operation results
        """
        base = base_dir or self.base_dir
        report = PathManagerReport()

        paths_to_add: list[tuple[Path, str]] = []

        if include_root:
            paths_to_add.append((base, "project root"))

        if include_src:
            src_path = base / "src"
            if src_path.exists():
                paths_to_add.append((src_path, "src directory"))

        if include_tools:
            tools_path = base / "tools"
            if tools_path.exists():
                paths_to_add.append((tools_path, "tools directory"))

        for path, description in paths_to_add:
            try:
                result = self.add_path(path, validate=True)
                if result.is_valid:
                    report.added_paths.append(str(path))
                    logger.info(f"Added {description}: {path}")
                else:
                    report.invalid_paths.append(str(path))
                    report.warnings.append(f"Could not add {description}: {result.reason}")
            except SecurityError as e:
                report.invalid_paths.append(str(path))
                report.errors.append(f"Security error adding {description}: {e}")

        return report

    def validate_and_clean(self) -> PathManagerReport:
        """
        Validate all paths in sys.path and remove invalid ones.

        Returns:
            PathManagerReport with cleanup results
        """
        report = PathManagerReport()
        paths_to_remove: list[str] = []

        for path_str in sys.path:
            if not path_str:
                paths_to_remove.append(path_str)
                continue

            try:
                result = self.validate_path(path_str)

                if not result.is_valid:
                    paths_to_remove.append(path_str)
                    report.removed_paths.append(path_str)
                    report.warnings.append(f"Removed invalid path: {path_str} ({result.reason})")
                elif not result.exists:
                    paths_to_remove.append(path_str)
                    report.removed_paths.append(path_str)
                    report.warnings.append(f"Removed non-existent path: {path_str}")

            except Exception as e:
                logger.warning(f"Error validating path {path_str}: {e}")
                # Don't remove on validation error - might be a temporary issue

        # Remove invalid paths
        for path in paths_to_remove:
            if path in sys.path:
                sys.path.remove(path)

        if report.removed_paths:
            logger.info(f"Cleaned {len(report.removed_paths)} invalid paths from sys.path")

        return report

    def get_path_report(self) -> dict[str, Any]:
        """
        Generate a report of current sys.path state.

        Returns:
            Dictionary with path analysis
        """
        report: dict[str, Any] = {
            "total_paths": len(sys.path),
            "valid_paths": 0,
            "invalid_paths": 0,
            "non_existent_paths": 0,
            "writable_paths": 0,
            "paths": [],
        }

        for path_str in sys.path:
            result = self.validate_path(path_str)
            path_info: dict[str, Any] = {
                "path": path_str,
                "valid": result.is_valid,
                "exists": result.exists,
                "is_directory": result.is_directory,
                "is_writable": result.is_writable,
                "contains_python_files": result.contains_python_files,
            }

            if result.is_valid:
                report["valid_paths"] += 1
            else:
                report["invalid_paths"] += 1
                path_info["reason"] = result.reason

            if not result.exists:
                report["non_existent_paths"] += 1

            if result.is_writable:
                report["writable_paths"] += 1

            report["paths"].append(path_info)

        return report

    @classmethod
    def clean_pythonpath(cls) -> list[str]:
        """
        Clean PYTHONPATH environment variable, removing non-existent paths.

        Returns:
            List of removed paths
        """
        pythonpath = os.environ.get("PYTHONPATH", "")
        if not pythonpath:
            return []

        # Split by platform-appropriate separator
        if os.name == "nt":  # Windows
            paths = pythonpath.split(";")
        else:  # Unix-like
            paths = pythonpath.split(":")

        valid_paths: list[str] = []
        removed_paths: list[str] = []

        for path_str in paths:
            if not path_str.strip():
                continue

            try:
                path = Path(path_str.strip())
                if path.exists() and path.is_dir():
                    valid_paths.append(path_str)
                else:
                    removed_paths.append(path_str)
            except (OSError, ValueError):
                removed_paths.append(path_str)

        # Update PYTHONPATH
        if os.name == "nt":
            os.environ["PYTHONPATH"] = ";".join(valid_paths)
        else:
            os.environ["PYTHONPATH"] = ":".join(valid_paths)

        if removed_paths:
            logger.info(f"Cleaned {len(removed_paths)} non-existent paths from PYTHONPATH")

        return removed_paths
