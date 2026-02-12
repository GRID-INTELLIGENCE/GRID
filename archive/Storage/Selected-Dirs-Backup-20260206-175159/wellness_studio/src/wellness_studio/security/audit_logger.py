"""
Wellness Studio - Audit Logging & Access Tracking
Comprehensive audit trail for data access and system operations
"""
import json
import hashlib
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum


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


@dataclass
class AuditEvent:
    """Single audit event record"""
    event_id: str
    timestamp: str
    event_type: str
    user_id: Optional[str]
    session_id: str
    resource_id: Optional[str]
    action: str
    status: str  # 'success', 'failure', 'blocked'
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Comprehensive audit logging system
    Tracks all data access, processing, and system events
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path("logs/audit")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = str(uuid.uuid4())[:12]
        self.event_buffer: List[AuditEvent] = []
        self.buffer_size = 100
        
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"evt_{uuid.uuid4().hex[:16]}"
    
    def _get_timestamp(self) -> str:
        """Get current ISO timestamp"""
        return datetime.now().isoformat()
    
    def _write_event(self, event: AuditEvent):
        """Write event to persistent log"""
        date_str = datetime.now().strftime('%Y%m%d')
        log_file = self.log_dir / f"audit_{date_str}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
    
    def _flush_buffer(self):
        """Flush event buffer to disk"""
        for event in self.event_buffer:
            self._write_event(event)
        self.event_buffer.clear()
    
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        status: str = "success",
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditEvent:
        """
        Log an audit event
        
        Returns:
            The created audit event
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=self._get_timestamp(),
            event_type=event_type.value,
            user_id=user_id or 'anonymous',
            session_id=self.session_id,
            resource_id=resource_id,
            action=action,
            status=status,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.event_buffer.append(event)
        
        # Flush if buffer full
        if len(self.event_buffer) >= self.buffer_size:
            self._flush_buffer()
        
        return event
    
    def log_data_input(
        self,
        source_type: str,
        content_hash: str,
        size_bytes: int,
        pii_detected: bool = False,
        user_id: Optional[str] = None
    ) -> AuditEvent:
        """Log data input event"""
        return self.log_event(
            event_type=AuditEventType.DATA_INPUT,
            action="data_received",
            user_id=user_id,
            resource_id=content_hash[:16],
            details={
                'source_type': source_type,
                'content_hash_prefix': content_hash[:16],
                'size_bytes': size_bytes,
                'pii_detected': pii_detected
            }
        )
    
    def log_pii_detection(
        self,
        content_hash: str,
        entity_types: List[str],
        entity_count: int,
        risk_level: str,
        user_id: Optional[str] = None
    ) -> AuditEvent:
        """Log PII detection event"""
        return self.log_event(
            event_type=AuditEventType.PII_DETECTED,
            action="pii_scan_completed",
            user_id=user_id,
            resource_id=content_hash[:16],
            details={
                'entity_types': entity_types,
                'entity_count': entity_count,
                'risk_level': risk_level
            }
        )
    
    def log_pii_sanitization(
        self,
        content_hash: str,
        entities_removed: int,
        sanitization_method: str,
        user_id: Optional[str] = None
    ) -> AuditEvent:
        """Log PII sanitization event"""
        return self.log_event(
            event_type=AuditEventType.PII_SANITIZED,
            action="pii_sanitized",
            user_id=user_id,
            resource_id=content_hash[:16],
            details={
                'entities_removed': entities_removed,
                'method': sanitization_method
            }
        )
    
    def log_model_inference(
        self,
        model_name: str,
        input_hash: str,
        output_hash: str,
        duration_ms: float,
        user_id: Optional[str] = None
    ) -> AuditEvent:
        """Log AI model inference event"""
        return self.log_event(
            event_type=AuditEventType.MODEL_INFERENCE,
            action=f"inference_{model_name}",
            user_id=user_id,
            resource_id=input_hash[:16],
            details={
                'model': model_name,
                'input_hash_prefix': input_hash[:16],
                'output_hash_prefix': output_hash[:16],
                'duration_ms': duration_ms
            }
        )
    
    def log_safety_violation(
        self,
        violation_type: str,
        severity: str,
        blocked: bool,
        detected_content: str,
        user_id: Optional[str] = None
    ) -> AuditEvent:
        """Log safety policy violation"""
        return self.log_event(
            event_type=AuditEventType.SAFETY_VIOLATION,
            action="safety_check_failed",
            status="blocked" if blocked else "flagged",
            user_id=user_id,
            details={
                'violation_type': violation_type,
                'severity': severity,
                'detected_content_hash': hashlib.sha256(detected_content.encode()).hexdigest()[:16]
            }
        )
    
    def log_report_generation(
        self,
        report_path: str,
        format: str,
        patient_id: Optional[str],
        content_hash: str,
        user_id: Optional[str] = None
    ) -> AuditEvent:
        """Log report generation event"""
        return self.log_event(
            event_type=AuditEventType.REPORT_GENERATED,
            action="report_created",
            user_id=user_id,
            resource_id=content_hash[:16],
            details={
                'report_path': str(report_path),
                'format': format,
                'patient_id': patient_id or 'anonymous'
            }
        )
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AuditEvent:
        """Log system error"""
        details = {'error_type': error_type, 'message': error_message}
        if stack_trace:
            details['stack_trace_hash'] = hashlib.sha256(stack_trace.encode()).hexdigest()[:16]
        
        return self.log_event(
            event_type=AuditEventType.ERROR_OCCURRED,
            action="system_error",
            status="failure",
            user_id=user_id,
            details=details
        )
    
    def get_audit_trail(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None
    ) -> List[AuditEvent]:
        """
        Retrieve audit trail with filtering
        """
        events = []
        
        # Collect all log files in date range
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        event = AuditEvent(**data)
                        
                        # Apply filters
                        if start_date and datetime.fromisoformat(event.timestamp) < start_date:
                            continue
                        if end_date and datetime.fromisoformat(event.timestamp) > end_date:
                            continue
                        if event_type and event.event_type != event_type.value:
                            continue
                        if user_id and event.user_id != user_id:
                            continue
                        
                        events.append(event)
                    except (json.JSONDecodeError, TypeError):
                        continue
        
        return events
    
    def get_summary_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get audit summary statistics"""
        since = datetime.now() - __import__('datetime').timedelta(days=days)
        events = self.get_audit_trail(start_date=since)
        
        return {
            'period_days': days,
            'total_events': len(events),
            'by_event_type': self._count_by_type(events),
            'by_status': self._count_by_status(events),
            'pii_events': len([e for e in events if e.event_type in ['pii_detected', 'pii_sanitized']]),
            'safety_violations': len([e for e in events if e.event_type == 'safety_violation']),
            'errors': len([e for e in events if e.event_type == 'error_occurred'])
        }
    
    def _count_by_type(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Count events by type"""
        counts = {}
        for event in events:
            counts[event.event_type] = counts.get(event.event_type, 0) + 1
        return counts
    
    def _count_by_status(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Count events by status"""
        counts = {}
        for event in events:
            counts[event.status] = counts.get(event.status, 0) + 1
        return counts
    
    def close(self):
        """Flush remaining events and close logger"""
        self._flush_buffer()


class DataAccessMonitor:
    """
    Monitor data access patterns for anomalies
    """
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.access_patterns: Dict[str, List[datetime]] = {}
        self.suspicious_threshold = 100  # accesses per hour
    
    def record_access(self, resource_id: str, user_id: str):
        """Record a data access"""
        key = f"{user_id}:{resource_id}"
        now = datetime.now()
        
        if key not in self.access_patterns:
            self.access_patterns[key] = []
        
        self.access_patterns[key].append(now)
        
        # Clean old entries (> 1 hour)
        self.access_patterns[key] = [
            t for t in self.access_patterns[key]
            if (now - t).total_seconds() < 3600
        ]
        
        # Check for suspicious activity
        if len(self.access_patterns[key]) > self.suspicious_threshold:
            self.audit_logger.log_event(
                event_type=AuditEventType.SAFETY_VIOLATION,
                action="suspicious_access_pattern",
                status="flagged",
                details={
                    'user_id': user_id,
                    'resource_id': resource_id,
                    'access_count': len(self.access_patterns[key]),
                    'threshold': self.suspicious_threshold
                }
            )
    
    def check_anomalies(self) -> List[Dict[str, Any]]:
        """Check for anomalous access patterns"""
        anomalies = []
        
        for key, times in self.access_patterns.items():
            if len(times) > self.suspicious_threshold:
                user_id, resource_id = key.split(':', 1)
                anomalies.append({
                    'user_id': user_id,
                    'resource_id': resource_id,
                    'access_count': len(times),
                    'severity': 'high' if len(times) > self.suspicious_threshold * 2 else 'medium'
                })
        
        return anomalies
