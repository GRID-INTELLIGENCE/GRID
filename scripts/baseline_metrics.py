#!/usr/bin/env python3
"""
Establish baseline metrics for basedpyright performance.
Measures file count, memory usage, and analysis times.
"""

import json
import time
from datetime import datetime
from pathlib import Path


def matches_pattern(path: Path, pattern: str, root: Path) -> bool:
    """Check if a path matches a glob pattern."""
    import fnmatch

    try:
        rel_path = path.relative_to(root)
    except ValueError:
        rel_path = path

    path_str = str(rel_path).replace("\\", "/")
    pattern_str = pattern.replace("\\", "/")

    if pattern_str == "**/.*":
        parts = path_str.split("/")
        return any(part.startswith(".") for part in parts if part)

    if "**" in pattern_str:
        if pattern_str.startswith("**/"):
            suffix = pattern_str[3:]
            if suffix:
                return fnmatch.fnmatch(path_str, f"*{suffix}") or fnmatch.fnmatch(path_str, suffix)
            else:
                return True
        elif pattern_str.endswith("/**"):
            prefix = pattern_str[:-3]
            return path_str.startswith(prefix) if prefix else True
        else:
            return fnmatch.fnmatch(path_str, pattern_str.replace("**", "*"))

    return fnmatch.fnmatch(path_str, pattern_str) or fnmatch.fnmatch(str(path), pattern_str)


def is_excluded(path: Path, exclude_patterns: list[str], root: Path) -> bool:
    """Check if a path matches any exclude pattern."""
    for pattern in exclude_patterns:
        if matches_pattern(path, pattern, root):
            return True
    return False


def count_python_files(root: Path, exclude_patterns: list[str], max_depth: int = 10) -> dict:
    """Count Python files that would be analyzed."""
    included = []
    excluded = []
    total_size = 0

    print(f"Scanning {root} for Python files...")
    start_time = time.time()

    for py_file in root.rglob("*.py"):
        if len(included) + len(excluded) >= 10000:
            break

        try:
            size = py_file.stat().st_size
            total_size += size

            if is_excluded(py_file, exclude_patterns, root):
                excluded.append(py_file)
            else:
                included.append(py_file)
        except (OSError, PermissionError):
            pass

    scan_time = time.time() - start_time

    return {
        "included_count": len(included),
        "excluded_count": len(excluded),
        "total_count": len(included) + len(excluded),
        "total_size_bytes": total_size,
        "scan_time_seconds": scan_time,
        "timestamp": datetime.now().isoformat(),
    }


