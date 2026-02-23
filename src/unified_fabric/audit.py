"""
Unified Fabric - Distributed Audit Logger
==========================================
Cross-system audit logging for compliance and observability.

Key Features:
- Writes to centralized log directory
- Includes project-id, request-id, correlation-id
- JSON-L format for easy parsing
- Async non-blocking writes
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditEventType(StrEnum):
    """Types of audit events"""

    REQUEST_RECEIVED = "request_received"
    REQUEST_COMPLETED = "request_completed"
    SAFETY_CHECK = "safety_check"
    SAFETY_VIOLATION = "safety_violation"
    RATE_LIMIT = "rate_limit"
    PORTFOLIO_ACTION = "portfolio_action"
    TRADING_SIGNAL = "trading_signal"
    NAVIGATION_REQUEST = "navigation_request"
    RAG_QUERY = "rag_query"
    ERROR = "error"
    SYSTEM_EVENT = "system_event"


@dataclass
class AuditEntry:
    """Single audit log entry"""

    event_type: str
    project_id: str
    domain: str
    action: str
    status: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    user_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class DistributedAuditLogger:
    """
    Centralized audit logger for cross-system observability.

    Writes audit entries to:
    - Primary: E:/grid/logs/unified_fabric/
    - Async buffered writes for performance
    """

    def __init__(self, log_dir: Path | None = None, buffer_size: int = 50, flush_interval_sec: float = 5.0):
        self.log_dir = log_dir or Path("E:/grid/logs/unified_fabric")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.buffer_size = buffer_size
        self.flush_interval = flush_interval_sec
        self._buffer: list[AuditEntry] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None
        self._running = False

        logger.info(f"DistributedAuditLogger initialized at {self.log_dir}")

    async def start(self):
        """Start the background flush worker"""
        if self._running:
            return
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_worker())
        logger.info("Audit logger started")

    async def stop(self):
        """Stop and flush remaining entries"""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush_buffer()
        logger.info("Audit logger stopped")

    async def log(
        self,
        event_type: AuditEventType,
        project_id: str,
        domain: str,
        action: str,
        status: str = "success",
        user_id: str | None = None,
        correlation_id: str | None = None,
        details: dict | None = None,
        duration_ms: float | None = None,
    ) -> str:
        """
        Log an audit entry.

        Returns:
            request_id for correlation
        """
        entry = AuditEntry(
            event_type=event_type.value,
            project_id=project_id,
            domain=domain,
            action=action,
            status=status,
            user_id=user_id,
            correlation_id=correlation_id,
            details=details or {},
            duration_ms=duration_ms,
        )

        async with self._lock:
            self._buffer.append(entry)

            if len(self._buffer) >= self.buffer_size:
                await self._flush_buffer()

        return entry.request_id

    async def log_safety_check(
        self,
        decision: str,
        threat_level: str,
        violation_count: int,
        domain: str,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> str:
        """Log a safety check event"""
        return await self.log(
            event_type=AuditEventType.SAFETY_CHECK,
            project_id="unified_fabric",
            domain=domain,
            action="safety_validation",
            status=decision,
            user_id=user_id,
            correlation_id=correlation_id,
            details={"threat_level": threat_level, "violation_count": violation_count},
        )

    async def log_portfolio_action(
        self, action: str, portfolio_id: str, user_id: str, success: bool, details: dict | None = None
    ) -> str:
        """Log a portfolio action"""
        return await self.log(
            event_type=AuditEventType.PORTFOLIO_ACTION,
            project_id="coinbase",
            domain="coinbase",
            action=action,
            status="success" if success else "failure",
            user_id=user_id,
            details={"portfolio_id": portfolio_id, **(details or {})},
        )

    async def log_navigation(
        self, nav_type: str, origin: str, destination: str, user_id: str, duration_ms: float
    ) -> str:
        """Log a GRID navigation request"""
        return await self.log(
            event_type=AuditEventType.NAVIGATION_REQUEST,
            project_id="grid",
            domain="grid",
            action=nav_type,
            status="success",
            user_id=user_id,
            duration_ms=duration_ms,
            details={"origin": origin, "destination": destination},
        )

    async def log_error(
        self, error_type: str, error_message: str, project_id: str, domain: str, user_id: str | None = None
    ) -> str:
        """Log an error event"""
        return await self.log(
            event_type=AuditEventType.ERROR,
            project_id=project_id,
            domain=domain,
            action="error",
            status="failure",
            user_id=user_id,
            details={"error_type": error_type, "message": error_message},
        )

    async def _flush_buffer(self):
        """Flush buffer to disk"""
        if not self._buffer:
            return

        entries = self._buffer.copy()
        self._buffer.clear()

        # Write to daily log file
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        log_file = self.log_dir / f"audit_{date_str}.jsonl"

        try:
            import aiofiles

            async with aiofiles.open(log_file, "a", encoding="utf-8") as f:
                for entry in entries:
                    await f.write(entry.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to flush audit log: {e}")
            # Re-add entries to buffer
            self._buffer.extend(entries)

    async def _flush_worker(self):
        """Background worker to periodically flush buffer"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                async with self._lock:
                    await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Flush worker error: {e}")

    async def get_recent_entries(
        self, limit: int = 100, event_type: AuditEventType | None = None, domain: str | None = None
    ) -> list[AuditEntry]:
        """Get recent audit entries with optional filtering"""
        entries = []

        # Read from today's log file
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        log_file = self.log_dir / f"audit_{date_str}.jsonl"

        if not await asyncio.to_thread(log_file.exists):
            return entries

        try:
            import aiofiles

            async with aiofiles.open(log_file, encoding="utf-8") as f:
                async for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry = AuditEntry(**data)

                        # Apply filters
                        if event_type and entry.event_type != event_type.value:
                            continue
                        if domain and entry.domain != domain:
                            continue

                        entries.append(entry)
                    except (json.JSONDecodeError, TypeError):
                        continue
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")

        # Return most recent entries
        return entries[-limit:]


# Singleton instance
_audit_logger: DistributedAuditLogger | None = None


def get_audit_logger() -> DistributedAuditLogger:
    """Get the singleton audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = DistributedAuditLogger()
    return _audit_logger


async def init_audit_logger() -> DistributedAuditLogger:
    """Initialize and start the audit logger"""
    audit_logger = get_audit_logger()
    await audit_logger.start()
    return audit_logger
