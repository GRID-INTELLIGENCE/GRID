"""
OVERWATCH audit logging
"""
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class AuditEventType(Enum):
    """Types of audit events"""
    DATA_INPUT = "data_input"
    DATA_PROCESSING = "data_processing"
    DATA_ACCESS = "data_access"
    DATA_DELETION = "data_deletion"
    MODEL_INFERENCE = "model_inference"
    PII_DETECTED = "pii_detected"
    PII_SANITIZED = "pii_sanitized"
    SAFETY_VIOLATION = "safety_violation"
    REPORT_GENERATED = "report_generated"
    CONFIG_CHANGE = "config_change"
    ERROR_OCCURRED = "error_occurred"
    MORPH_STATE_CHANGE = "morph_state_change"
    GUARDIAN_VIOLATION = "guardian_violation"
    ADSR_PHASE_TRANSITION = "adsr_phase_transition"

@dataclass
class AuditEvent:
    """Single audit event record"""
    event_id: str
    timestamp: str
    event_type: str
    user_id: str | None
    session_id: str
    resource_id: str | None
    action: str
    status: str  # 'success', 'failure', 'blocked'
    details: dict[str, Any]
    ip_address: str | None = None
    user_agent: str | None = None

class OverwatchAuditLogger:
    """OVERWATCH audit logging (extends Wellness Studio AuditLogger)"""
    def __init__(self, log_dir: Path | None = None):
        self.log_dir = log_dir or Path("logs/audit")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = str(uuid.uuid4())[:12]
        self.event_buffer: list[AuditEvent] = []
        self.buffer_size = 100

    def log_event(self, event_type: AuditEventType, action: str, status: str = "success", user_id: str | None = None, resource_id: str | None = None, details: dict | None = None, ip_address: str | None = None, user_agent: str | None = None) -> AuditEvent:
        """Log an audit event"""
        event = AuditEvent(event_id=f"evt_{uuid.uuid4().hex[:16]}", timestamp=datetime.now().isoformat(), event_type=event_type.value, user_id=user_id, session_id=self.session_id, resource_id=resource_id, action=action, status=status, details=details or {}, ip_address=ip_address, user_agent=user_agent)
        self.event_buffer.append(event)
        if len(self.event_buffer) >= self.buffer_size:
            self._flush_buffer()
        return event

    def _flush_buffer(self):
        """Flush event buffer to disk"""
        for event in self.event_buffer:
            self._write_event(event)
        self.event_buffer.clear()

    def _write_event(self, event: AuditEvent):
        """Write event to persistent log"""
        date_str = datetime.now().strftime('%Y%m%d')
        log_file = self.log_dir / f"audit_{date_str}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(asdict(event)) + '\n')
