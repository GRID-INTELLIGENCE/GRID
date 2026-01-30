"""JSON metrics parser for extracting BridgeMetrics and SensoryMetrics from JSON files."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from grid.interfaces.json_scanner import JSONFileType
from grid.tracing.action_trace import ActionTrace

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class JSONParser:
    """Parses JSON files and extracts metrics data."""

    def __init__(self):
        """Initialize JSON parser."""
        pass

    def extract_metrics_from_json(
        self,
        file_path: Path,
        file_type: JSONFileType,
    ) -> tuple[list[Any], list[Any]]:
        """Extract metrics from a JSON file.

        Args:
            file_path: Path to JSON file
            file_type: Type of JSON file

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        try:
            with open(file_path) as f:
                json_data = json.load(f)

            if file_type == JSONFileType.BENCHMARK_METRICS:
                return self.parse_benchmark_metrics(json_data, file_path)
            elif file_type == JSONFileType.BENCHMARK_RESULTS:
                return self.parse_benchmark_results(json_data, file_path)
            elif file_type == JSONFileType.STRESS_METRICS:
                return self.parse_stress_metrics(json_data, file_path)
            elif file_type == JSONFileType.ACTION_TRACE:
                return self.parse_trace_file(json_data, file_path)
            else:
                # Try generic parsing
                return self.parse_generic_json(json_data, file_path)

        except Exception as e:
            logger.error(f"Error parsing JSON file {file_path}: {e}", exc_info=True)
            return [], []

    def parse_benchmark_metrics(
        self,
        json_data: dict[str, Any],
        file_path: Path,
    ) -> tuple[list[Any], list[Any]]:
        """Parse benchmark_metrics.json file.

        Args:
            json_data: Parsed JSON data
            file_path: Path to JSON file

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        # Import here to avoid circular import
        from grid.interfaces.metrics_collector import BridgeMetrics, SensoryMetrics

        bridge_metrics = []
        sensory_metrics = []

        # Get file modification time for timestamp
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
        except Exception:
            mtime = datetime.now(UTC)

        # Extract bridge_transfer metrics
        if "bridge_transfer" in json_data:
            bridge_data = json_data["bridge_transfer"]
            trace_id = f"benchmark_bridge_{uuid4().hex[:8]}"

            bridge_metrics.append(
                BridgeMetrics(
                    timestamp=mtime,
                    trace_id=trace_id,
                    transfer_latency_ms=float(bridge_data.get("mean_ms", 0.0)),
                    compressed_size=0,  # Not available in benchmark data
                    raw_size=0,  # Not available in benchmark data
                    coherence_level=0.5,  # Default
                    entanglement_count=0,  # Not available
                    integrity_check="",
                    success=True,
                    source_module="benchmark_metrics.json",
                    metadata={
                        "source_file": str(file_path),
                        "count": bridge_data.get("count", 0),
                        "median_ms": bridge_data.get("median_ms", 0.0),
                        "p95_ms": bridge_data.get("p95_ms", 0.0),
                        "p99_ms": bridge_data.get("p99_ms", 0.0),
                        "min_ms": bridge_data.get("min_ms", 0.0),
                        "max_ms": bridge_data.get("max_ms", 0.0),
                    },
                )
            )

        # Extract sensory_processing metrics
        if "sensory_processing" in json_data:
            sensory_data = json_data["sensory_processing"]
            trace_id = f"benchmark_sensory_{uuid4().hex[:8]}"

            sensory_metrics.append(
                SensoryMetrics(
                    timestamp=mtime,
                    trace_id=trace_id,
                    modality="text",  # Default, not specified in benchmark
                    duration_ms=float(sensory_data.get("mean_ms", 0.0)),
                    coherence=0.5,  # Default
                    raw_size=0,  # Not available
                    source="benchmark_metrics.json",
                    success=True,
                    error_message=None,
                    metadata={
                        "source_file": str(file_path),
                        "count": sensory_data.get("count", 0),
                        "median_ms": sensory_data.get("median_ms", 0.0),
                        "p95_ms": sensory_data.get("p95_ms", 0.0),
                        "p99_ms": sensory_data.get("p99_ms", 0.0),
                        "min_ms": sensory_data.get("min_ms", 0.0),
                        "max_ms": sensory_data.get("max_ms", 0.0),
                    },
                )
            )

        logger.info(
            f"Parsed benchmark_metrics.json: {len(bridge_metrics)} bridge, {len(sensory_metrics)} sensory metrics"
        )
        return bridge_metrics, sensory_metrics

    def parse_benchmark_results(
        self,
        json_data: dict[str, Any],
        file_path: Path,
    ) -> tuple[list[Any], list[Any]]:
        """Parse benchmark_results.json file.

        Args:
            json_data: Parsed JSON data
            file_path: Path to JSON file

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        # Import here to avoid circular import
        from grid.interfaces.metrics_collector import BridgeMetrics, SensoryMetrics

        # benchmark_results.json has a "results" wrapper
        results = json_data.get("results", json_data)

        # Get file modification time
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
        except Exception:
            mtime = datetime.now(UTC)

        bridge_metrics = []
        sensory_metrics = []

        # Extract bridge_transfer from results
        if "bridge_transfer" in results:
            bridge_data = results["bridge_transfer"]
            trace_id = f"benchmark_results_bridge_{uuid4().hex[:8]}"

            bridge_metrics.append(
                BridgeMetrics(
                    timestamp=mtime,
                    trace_id=trace_id,
                    transfer_latency_ms=float(bridge_data.get("mean_ms", 0.0)),
                    compressed_size=0,
                    raw_size=0,
                    coherence_level=0.5,
                    entanglement_count=0,
                    integrity_check="",
                    success=True,
                    source_module="benchmark_results.json",
                    metadata={
                        "source_file": str(file_path),
                        "count": bridge_data.get("count", 0),
                        "median_ms": bridge_data.get("median_ms", 0.0),
                        "p95_ms": bridge_data.get("p95_ms", 0.0),
                        "p99_ms": bridge_data.get("p99_ms", 0.0),
                    },
                )
            )

        # Extract sensory_processing from results
        if "sensory_processing" in results:
            sensory_data = results["sensory_processing"]
            trace_id = f"benchmark_results_sensory_{uuid4().hex[:8]}"

            sensory_metrics.append(
                SensoryMetrics(
                    timestamp=mtime,
                    trace_id=trace_id,
                    modality="text",
                    duration_ms=float(sensory_data.get("mean_ms", 0.0)),
                    coherence=0.5,
                    raw_size=0,
                    source="benchmark_results.json",
                    success=True,
                    error_message=None,
                    metadata={
                        "source_file": str(file_path),
                        "count": sensory_data.get("count", 0),
                        "median_ms": sensory_data.get("median_ms", 0.0),
                        "p95_ms": sensory_data.get("p95_ms", 0.0),
                        "p99_ms": sensory_data.get("p99_ms", 0.0),
                    },
                )
            )

        logger.info(
            f"Parsed benchmark_results.json: {len(bridge_metrics)} bridge, {len(sensory_metrics)} sensory metrics"
        )
        return bridge_metrics, sensory_metrics

    def parse_stress_metrics(
        self,
        json_data: dict[str, Any],
        file_path: Path,
    ) -> tuple[list[Any], list[Any]]:
        """Parse stress_metrics.json file.

        Args:
            json_data: Parsed JSON data
            file_path: Path to JSON file

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        # Import here to avoid circular import
        from grid.interfaces.metrics_collector import BridgeMetrics

        bridge_metrics = []

        # Get file modification time
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
        except Exception:
            mtime = datetime.now(UTC)

        # Extract summary metrics
        summary = json_data.get("summary", {})
        if summary:
            trace_id = f"stress_{uuid4().hex[:8]}"

            # Use mean latency as transfer latency
            latency_ms = float(summary.get("latency_ms_mean", 0.0))

            bridge_metrics.append(
                BridgeMetrics(
                    timestamp=mtime,
                    trace_id=trace_id,
                    transfer_latency_ms=latency_ms,
                    compressed_size=0,
                    raw_size=0,
                    coherence_level=0.5,
                    entanglement_count=0,
                    integrity_check="",
                    success=True,
                    source_module="stress_metrics.json",
                    metadata={
                        "source_file": str(file_path),
                        "latency_ms_p95": summary.get("latency_ms_p95", 0.0),
                        "latency_ms_p99": summary.get("latency_ms_p99", 0.0),
                        "wall_clock_ms": summary.get("wall_clock_ms", 0.0),
                        "concurrency": summary.get("concurrency", 0),
                        "repeats_per_worker": summary.get("repeats_per_worker", 0),
                        "calls": summary.get("calls", 0),
                        "mem_rss_mean": summary.get("mem_rss_mean", 0.0),
                        "mem_rss_max": summary.get("mem_rss_max", 0.0),
                    },
                )
            )

        logger.info(f"Parsed stress_metrics.json: {len(bridge_metrics)} bridge metrics")
        return bridge_metrics, []

    def parse_trace_file(
        self,
        json_data: dict[str, Any],
        file_path: Path,
    ) -> tuple[list[Any], list[Any]]:
        """Parse ActionTrace JSON file.

        Args:
            json_data: Parsed JSON data
            file_path: Path to JSON file

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        try:
            # Use existing ActionTrace model to parse
            trace = ActionTrace(**json_data)

            # Use existing extraction methods from MetricsCollector
            # We'll need to call these methods, so we create a temporary collector
            from grid.interfaces.metrics_collector import MetricsCollector

            collector = MetricsCollector()

            bridge_metrics = []
            sensory_metrics = []

            # Try bridge extraction
            bridge_metric = collector._extract_bridge_metrics_from_trace(trace)
            if bridge_metric:
                bridge_metrics.append(bridge_metric)

            # Try sensory extraction
            sensory_metric = collector._extract_sensory_metrics_from_trace(trace)
            if sensory_metric:
                sensory_metrics.append(sensory_metric)

            logger.info(
                f"Parsed trace file {file_path.name}: {len(bridge_metrics)} bridge, {len(sensory_metrics)} sensory"
            )
            return bridge_metrics, sensory_metrics

        except Exception as e:
            logger.warning(f"Failed to parse trace file {file_path}: {e}")
            return [], []

    def parse_generic_json(
        self,
        json_data: dict[str, Any],
        file_path: Path,
    ) -> tuple[list[Any], list[Any]]:
        """Parse generic JSON file by pattern matching.

        Args:
            json_data: Parsed JSON data
            file_path: Path to JSON file

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        # Import here to avoid circular import
        from grid.interfaces.metrics_collector import BridgeMetrics, SensoryMetrics

        bridge_metrics = []
        sensory_metrics = []

        # Get file modification time
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
        except Exception:
            mtime = datetime.now(UTC)

        # Pattern match for common metric fields
        def find_metrics_recursive(data: Any, path: str = "") -> None:
            """Recursively search for metric-like structures."""
            if isinstance(data, dict):
                # Check for latency/duration fields
                latency_keys = ["latency_ms", "duration_ms", "mean_ms", "avg_latency_ms"]
                for key in latency_keys:
                    if key in data and isinstance(data[key], (int, float)):
                        trace_id = f"generic_{uuid4().hex[:8]}"
                        latency = float(data[key])

                        # Determine if bridge or sensory based on context
                        if "bridge" in path.lower() or "transfer" in path.lower():
                            bridge_metrics.append(
                                BridgeMetrics(
                                    timestamp=mtime,
                                    trace_id=trace_id,
                                    transfer_latency_ms=latency,
                                    compressed_size=0,
                                    raw_size=0,
                                    coherence_level=0.5,
                                    entanglement_count=0,
                                    integrity_check="",
                                    success=True,
                                    source_module=str(file_path),
                                    metadata={"source_file": str(file_path), "path": path, "raw_data": data},
                                )
                            )
                        elif "sensory" in path.lower() or "process" in path.lower():
                            sensory_metrics.append(
                                SensoryMetrics(
                                    timestamp=mtime,
                                    trace_id=trace_id,
                                    modality="text",
                                    duration_ms=latency,
                                    coherence=0.5,
                                    raw_size=0,
                                    source=str(file_path),
                                    success=True,
                                    error_message=None,
                                    metadata={"source_file": str(file_path), "path": path, "raw_data": data},
                                )
                            )

                # Recursively search nested structures
                for key, value in data.items():
                    find_metrics_recursive(value, f"{path}.{key}" if path else key)

            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    find_metrics_recursive(item, f"{path}[{idx}]")

        find_metrics_recursive(json_data)

        if bridge_metrics or sensory_metrics:
            logger.info(
                f"Parsed generic JSON {file_path.name}: {len(bridge_metrics)} bridge, {len(sensory_metrics)} sensory metrics"
            )

        return bridge_metrics, sensory_metrics
