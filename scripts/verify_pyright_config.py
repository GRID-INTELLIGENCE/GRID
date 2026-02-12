#!/usr/bin/env python3
"""
Verify pyrightconfig.json exclude patterns and identify files being analyzed.
This script helps debug basedpyright performance issues by showing what files
would be included/excluded based on the current configuration.
"""

import fnmatch
import json
from collections import defaultdict
from pathlib import Path


def load_pyright_config(config_path: Path) -> dict:
    """Load and parse pyrightconfig.json."""
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_path}: {e}")
        return {}


def matches_pattern(path: Path, pattern: str, root: Path) -> bool:
    """
    Check if a path matches a glob pattern.
    Handles both relative and absolute patterns.
    """
    # Convert to relative path from root
    try:
        rel_path = path.relative_to(root)
    except ValueError:
        # Path is outside root, check absolute
        rel_path = path

    # Normalize path separators
    path_str = str(rel_path).replace("\\", "/")
    pattern_str = pattern.replace("\\", "/")

    # Special handling for **/.* pattern - should match hidden files/dirs, not all files
    if pattern_str == "**/.*":
        # Match if any part of the path starts with a dot
        parts = path_str.split("/")
        return any(part.startswith(".") for part in parts if part)

    # Handle ** patterns
    if "**" in pattern_str:
        # Convert ** pattern to fnmatch-compatible
        pattern_parts = pattern_str.split("**")
        if len(pattern_parts) == 2:
            # Pattern like "**/something" or "something/**"
            if pattern_str.startswith("**/"):
                # Match anywhere
                suffix = pattern_str[3:]
                if suffix:
                    return fnmatch.fnmatch(path_str, f"*{suffix}") or fnmatch.fnmatch(path_str, suffix)
                else:
                    return True  # **/ matches everything
            elif pattern_str.endswith("/**"):
                # Match directory and all subdirectories
                prefix = pattern_str[:-3]
                return path_str.startswith(prefix) if prefix else True
            else:
                # Pattern like "a/**/b"
                return fnmatch.fnmatch(path_str, pattern_str.replace("**", "*"))

    # Simple pattern matching
    return fnmatch.fnmatch(path_str, pattern_str) or fnmatch.fnmatch(str(path), pattern_str)


def is_excluded(path: Path, exclude_patterns: list[str], root: Path) -> bool:
    """Check if a path matches any exclude pattern."""
    for pattern in exclude_patterns:
        if matches_pattern(path, pattern, root):
            return True
    return False


def find_python_files(root: Path, exclude_patterns: list[str], max_files: int = 10000) -> dict[str, list[Path]]:
    """
    Find all Python files in the workspace, categorizing them by whether
    they would be excluded or included.
    """
    included = []
    excluded = []
    excluded_by_pattern = defaultdict(list)

    print(f"Scanning {root} for Python files...")
    print("This may take a while for large workspaces...\n")

    for py_file in root.rglob("*.py"):
        if len(included) + len(excluded) >= max_files:
            print(f"Reached limit of {max_files} files. Stopping scan.")
            break

        # Check if excluded
        excluded_flag = False
        matching_pattern = None

        for pattern in exclude_patterns:
            if matches_pattern(py_file, pattern, root):
                excluded_flag = True
                matching_pattern = pattern
                break

        if excluded_flag:
            excluded.append(py_file)
            excluded_by_pattern[matching_pattern].append(py_file)
        else:
            included.append(py_file)

    return {
        "included": included,
        "excluded": excluded,
        "excluded_by_pattern": dict(excluded_by_pattern),  # type: ignore[reportOptionalMemberAccess]
    }


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0  # pyright: ignore[reportAssignmentType]
    return f"{size_bytes:.2f} TB"


from typing import Any


def analyze_file_sizes(files: list[Path]) -> dict[str, Any]:
    """Analyze file sizes and identify large files."""
    sizes: list[int] = []
    large_files: list[tuple[Path, int]] = []
    for file_path in files:
        try:
            size = file_path.stat().st_size
            sizes.append(size)
            if size > 100 * 1024:  # Files larger than 100KB
                large_files.append((file_path, size))
        except (OSError, PermissionError):
            pass

    large_files.sort(key=lambda x: x[1], reverse=True)

    total_size = sum(sizes)
    avg_size = total_size / len(sizes) if sizes else 0

    return {
        "total_size": total_size,
        "avg_size": avg_size,
        "max_size": max(sizes) if sizes else 0,
        "large_files": large_files[:20],  # Top 20 largest files
    }


def check_recycle_bin_access(root: Path) -> bool:
    """Check if $RECYCLE.BIN is accessible and contains Python files."""
    recycle_bin = root / "$RECYCLE.BIN"
    if recycle_bin.exists():
        try:
            # Try to list contents (may fail due to permissions)
            list(recycle_bin.iterdir())
            return True
        except (PermissionError, OSError):
            return True  # Exists but not accessible
    return False