def load_config_metrics(config_path: Path) -> dict:
    """Extract metrics from pyrightconfig.json."""
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

        return {
            "type_checking_mode": config.get("typeCheckingMode", "unknown"),
            "exclude_patterns_count": len(config.get("exclude", [])),
            "include_patterns_count": len(config.get("include", [])),
            "python_version": config.get("pythonVersion", "unknown"),
            "exclude_patterns": config.get("exclude", []),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0  # pyright: ignore[reportAssignmentType]
    return f"{size_bytes:.2f} TB"


def save_baseline(metrics: dict, output_path: Path):
    """Save baseline metrics to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Baseline metrics saved to: {output_path}")


def compare_baselines(current: dict, previous: dict) -> dict:
    """Compare current metrics with previous baseline."""
    if not previous:
        return {"status": "no_previous", "message": "No previous baseline found"}

    comparison = {
        "status": "comparison",
        "file_count_change": current.get("included_count", 0) - previous.get("included_count", 0),
        "file_count_change_percent": 0,
        "size_change_bytes": current.get("total_size_bytes", 0) - previous.get("total_size_bytes", 0),
        "size_change_percent": 0,
    }

    if previous.get("included_count", 0) > 0:
        comparison["file_count_change_percent"] = comparison["file_count_change"] / previous["included_count"] * 100

    if previous.get("total_size_bytes", 0) > 0:
        comparison["size_change_percent"] = comparison["size_change_bytes"] / previous["total_size_bytes"] * 100

    return comparison


def main():
    """Main function to establish baseline metrics."""
    workspace_root = Path("e:\\")
    config_path = workspace_root / "pyrightconfig.json"
    baseline_path = workspace_root / ".basedpyright" / "baseline_metrics.json"
    previous_baseline_path = workspace_root / ".basedpyright" / "baseline_metrics_previous.json"

    print("=" * 80)
    print("Basedpyright Baseline Metrics")
    print("=" * 80)
    print()

    # Load configuration
    config_metrics = load_config_metrics(config_path)
    if not config_metrics:
        print("Error: Could not load pyrightconfig.json")
        return

    exclude_patterns = config_metrics.get("exclude_patterns", [])

    print("Configuration:")
    print(f"  Type checking mode: {config_metrics.get('type_checking_mode')}")
    print(f"  Exclude patterns: {config_metrics.get('exclude_patterns_count')}")
    print(f"  Include patterns: {config_metrics.get('include_patterns_count')}")
    print(f"  Python version: {config_metrics.get('python_version')}")
    print()

    # Count files
    print("Counting Python files...")
    file_metrics = count_python_files(workspace_root, exclude_patterns)

    # Combine metrics
    baseline_metrics = {
        "timestamp": datetime.now().isoformat(),
        "workspace_root": str(workspace_root),
        "configuration": config_metrics,
        "file_metrics": file_metrics,
    }

    # Load previous baseline for comparison
    previous_baseline = {}
    if previous_baseline_path.exists():
        try:
            with open(previous_baseline_path, encoding="utf-8") as f:
                previous_baseline = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    # Save current baseline as previous if it exists
    if baseline_path.exists() and not previous_baseline:
        import shutil

        shutil.copy2(baseline_path, previous_baseline_path)

    # Save new baseline
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    save_baseline(baseline_metrics, baseline_path)

    # Display results
    print()
    print("=" * 80)
    print("Baseline Metrics Summary")
    print("=" * 80)
    print(f"Included files: {file_metrics['included_count']}")
    print(f"Excluded files: {file_metrics['excluded_count']}")
    print(f"Total files scanned: {file_metrics['total_count']}")
    print(f"Total size: {format_size(file_metrics['total_size_bytes'])}")
    print(f"Scan time: {file_metrics['scan_time_seconds']:.2f} seconds")
    print()

    # Compare with previous if available
    if previous_baseline:
        prev_file_metrics = previous_baseline.get("file_metrics", {})
        comparison = compare_baselines(file_metrics, prev_file_metrics)

        if comparison["status"] == "comparison":
            print("Comparison with previous baseline:")
            file_change = comparison["file_count_change"]
            file_change_pct = comparison["file_count_change_percent"]
            size_change = comparison["size_change_bytes"]
            size_change_pct = comparison["size_change_percent"]

            print(f"  File count change: {file_change:+d} ({file_change_pct:+.1f}%)")
            print(f"  Size change: {format_size(size_change)} ({size_change_pct:+.1f}%)")

            if file_change < 0:
                print("  IMPROVEMENT: File count decreased")
            elif file_change > 0:
                print("  WARNING: File count increased")
    else:
        print("No previous baseline found for comparison.")
        print("Run this script again after making changes to see improvements.")

    print()
    print("=" * 80)
    print("Target Metrics (from plan):")
    print("=" * 80)
    print("  File count: < 1000 project files (current: {})".format(file_metrics["included_count"]))
    print("  Memory usage: < 10GB (requires basedpyright restart to measure)")
    print("  Analysis time: < 5 minutes (requires basedpyright restart to measure)")
    print()

    if file_metrics["included_count"] > 1000:
        print("  WARNING: File count exceeds target. Consider:")
        print("    - Adding more exclude patterns")
        print("    - Using include patterns to limit scope")
    else:
        print("  OK: File count is within target range")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
