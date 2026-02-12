"""
Input validation utilities for workspace utilities.
"""

from pathlib import Path
from typing import Optional
from .exceptions import ValidationError, ConfigurationError


def validate_root_path(path: str, must_exist: bool = True) -> Path:
    """Validate and normalize root path.
    
    Args:
        path: Path to validate
        must_exist: Whether the path must exist (default: True)
    
    Returns:
        Resolved Path object
    
    Raises:
        ValidationError: If path is invalid
    """
    try:
        path_obj = Path(path)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid path format: {path}") from e
    
    if must_exist:
        if not path_obj.exists():
            raise ValidationError(
                f"Root path does not exist: {path}\n"
                f"Please ensure the path exists and is accessible."
            )
        if not path_obj.is_dir():
            raise ValidationError(
                f"Root path is not a directory: {path}\n"
                f"Please provide a directory path, not a file."
            )
    
    try:
        return path_obj.resolve()
    except (OSError, PermissionError) as e:
        raise ValidationError(
            f"Cannot access path: {path}\n"
            f"Error: {str(e)}\n"
            f"Please check file permissions."
        ) from e


def validate_output_dir(path: str, create: bool = True) -> Path:
    """Validate and optionally create output directory.
    
    Args:
        path: Output directory path
        create: Whether to create the directory if it doesn't exist (default: True)
    
    Returns:
        Resolved Path object
    
    Raises:
        ValidationError: If path is invalid or cannot be created
    """
    try:
        path_obj = Path(path)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid output path format: {path}") from e
    
    if path_obj.exists():
        if not path_obj.is_dir():
            raise ValidationError(
                f"Output path exists but is not a directory: {path}\n"
                f"Please provide a directory path."
            )
        if not path_obj.is_writable():
            raise ValidationError(
                f"Output directory is not writable: {path}\n"
                f"Please check write permissions."
            )
    elif create:
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise ValidationError(
                f"Cannot create output directory: {path}\n"
                f"Error: {str(e)}\n"
                f"Please check parent directory permissions."
            ) from e
    else:
        raise ValidationError(
            f"Output directory does not exist: {path}\n"
            f"Please create it first or use --create-output flag."
        )
    
    return path_obj.resolve()


def validate_analysis_dir(path: str) -> Path:
    """Validate analysis output directory.
    
    Args:
        path: Analysis directory path
    
    Returns:
        Resolved Path object
    
    Raises:
        ValidationError: If analysis directory is invalid
    """
    try:
        path_obj = Path(path)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid analysis directory path: {path}") from e
    
    if not path_obj.exists():
        raise ValidationError(
            f"Analysis directory does not exist: {path}\n"
            f"Please run analysis first or provide a valid analysis directory."
        )
    
    if not path_obj.is_dir():
        raise ValidationError(
            f"Analysis path is not a directory: {path}"
        )
    
    # Check for required files
    required_files = ["candidates.json", "module_graph.json"]
    missing_files = [f for f in required_files if not (path_obj / f).exists()]
    
    if missing_files:
        raise ValidationError(
            f"Analysis directory is missing required files: {', '.join(missing_files)}\n"
            f"Please ensure you're providing a valid analysis output directory."
        )
    
    return path_obj.resolve()


def validate_max_depth(depth: int) -> int:
    """Validate maximum recursion depth.
    
    Args:
        depth: Maximum depth value
    
    Returns:
        Validated depth value
    
    Raises:
        ValidationError: If depth is invalid
    """
    if not isinstance(depth, int):
        raise ValidationError(f"Max depth must be an integer, got: {type(depth)}")
    
    if depth < 1:
        raise ValidationError(
            f"Max depth must be at least 1, got: {depth}\n"
            f"Use 1-10 for typical analysis."
        )
    
    if depth > 20:
        raise ValidationError(
            f"Max depth is too large (max 20), got: {depth}\n"
            f"Very large depths may cause performance issues."
        )
    
    return depth


def validate_file_size_limit(size_mb: int) -> int:
    """Validate file size limit in MB.
    
    Args:
        size_mb: File size limit in megabytes
    
    Returns:
        Validated size limit
    
    Raises:
        ValidationError: If size limit is invalid
    """
    if not isinstance(size_mb, int):
        raise ValidationError(f"File size limit must be an integer, got: {type(size_mb)}")
    
    if size_mb < 1:
        raise ValidationError(
            f"File size limit must be at least 1 MB, got: {size_mb}"
        )
    
    if size_mb > 100:
        raise ValidationError(
            f"File size limit is too large (max 100 MB), got: {size_mb}\n"
            f"Very large files may cause performance issues."
        )
    
    return size_mb


def validate_exclude_patterns(patterns: str) -> list:
    """Validate and parse exclude patterns.
    
    Args:
        patterns: Comma-separated exclude patterns
    
    Returns:
        List of validated patterns
    
    Raises:
        ValidationError: If patterns are invalid
    """
    if not patterns:
        return []
    
    if not isinstance(patterns, str):
        raise ValidationError(f"Exclude patterns must be a string, got: {type(patterns)}")
    
    pattern_list = [p.strip() for p in patterns.split(',')]
    pattern_list = [p for p in pattern_list if p]  # Remove empty strings
    
    if not pattern_list:
        raise ValidationError("Exclude patterns cannot be empty after parsing")
    
    # Validate each pattern
    for pattern in pattern_list:
        if not pattern or pattern.startswith('.'):
            continue  # Allow hidden files/dirs
        if '/' in pattern or '\\' in pattern:
            raise ValidationError(
                f"Exclude patterns cannot contain path separators: {pattern}\n"
                f"Use directory names only (e.g., 'node_modules', not 'src/node_modules')."
            )
    
    return pattern_list