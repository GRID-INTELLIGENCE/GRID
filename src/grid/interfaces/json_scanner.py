"""JSON file scanner for finding recent metrics files across codebase."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JSONFileType(StrEnum):
    """Types of JSON files we can identify."""

    BENCHMARK_METRICS = "benchmark_metrics"
    BENCHMARK_RESULTS = "benchmark_results"
    STRESS_METRICS = "stress_metrics"
    ACTION_TRACE = "action_trace"
    UNKNOWN = "unknown"


class JSONScanner:
    """Scans for and identifies relevant JSON files."""

    def __init__(self, base_path: Path | None = None):
        """Initialize JSON scanner.

        Args:
            base_path: Base path to start scanning from (default: project root)
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent
        self.base_path = Path(base_path).resolve()

    def scan_recent_json_files(
        self,
        days: int = 7,
        patterns: list[str] | None = None,
    ) -> list[tuple[Path, JSONFileType, dict[str, Any]]]:
        """Scan for recently modified JSON files.

        Args:
            days: Number of days to look back (default: 7)
            patterns: File patterns to match (default: common metrics patterns)

        Returns:
            List of tuples (file_path, file_type, metadata)
        """
        if patterns is None:
            patterns = [
                "**/benchmark_metrics.json",
                "**/benchmark_results.json",
                "**/stress_metrics.json",
                "**/metrics/*.json",
                "grid/logs/traces/**/*.json",
            ]

        cutoff_time = datetime.now(UTC) - timedelta(days=days)
        results: list[tuple[Path, JSONFileType, dict[str, Any]]] = []

        for pattern in patterns:
            try:
                for file_path in self.base_path.glob(pattern):
                    # Skip if file is too old
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
                    if mtime < cutoff_time:
                        continue

                    # Identify file type
                    file_type = self.identify_metrics_file(file_path)

                    # Get metadata
                    metadata = self.get_file_metadata(file_path)

                    results.append((file_path, file_type, metadata))

            except Exception as e:
                logger.warning(f"Error scanning pattern {pattern}: {e}")
                continue

        # Sort by modification time (most recent first)
        results.sort(key=lambda x: x[2].get("modified_time", datetime.min.replace(tzinfo=UTC)), reverse=True)

        logger.info(f"Found {len(results)} recent JSON files")
        return results

    def identify_metrics_file(self, file_path: Path) -> JSONFileType:
        """Identify the type of metrics file.

        Args:
            file_path: Path to JSON file

        Returns:
            JSONFileType enum value
        """
        file_name = file_path.name.lower()
        file_str = str(file_path).lower()

        # Check by filename
        if "benchmark_metrics.json" in file_name:
            return JSONFileType.BENCHMARK_METRICS
        if "benchmark_results.json" in file_name:
            return JSONFileType.BENCHMARK_RESULTS
        if "stress_metrics.json" in file_name:
            return JSONFileType.STRESS_METRICS

        # Check by path (trace files)
        if "traces" in file_str and file_name.endswith(".json"):
            return JSONFileType.ACTION_TRACE

        # Try to identify by content
        try:
            with open(file_path) as f:
                data = json.load(f)

            # Check for benchmark metrics structure
            if isinstance(data, dict):
                if "bridge_transfer" in data or "sensory_processing" in data:
                    return JSONFileType.BENCHMARK_METRICS
                if "summary" in data and "latency_ms_mean" in data.get("summary", {}):
                    return JSONFileType.STRESS_METRICS
                # Check for ActionTrace structure
                if "trace_id" in data and "action_type" in data and "context" in data:
                    return JSONFileType.ACTION_TRACE

        except Exception:  # noqa: S110 intentional silent handling
            pass  # Ignore parse errors during identification

        return JSONFileType.UNKNOWN

    def get_file_metadata(self, file_path: Path) -> dict[str, Any]:
        """Get metadata for a file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with metadata (size, modified_time, etc.)
        """
        try:
            stat = file_path.stat()
            return {
                "size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                "created_time": datetime.fromtimestamp(stat.st_ctime, tz=UTC),
                "absolute_path": str(file_path.resolve()),
                "relative_path": str(file_path.relative_to(self.base_path)),
            }
        except Exception as e:
            logger.warning(f"Error getting metadata for {file_path}: {e}")
            return {
                "size": 0,
                "modified_time": datetime.now(UTC),
                "created_time": datetime.now(UTC),
                "absolute_path": str(file_path),
                "relative_path": str(file_path),
            }

    def find_specific_files(
        self,
        file_names: list[str],
        search_paths: list[str] | None = None,
    ) -> list[tuple[Path, dict[str, Any]]]:
        """Find specific JSON files by name.

        Args:
            file_names: List of file names to find
            search_paths: Paths to search in (default: data/, grid/logs/)

        Returns:
            List of tuples (file_path, metadata)
        """
        if search_paths is None:
            search_paths = ["data", "grid/logs/traces"]

        results: list[tuple[Path, dict[str, Any]]] = []

        for search_path in search_paths:
            search_dir = self.base_path / search_path
            if not search_dir.exists():
                continue

            for file_name in file_names:
                # Try exact match
                file_path = search_dir / file_name
                if file_path.exists():
                    results.append((file_path, self.get_file_metadata(file_path)))
                    continue

                # Try recursive search
                results.extend(
                    (found_file, self.get_file_metadata(found_file)) for found_file in search_dir.rglob(file_name)
                )

        return results
