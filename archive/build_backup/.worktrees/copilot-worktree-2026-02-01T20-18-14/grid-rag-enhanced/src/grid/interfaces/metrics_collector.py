"""Metrics collector for grid/interfaces/ performance data.

Extracts performance metrics from audit logs and ActionTrace records
for QuantumBridge and SensoryProcessor operations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grid.interfaces.json_parser import JSONParser
from grid.interfaces.json_scanner import JSONFileType, JSONScanner
from grid.tracing.action_trace import ActionTrace
from grid.tracing.trace_store import TraceStore

logger = logging.getLogger(__name__)


class BridgeMetrics:
    """Extracted metrics from QuantumBridge transfer operation."""

    def __init__(
        self,
        timestamp: datetime,
        trace_id: str,
        transfer_latency_ms: float,
        compressed_size: int,
        raw_size: int,
        coherence_level: float,
        entanglement_count: int,
        integrity_check: str,
        success: bool,
        source_module: str,
        metadata: dict[str, Any],
    ):
        """Initialize bridge metrics.

        Args:
            timestamp: Operation timestamp
            trace_id: Trace identifier
            transfer_latency_ms: Transfer latency in milliseconds
            compressed_size: Compressed data size
            raw_size: Raw data size
            coherence_level: Coherence level (0.0-1.0)
            entanglement_count: Number of entanglement pairs
            integrity_check: Integrity check hash
            success: Whether operation succeeded
            source_module: Source module name
            metadata: Additional metadata
        """
        self.timestamp = timestamp
        self.trace_id = trace_id
        self.transfer_latency_ms = transfer_latency_ms
        self.compressed_size = compressed_size
        self.raw_size = raw_size
        self.compression_ratio = compressed_size / raw_size if raw_size > 0 else 0.0
        self.coherence_level = coherence_level
        self.entanglement_count = entanglement_count
        self.integrity_check = integrity_check
        self.success = success
        self.source_module = source_module
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "transfer_latency_ms": self.transfer_latency_ms,
            "compressed_size": self.compressed_size,
            "raw_size": self.raw_size,
            "compression_ratio": self.compression_ratio,
            "coherence_level": self.coherence_level,
            "entanglement_count": self.entanglement_count,
            "integrity_check": self.integrity_check,
            "success": self.success,
            "source_module": self.source_module,
            "metadata": self.metadata,
        }


class SensoryMetrics:
    """Extracted metrics from SensoryProcessor operation."""

    def __init__(
        self,
        timestamp: datetime,
        trace_id: str,
        modality: str,
        duration_ms: float,
        coherence: float,
        raw_size: int,
        source: str,
        success: bool,
        error_message: str | None,
        metadata: dict[str, Any],
    ):
        """Initialize sensory metrics.

        Args:
            timestamp: Operation timestamp
            trace_id: Trace identifier
            modality: Input modality (text/visual/audio/structured)
            duration_ms: Processing duration in milliseconds
            coherence: Coherence factor (0.0-1.0)
            raw_size: Input data size
            source: Source identifier
            success: Whether operation succeeded
            error_message: Error message if failed
            metadata: Additional metadata
        """
        self.timestamp = timestamp
        self.trace_id = trace_id
        self.modality = modality
        self.duration_ms = duration_ms
        self.coherence = coherence
        self.raw_size = raw_size
        self.source = source
        self.success = success
        self.error_message = error_message
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "modality": self.modality,
            "duration_ms": self.duration_ms,
            "coherence": self.coherence,
            "raw_size": self.raw_size,
            "source": self.source,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class MetricsCollector:
    """Collects performance metrics from audit logs and traces."""

    def __init__(
        self,
        session: AsyncSession | None = None,
        trace_store: TraceStore | None = None,
        json_scanner: JSONScanner | None = None,
        json_parser: JSONParser | None = None,
    ):
        """Initialize metrics collector.

        Args:
            session: Database session for querying audit logs
            trace_store: Trace store for querying ActionTrace records
            json_scanner: JSON file scanner (default: new instance)
            json_parser: JSON file parser (default: new instance)
        """
        self.session = session
        self.trace_store = trace_store or TraceStore()
        self.json_scanner = json_scanner or JSONScanner()
        self.json_parser = json_parser or JSONParser()

    def _is_bridge_action(self, action_type: str, resource_type: str, details: dict[str, Any]) -> bool:
        """Check if action is related to QuantumBridge.

        Args:
            action_type: Action type string
            resource_type: Resource type string
            details: Action details dictionary

        Returns:
            True if related to QuantumBridge
        """
        # Check various indicators of bridge operations
        bridge_indicators = [
            "bridge",
            "transfer",
            "quantum",
            "grid.interfaces.bridge",
        ]

        check_strings = [
            action_type.lower(),
            resource_type.lower(),
            str(details.get("action_name", "")).lower(),
            str(details.get("operation", "")).lower(),
        ]

        return any(indicator in check_str for check_str in check_strings for indicator in bridge_indicators)

    def _is_sensory_action(self, action_type: str, resource_type: str, details: dict[str, Any]) -> bool:
        """Check if action is related to SensoryProcessor.

        Args:
            action_type: Action type string
            resource_type: Resource type string
            details: Action details dictionary

        Returns:
            True if related to SensoryProcessor
        """
        # Check various indicators of sensory operations
        sensory_indicators = [
            "sensory",
            "process",
            "input",
            "modality",
            "grid.interfaces.sensory",
        ]

        check_strings = [
            action_type.lower(),
            resource_type.lower(),
            str(details.get("action_name", "")).lower(),
            str(details.get("operation", "")).lower(),
        ]

        return any(indicator in check_str for check_str in check_strings for indicator in sensory_indicators)

    def _extract_bridge_metrics_from_trace(self, trace: ActionTrace) -> BridgeMetrics | None:
        """Extract bridge metrics from ActionTrace.

        Args:
            trace: Action trace record

        Returns:
            BridgeMetrics if successful, None otherwise
        """
        try:
            # Check if this is a bridge operation
            if "bridge" not in trace.action_type.lower() and "transfer" not in trace.action_type.lower():
                if "bridge" not in trace.action_name.lower() and "transfer" not in trace.action_name.lower():
                    return None

            # Extract output data (should contain bridge transfer result)
            output_data = trace.output_data or {}
            if not output_data:
                # Check input_data for transfer call parameters
                input_data = trace.input_data or {}
                if not input_data:
                    return None

            # Try to extract from output_data first (actual transfer result)
            if output_data:
                transfer_latency_ms = float(output_data.get("transfer_latency_ms", 0.0))
                if transfer_latency_ms == 0.0:
                    # Check quantum_state for bridge_latency_ms
                    quantum_state = input_data.get("quantum_state", {})
                    if isinstance(quantum_state, dict):
                        transfer_latency_ms = float(quantum_state.get("bridge_latency_ms", 0.0))

                compressed_size = int(output_data.get("compressed_size", 0))
                raw_size = int(output_data.get("raw_size", 0))
                coherence_level = float(output_data.get("coherence_level", 0.5))
                entanglement_count = int(output_data.get("entanglement_count", 0))
                integrity_check = str(output_data.get("integrity_check", ""))
                signature = str(output_data.get("signature", ""))
            else:
                # Fallback to defaults or metadata
                transfer_latency_ms = 0.0
                compressed_size = 0
                raw_size = 0
                coherence_level = trace.metadata.get("coherence", 0.5) if trace.metadata else 0.5
                entanglement_count = 0
                integrity_check = ""
                signature = ""

            # Get duration from trace if available
            if trace.duration_ms:
                transfer_latency_ms = trace.duration_ms

            # Extract source module
            source_module = trace.context.source_module if trace.context else "unknown"

            return BridgeMetrics(
                timestamp=trace.context.timestamp if trace.context else datetime.now(UTC),
                trace_id=trace.trace_id,
                transfer_latency_ms=transfer_latency_ms,
                compressed_size=compressed_size,
                raw_size=raw_size,
                coherence_level=coherence_level,
                entanglement_count=entanglement_count,
                integrity_check=integrity_check or signature,
                success=trace.success,
                source_module=source_module,
                metadata=trace.metadata or {},
            )
        except Exception as e:
            logger.warning(f"Failed to extract bridge metrics from trace {trace.trace_id}: {e}")
            return None

    def _extract_sensory_metrics_from_trace(self, trace: ActionTrace) -> SensoryMetrics | None:
        """Extract sensory metrics from ActionTrace.

        Args:
            trace: Action trace record

        Returns:
            SensoryMetrics if successful, None otherwise
        """
        try:
            # Check if this is a sensory operation
            if "sensory" not in trace.action_type.lower() and "process" not in trace.action_type.lower():
                if "sensory" not in trace.action_name.lower():
                    # Check sensory_inputs field
                    if not trace.sensory_inputs:
                        return None

            # Extract from output_data (should contain processed result)
            output_data = trace.output_data or {}
            input_data = trace.input_data or {}

            # Extract modality
            modality = "text"  # default
            if output_data:
                modality = str(output_data.get("modality", "text"))
            elif input_data:
                modality = str(input_data.get("modality", "text"))
            elif trace.sensory_inputs:
                # Get first sensory input modality
                first_input = next(iter(trace.sensory_inputs.values())) if trace.sensory_inputs else {}
                if isinstance(first_input, dict):
                    modality = str(first_input.get("modality", "text"))

            # Extract duration
            duration_ms = trace.duration_ms or 0.0
            if duration_ms == 0.0 and output_data:
                duration_ms = float(output_data.get("duration_ms", 0.0))

            # Extract coherence
            coherence = 0.5  # default
            if output_data:
                coherence = float(output_data.get("coherence", 0.5))
            elif trace.metadata:
                coherence = float(trace.metadata.get("coherence", 0.5))

            # Extract raw_size
            raw_size = 0
            if output_data:
                raw_size = int(output_data.get("raw_size", 0))
            elif input_data:
                raw_size = len(str(input_data))

            # Extract source
            source = "unknown"
            if input_data:
                source = str(input_data.get("source", "unknown"))
            elif trace.context:
                source = trace.context.source_module or "unknown"

            # Extract error message
            error_message = trace.error if not trace.success else None

            return SensoryMetrics(
                timestamp=trace.context.timestamp if trace.context else datetime.now(UTC),
                trace_id=trace.trace_id,
                modality=modality,
                duration_ms=duration_ms,
                coherence=coherence,
                raw_size=raw_size,
                source=source,
                success=trace.success,
                error_message=error_message,
                metadata=trace.metadata or {},
            )
        except Exception as e:
            logger.warning(f"Failed to extract sensory metrics from trace {trace.trace_id}: {e}")
            return None

    async def collect_from_audit_logs(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[BridgeMetrics], list[SensoryMetrics]]:
        """Collect metrics from audit logs.

        Args:
            start_time: Start time for query (default: 7 days ago)
            end_time: End time for query (default: now)

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        if not self.session:
            logger.warning("No database session provided, skipping audit log collection")
            return [], []

        if start_time is None:
            start_time = datetime.now(UTC) - timedelta(days=7)
        if end_time is None:
            end_time = datetime.now(UTC)

        try:
            from application.mothership.db.models_audit import AuditLogRow

            # Query audit logs related to interfaces
            stmt = (
                select(AuditLogRow)
                .where(
                    AuditLogRow.created_at >= start_time,
                    AuditLogRow.created_at <= end_time,
                )
                .where(
                    (AuditLogRow.resource_type.like("grid.interfaces%"))
                    | (AuditLogRow.action.like("%bridge%"))
                    | (AuditLogRow.action.like("%sensory%"))
                )
            )

            result = await self.session.execute(stmt)
            audit_rows = result.scalars().all()

            bridge_metrics = []
            sensory_metrics = []

            for row in audit_rows:
                details = row.details or {}

                # Try to extract bridge metrics
                if self._is_bridge_action(row.action, row.resource_type, details):
                    try:
                        # Extract from details
                        transfer_latency_ms = float(details.get("transfer_latency_ms", 0.0))
                        compressed_size = int(details.get("compressed_size", 0))
                        raw_size = int(details.get("raw_size", 0))
                        coherence_level = float(details.get("coherence_level", 0.5))
                        entanglement_count = int(details.get("entanglement_count", 0))
                        integrity_check = str(details.get("integrity_check", ""))

                        bridge_metrics.append(
                            BridgeMetrics(
                                timestamp=row.created_at,
                                trace_id=row.request_id or f"audit_{row.id}",
                                transfer_latency_ms=transfer_latency_ms,
                                compressed_size=compressed_size,
                                raw_size=raw_size,
                                coherence_level=coherence_level,
                                entanglement_count=entanglement_count,
                                integrity_check=integrity_check,
                                success=details.get("success", True),
                                source_module=row.resource_type,
                                metadata=details,
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Failed to extract bridge metrics from audit log {row.id}: {e}")

                # Try to extract sensory metrics
                if self._is_sensory_action(row.action, row.resource_type, details):
                    try:
                        modality = str(details.get("modality", "text"))
                        duration_ms = float(details.get("duration_ms", 0.0))
                        coherence = float(details.get("coherence", 0.5))
                        raw_size = int(details.get("raw_size", 0))

                        sensory_metrics.append(
                            SensoryMetrics(
                                timestamp=row.created_at,
                                trace_id=row.request_id or f"audit_{row.id}",
                                modality=modality,
                                duration_ms=duration_ms,
                                coherence=coherence,
                                raw_size=raw_size,
                                source=str(details.get("source", "unknown")),
                                success=details.get("success", True),
                                error_message=details.get("error_message"),
                                metadata=details,
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Failed to extract sensory metrics from audit log {row.id}: {e}")

            logger.info(
                f"Collected {len(bridge_metrics)} bridge metrics and {len(sensory_metrics)} sensory metrics from audit logs"
            )
            return bridge_metrics, sensory_metrics

        except Exception as e:
            logger.error(f"Error collecting metrics from audit logs: {e}")
            return [], []

    def collect_from_traces(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> tuple[list[BridgeMetrics], list[SensoryMetrics]]:
        """Collect metrics from ActionTrace records.

        Args:
            start_time: Start time for query (default: 7 days ago)
            end_time: End time for query (default: now)
            limit: Maximum number of traces to process

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        if start_time is None:
            start_time = datetime.now(UTC) - timedelta(days=7)
        if end_time is None:
            end_time = datetime.now(UTC)

        try:
            # Query traces
            traces = self.trace_store.query_traces(
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )

            # Filter for interfaces-related traces
            interfaces_traces = [
                t
                for t in traces
                if "interfaces" in (t.context.source_module or "").lower()
                or "bridge" in t.action_type.lower()
                or "sensory" in t.action_type.lower()
            ]

            bridge_metrics = []
            sensory_metrics = []

            for trace in interfaces_traces:
                # Try bridge metrics
                bridge_metric = self._extract_bridge_metrics_from_trace(trace)
                if bridge_metric:
                    bridge_metrics.append(bridge_metric)

                # Try sensory metrics
                sensory_metric = self._extract_sensory_metrics_from_trace(trace)
                if sensory_metric:
                    sensory_metrics.append(sensory_metric)

            logger.info(
                f"Collected {len(bridge_metrics)} bridge metrics and {len(sensory_metrics)} sensory metrics from traces"
            )
            return bridge_metrics, sensory_metrics

        except Exception as e:
            logger.error(f"Error collecting metrics from traces: {e}")
            return [], []

    async def collect_all(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        trace_limit: int = 1000,
    ) -> tuple[list[BridgeMetrics], list[SensoryMetrics]]:
        """Collect metrics from both audit logs and traces.

        Args:
            start_time: Start time for query (default: 7 days ago)
            end_time: End time for query (default: now)
            trace_limit: Maximum number of traces to process

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        # Collect from both sources
        audit_bridge, audit_sensory = await self.collect_from_audit_logs(start_time, end_time)
        trace_bridge, trace_sensory = self.collect_from_traces(start_time, end_time, trace_limit)

        # Combine and deduplicate by trace_id
        bridge_map: dict[str, BridgeMetrics] = {}
        for m in audit_bridge + trace_bridge:
            bridge_map[m.trace_id] = m

        sensory_map: dict[str, SensoryMetrics] = {}
        for m in audit_sensory + trace_sensory:
            sensory_map[m.trace_id] = m

        return list(bridge_map.values()), list(sensory_map.values())

    def collect_from_json_files(
        self,
        json_files: list[Path] | None = None,
        scan_days: int = 7,
    ) -> tuple[list[BridgeMetrics], list[SensoryMetrics]]:
        """Collect metrics from JSON files.

        Args:
            json_files: Optional list of specific JSON files to process
            scan_days: Number of days to scan back if json_files not provided (default: 7)

        Returns:
            Tuple of (bridge_metrics_list, sensory_metrics_list)
        """
        bridge_metrics = []
        sensory_metrics = []

        # If no files provided, scan for recent files
        if json_files is None:
            logger.info(f"Scanning for recent JSON files (last {scan_days} days)")
            scanned_files = self.json_scanner.scan_recent_json_files(days=scan_days)
            json_files = [file_path for file_path, _, _ in scanned_files]

        logger.info(f"Processing {len(json_files)} JSON files")

        for file_path in json_files:
            try:
                # Identify file type
                file_type = self.json_scanner.identify_metrics_file(file_path)

                # Skip unknown files if we can't identify them
                if file_type == JSONFileType.UNKNOWN:
                    logger.debug(f"Skipping unknown file type: {file_path}")
                    continue

                # Parse file
                file_bridge, file_sensory = self.json_parser.extract_metrics_from_json(file_path, file_type)

                bridge_metrics.extend(file_bridge)
                sensory_metrics.extend(file_sensory)

            except Exception as e:
                logger.warning(f"Failed to process JSON file {file_path}: {e}", exc_info=True)
                continue

        # Deduplicate by trace_id
        bridge_map: dict[str, BridgeMetrics] = {}
        for m in bridge_metrics:
            bridge_map[m.trace_id] = m

        sensory_map: dict[str, SensoryMetrics] = {}
        for m in sensory_metrics:
            sensory_map[m.trace_id] = m

        logger.info(
            f"Collected {len(bridge_map)} unique bridge metrics and {len(sensory_map)} unique sensory metrics from JSON files"
        )
        return list(bridge_map.values()), list(sensory_map.values())