def main():
    """Main verification function."""
    workspace_root = Path("e:\\")
    config_path = workspace_root / "pyrightconfig.json"

    print("=" * 80)
    print("Basedpyright Configuration Verification")
    print("=" * 80)
    print()

    # Load configuration
    config = load_pyright_config(config_path)
    if not config:
        return

    exclude_patterns = config.get("exclude", [])
    include_patterns = config.get("include", [])
    type_checking_mode = config.get("typeCheckingMode", "basic")

    print(f"Configuration loaded from: {config_path}")
    print(f"Type checking mode: {type_checking_mode}")
    print(f"Exclude patterns: {len(exclude_patterns)}")
    if include_patterns:
        print(f"Include patterns: {len(include_patterns)}")
    print()

    # Check for $RECYCLE.BIN
    print("Checking for $RECYCLE.BIN...")
    if check_recycle_bin_access(workspace_root):
        print("  WARNING: $RECYCLE.BIN exists in workspace root")
        print("  Verify it's properly excluded in configuration")
    else:
        print("  OK: $RECYCLE.BIN not found or not accessible")
    print()

    # Find Python files
    print("Scanning for Python files...")
    results = find_python_files(workspace_root, exclude_patterns, max_files=5000)

    included = results["included"]
    excluded = results["excluded"]
    excluded_by_pattern = results["excluded_by_pattern"]

    print()
    print("=" * 80)
    print("Results Summary")
    print("=" * 80)
    print(f"Total Python files found: {len(included) + len(excluded)}")
    print(f"  Included (would be analyzed): {len(included)}")
    print(f"  Excluded (by patterns): {len(excluded)}")
    print()

    # Show exclusion breakdown
    if excluded_by_pattern:
        print("Exclusion breakdown by pattern:")
        pattern_file_pairs = excluded_by_pattern.items()  # type: ignore[reportOptionalMemberAccess]
        for pattern, files in sorted(pattern_file_pairs, key=lambda x: len(x[1]), reverse=True):
            print(f"  {pattern}: {len(files)} files")
        print()
    # Analyze included files
    included_analysis = None
    if included:
        print("Analyzing included files...")
        included_analysis = analyze_file_sizes(included)

        print(f"Total size of included files: {format_size(included_analysis['total_size'])}")
        print(f"Average file size: {format_size(included_analysis['avg_size'])}")
        print(f"Largest file: {format_size(included_analysis['max_size'])}")
        print()

        if included_analysis["large_files"]:
            print("Top 10 largest included files (potential performance issues):")
            for file_path, size in included_analysis["large_files"][:10]:
                rel_path = file_path.relative_to(workspace_root)
                print(f"  {format_size(size):>10} - {rel_path}")
            print()

        # Check for problematic directories
        print("Checking for problematic patterns in included files...")
        problematic_dirs = defaultdict(int)
        for file_path in included:
            parts = file_path.parts
            # Check for site-packages, tests, etc.
            for i, part in enumerate(parts):
                if "site-packages" in part.lower() or "test" in part.lower() or "venv" in part.lower():
                    dir_path = Path(*parts[: i + 1])
                    problematic_dirs[str(dir_path)] += 1

        if problematic_dirs:
            print("  WARNING: Found potentially problematic directories in included files:")
            for dir_path, count in sorted(problematic_dirs.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"    {dir_path}: {count} files")
        else:
            print("  OK: No obvious problematic directories found")
        print()
    else:
        print("No included files found - all files are excluded by patterns.")
        print("This may indicate exclude patterns are too broad (e.g., **/.* matches everything).")
        print()

    # Recommendations
    print("=" * 80)
    print("Recommendations")
    print("=" * 80)

    if len(included) > 1000:
        print(f"  WARNING: High file count ({len(included)} files). Consider:")
        print("     - Adding more exclude patterns")
        print("     - Using 'include' patterns to limit scope")
        print("     - Excluding test directories: **/tests/**, **/test_*.py")
        print("     - Excluding site-packages tests: **/site-packages/**/tests/**")

    if included_analysis and included_analysis.get("max_size", 0) > 500 * 1024:  # 500KB
        print("  WARNING: Large files detected. Consider excluding:")
        print("     - Test files: **/test_*.py, **/*_test.py")
        print("     - Generated files: **/generated/**, **/build/**")

    if not include_patterns and len(included) > 500:
        print("  TIP: Consider using 'include' patterns to explicitly limit scope")
        print('     Example: ["src/**", "app/**"]')

    print()
    print("=" * 80)
    print("Verification complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
