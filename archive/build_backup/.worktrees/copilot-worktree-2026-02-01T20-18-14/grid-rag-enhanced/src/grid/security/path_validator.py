"""Centralized path validation utility for GRID security."""

from collections.abc import Sequence
from pathlib import Path


class SecurityError(Exception):
    """Raised when a security constraint is violated."""

    pass


class PathValidator:
    """Centralized utility for validating file paths to prevent path traversal attacks."""

    @staticmethod
    def validate_path(path: str | Path, base_path: str | Path) -> Path:
        """
        Validate that a path is within the allowed base path.

        Args:
            path: The path to validate (can be relative or absolute)
            base_path: The allowed base directory

        Returns:
            The resolved and validated absolute path

        Raises:
            SecurityError: If the path is outside the allowed base path
        """
        base = Path(base_path).resolve()

        # Handle absolute paths - only allow if they're within base
        target_path = Path(path)
        if target_path.is_absolute():
            target = target_path.resolve()
        else:
            # For relative paths, resolve against base
            try:
                target = (base / target_path).resolve()
            except (ValueError, OSError):
                # Handle path traversal that goes outside base
                raise SecurityError(f"Access denied: {path} outside allowed directory {base}")

        # Security check: ensure the resolved path is still within base path
        try:
            if not target.is_relative_to(base):
                raise SecurityError(f"Access denied: {path} outside allowed directory {base}")
        except ValueError:
            # Handle case where paths are on different drives (Windows)
            raise SecurityError(f"Access denied: {path} on different drive from allowed directory {base}")

        return target

    @staticmethod
    def validate_file_exists(path: str | Path, base_path: str | Path) -> Path:
        """
        Validate path and check if file exists.

        Args:
            path: The path to validate
            base_path: The allowed base directory

        Returns:
            The validated path if file exists

        Raises:
            SecurityError: If path is invalid or outside allowed directory
            FileNotFoundError: If file does not exist
        """
        validated_path = PathValidator.validate_path(path, base_path)

        if not validated_path.exists():
            raise FileNotFoundError(f"File not found: {validated_path}")

        if not validated_path.is_file():
            raise SecurityError(f"Path is not a file: {validated_path}")

        return validated_path

    @staticmethod
    def validate_safe_directory(path: str | Path, allowed_directories: Sequence[str | Path]) -> Path:
        """
        Validate that a directory is within a list of allowed directories.

        Args:
            path: The directory path to validate
            allowed_directories: List of allowed base directories

        Returns:
            The resolved and validated directory path

        Raises:
            SecurityError: If the directory is not within any allowed directory
        """
        target = Path(path).resolve()
        allowed_resolved = [Path(allowed).resolve() for allowed in allowed_directories]

        for allowed in allowed_resolved:
            try:
                if target.is_relative_to(allowed):
                    return target
            except ValueError:
                # Different drives on Windows - continue checking
                continue

        raise SecurityError(f"Directory not allowed: {path}")

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename to prevent directory traversal.

        Args:
            filename: The filename to sanitize

        Returns:
            Sanitized filename safe for use
        """
        # Remove path separators and other dangerous characters
        sanitized = filename.replace("/", "_").replace("\\", "_")
        sanitized = sanitized.replace("..", "_")
        sanitized = sanitized.replace("\x00", "_")  # Null bytes

        # Remove any leading dots that could be used for hidden files
        sanitized = sanitized.lstrip(".")

        # Ensure filename is not empty
        if not sanitized:
            sanitized = "unnamed_file"

        return sanitized

    @staticmethod
    def validate_extension(path: str | Path, allowed_extensions: set[str]) -> Path:
        """
        Validate that a file has an allowed extension.

        Args:
            path: The file path to validate
            allowed_extensions: Set of allowed file extensions (including the dot)

        Returns:
            The validated path

        Raises:
            SecurityError: If file extension is not allowed
        """
        file_path = Path(path)
        extension = file_path.suffix.lower()

        if extension not in allowed_extensions:
            raise SecurityError(f"File extension not allowed: {extension}")

        return file_path
