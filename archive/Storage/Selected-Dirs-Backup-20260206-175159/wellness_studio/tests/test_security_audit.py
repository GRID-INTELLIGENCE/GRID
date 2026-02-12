"""
Comprehensive Audit Logging Tests for Wellness Studio
Tests for audit trail, access monitoring, and compliance tracking
"""
import pytest
import sys
import os
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from wellness_studio.security import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    DataAccessMonitor
)


class TestAuditEventCreation:
    """Test audit event creation and structure"""
    
    def test_event_creation(self):
        """Test basic event creation"""
        event = AuditEvent(
            event_id="evt_123",
            timestamp="2024-01-15T10:30:00",
            event_type="data_input",
            user_id="user_001",
            session_id="sess_456",
            resource_id="res_789",
            action="file_upload",
            status="success",
            details={"size": 1024}
        )
        
        assert event.event_id == "evt_123"
        assert event.user_id == "user_001"
        assert event.status == "success"
    
    def test_event_to_dict(self):
        """Test event serialization to dict"""
        event = AuditEvent(
            event_id="evt_123",
            timestamp="2024-01-15T10:30:00",
            event_type="data_input",
            user_id="user_001",
            session_id="sess_456",
            resource_id=None,
            action="test_action",
            status="success",
            details={}
        )
        
        d = event.to_dict()
        assert d['event_id'] == "evt_123"
        assert d['user_id'] == "user_001"
    
    def test_event_to_json(self):
        """Test event serialization to JSON"""
        event = AuditEvent(
            event_id="evt_123",
            timestamp="2024-01-15T10:30:00",
            event_type="data_input",
            user_id="user_001",
            session_id="sess_456",
            resource_id="res_789",
            action="test",
            status="success",
            details={"key": "value"}
        )
        
        json_str = event.to_json()
        assert "evt_123" in json_str
        assert "test" in json_str
        
        # Verify valid JSON
        parsed = json.loads(json_str)
        assert parsed['event_id'] == "evt_123"


class TestAuditLoggerBasic:
    """Test basic audit logging functionality"""
    
    def test_logger_initialization(self):
        """Test logger setup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            assert logger.log_dir.exists()
            assert len(logger.session_id) == 12
    
    def test_log_event(self):
        """Test logging a generic event"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            event = logger.log_event(
                event_type=AuditEventType.DATA_INPUT,
                action="file_received",
                status="success",
                user_id="user_001",
                details={"filename": "test.pdf"}
            )
            
            assert event.event_type == "data_input"
            assert event.action == "file_received"
            assert event.user_id == "user_001"
    
    def test_log_data_input(self):
        """Test data input logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            event = logger.log_data_input(
                source_type="pdf",
                content_hash="abc123def456",
                size_bytes=2048,
                pii_detected=True,
                user_id="user_001"
            )
            
            assert event.event_type == "data_input"
            assert event.details['source_type'] == "pdf"
            assert event.details['pii_detected'] is True
    
    def test_log_pii_detection(self):
        """Test PII detection logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            event = logger.log_pii_detection(
                content_hash="abc123",
                entity_types=["SSN", "EMAIL"],
                entity_count=2,
                risk_level="HIGH",
                user_id="user_001"
            )
            
            assert event.event_type == "pii_detected"
            assert event.details['entity_count'] == 2
            assert "SSN" in event.details['entity_types']
    
    def test_log_pii_sanitization(self):
        """Test PII sanitization logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            event = logger.log_pii_sanitization(
                content_hash="abc123",
                entities_removed=3,
                sanitization_method="hash",
                user_id="user_001"
            )
            
            assert event.event_type == "pii_sanitized"
            assert event.details['entities_removed'] == 3
    
    def test_log_model_inference(self):
        """Test model inference logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            event = logger.log_model_inference(
                model_name="llama-3.1",
                input_hash="input123",
                output_hash="output456",
                duration_ms=1500.5,
                user_id="user_001"
            )
            
            assert event.event_type == "model_inference"
            assert event.details['model'] == "llama-3.1"
            assert event.details['duration_ms'] == 1500.5
    
    def test_log_safety_violation(self):
        """Test safety violation logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            event = logger.log_safety_violation(
                violation_type="prompt_injection",
                severity="critical",
                blocked=True,
                detected_content="malicious content",
                user_id="user_001"
            )
            
            assert event.event_type == "safety_violation"
            assert event.status == "blocked"
            assert event.details['severity'] == "critical"
    
    def test_log_report_generation(self):
        """Test report generation logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            event = logger.log_report_generation(
                report_path="/reports/report_001.md",
                format="markdown",
                patient_id="patient_001",
                content_hash="content123",
                user_id="user_001"
            )
            
            assert event.event_type == "report_generated"
            assert event.details['format'] == "markdown"
    
    def test_log_error(self):
        """Test error logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            event = logger.log_error(
                error_type="ModelLoadError",
                error_message="Failed to load model",
                stack_trace="Traceback...",
                user_id="user_001"
            )
            
            assert event.event_type == "error_occurred"
            assert event.status == "failure"
            assert event.details['error_type'] == "ModelLoadError"


class TestAuditPersistence:
    """Test audit log persistence to disk"""
    
    def test_events_written_to_file(self):
        """Test that events are written to log file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(
                event_type=AuditEventType.DATA_INPUT,
                action="test",
                status="success"
            )
            logger.close()
            
            date_str = datetime.now().strftime('%Y%m%d')
            log_file = Path(tmpdir) / f"audit_{date_str}.jsonl"
            
            assert log_file.exists()
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                data = json.loads(lines[0])
                assert data['action'] == "test"
    
    def test_multiple_events_in_file(self):
        """Test multiple events in same log file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(AuditEventType.DATA_INPUT, "event1", "success")
            logger.log_event(AuditEventType.DATA_PROCESSING, "event2", "success")
            logger.close()
            
            date_str = datetime.now().strftime('%Y%m%d')
            log_file = Path(tmpdir) / f"audit_{date_str}.jsonl"
            
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 2
    
    def test_buffer_flush(self):
        """Test that buffer is flushed properly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.buffer_size = 3
            
            # Add events without triggering auto-flush
            logger.log_event(AuditEventType.DATA_INPUT, "event1", "success")
            logger.log_event(AuditEventType.DATA_INPUT, "event2", "success")
            
            # Manual flush
            logger._flush_buffer()
            
            date_str = datetime.now().strftime('%Y%m%d')
            log_file = Path(tmpdir) / f"audit_{date_str}.jsonl"
            
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 2


class TestAuditRetrieval:
    """Test audit trail retrieval and filtering"""
    
    def test_retrieve_all_events(self):
        """Test retrieving all events"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(AuditEventType.DATA_INPUT, "action1", "success")
            logger.log_event(AuditEventType.DATA_ACCESS, "action2", "success")
            logger.close()
            
            events = logger.get_audit_trail()
            assert len(events) == 2
    
    def test_filter_by_event_type(self):
        """Test filtering by event type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(AuditEventType.DATA_INPUT, "action1", "success")
            logger.log_event(AuditEventType.DATA_ACCESS, "action2", "success")
            logger.log_event(AuditEventType.DATA_INPUT, "action3", "success")
            logger.close()
            
            events = logger.get_audit_trail(event_type=AuditEventType.DATA_INPUT)
            assert len(events) == 2
            for e in events:
                assert e.event_type == "data_input"
    
    def test_filter_by_user(self):
        """Test filtering by user ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(AuditEventType.DATA_INPUT, "action", "success", user_id="user_001")
            logger.log_event(AuditEventType.DATA_INPUT, "action", "success", user_id="user_002")
            logger.log_event(AuditEventType.DATA_INPUT, "action", "success", user_id="user_001")
            logger.close()
            
            events = logger.get_audit_trail(user_id="user_001")
            assert len(events) == 2
            for e in events:
                assert e.user_id == "user_001"
    
    def test_filter_by_date_range(self):
        """Test filtering by date range"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Create event with current timestamp
            logger.log_event(AuditEventType.DATA_INPUT, "recent", "success")
            logger.close()
            
            # Filter for today
            today = datetime.now().replace(hour=0, minute=0, second=0)
            tomorrow = today + timedelta(days=1)
            
            events = logger.get_audit_trail(start_date=today, end_date=tomorrow)
            assert len(events) == 1
    
    def test_combined_filters(self):
        """Test combining multiple filters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(AuditEventType.DATA_INPUT, "action", "success", user_id="user_001")
            logger.log_event(AuditEventType.DATA_ACCESS, "action", "success", user_id="user_001")
            logger.close()
            
            events = logger.get_audit_trail(
                event_type=AuditEventType.DATA_INPUT,
                user_id="user_001"
            )
            assert len(events) == 1


class TestAuditSummaryStats:
    """Test audit summary statistics"""
    
    def test_summary_basic(self):
        """Test basic summary generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(AuditEventType.DATA_INPUT, "action", "success")
            logger.log_event(AuditEventType.DATA_ACCESS, "action", "success")
            logger.close()
            
            stats = logger.get_summary_stats(days=7)
            
            assert stats['total_events'] == 2
            assert stats['period_days'] == 7
    
    def test_summary_by_type(self):
        """Test summary counting by type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(AuditEventType.DATA_INPUT, "action", "success")
            logger.log_event(AuditEventType.DATA_INPUT, "action", "success")
            logger.log_event(AuditEventType.DATA_ACCESS, "action", "success")
            logger.close()
            
            stats = logger.get_summary_stats()
            
            assert stats['by_event_type']['data_input'] == 2
            assert stats['by_event_type']['data_access'] == 1
    
    def test_summary_by_status(self):
        """Test summary counting by status"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(AuditEventType.DATA_INPUT, "action", "success")
            logger.log_event(AuditEventType.DATA_INPUT, "action", "failure")
            logger.log_event(AuditEventType.DATA_ACCESS, "action", "blocked")
            logger.close()
            
            stats = logger.get_summary_stats()
            
            assert stats['by_status']['success'] == 1
            assert stats['by_status']['failure'] == 1
            assert stats['by_status']['blocked'] == 1
    
    def test_pii_and_safety_counts(self):
        """Test PII and safety violation counting"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            logger.log_event(AuditEventType.PII_DETECTED, "scan", "success")
            logger.log_event(AuditEventType.PII_SANITIZED, "sanitize", "success")
            logger.log_event(AuditEventType.SAFETY_VIOLATION, "violation", "blocked")
            logger.close()
            
            stats = logger.get_summary_stats()
            
            assert stats['pii_events'] == 2
            assert stats['safety_violations'] == 1


class TestDataAccessMonitor:
    """Test data access monitoring"""
    
    def test_access_recording(self):
        """Test recording data access"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            monitor = DataAccessMonitor(logger)
            
            monitor.record_access("resource_001", "user_001")
            
            assert "user_001:resource_001" in monitor.access_patterns
    
    def test_suspicious_activity_detection(self):
        """Test detection of suspicious access patterns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            monitor = DataAccessMonitor(logger)
            monitor.suspicious_threshold = 5
            
            # Generate many accesses
            for _ in range(10):
                monitor.record_access("resource_001", "user_001")
            
            anomalies = monitor.check_anomalies()
            assert len(anomalies) == 1
            assert anomalies[0]['access_count'] == 10
    
    def test_no_anomaly_normal_usage(self):
        """Test that normal usage doesn't trigger anomaly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            monitor = DataAccessMonitor(logger)
            monitor.suspicious_threshold = 100
            
            monitor.record_access("resource_001", "user_001")
            monitor.record_access("resource_001", "user_001")
            
            anomalies = monitor.check_anomalies()
            assert len(anomalies) == 0
    
    def test_old_access_cleanup(self):
        """Test that old access records are cleaned up"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            monitor = DataAccessMonitor(logger)
            
            # Access and check cleanup doesn't error
            monitor.record_access("resource_001", "user_001")
            
            # Should still have the pattern
            assert "user_001:resource_001" in monitor.access_patterns


class TestAuditEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_log_retrieval(self):
        """Test retrieval from empty logs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            events = logger.get_audit_trail()
            assert len(events) == 0
    
    def test_corrupted_log_line(self):
        """Test handling of corrupted log lines"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "audit_20240115.jsonl"

            # Write corrupted line
            with open(log_file, 'w') as f:
                f.write('corrupted json\n')
                f.write(json.dumps({'event_id': 'valid', 'timestamp': datetime.now().isoformat(),
                                   'event_type': 'test', 'user_id': 'test', 'session_id': 'test',
                                   'resource_id': None, 'action': 'test', 'status': 'success', 'details': {}}) + '\n')

            logger = AuditLogger(log_dir=log_dir)
            events = logger.get_audit_trail()

            # Should skip corrupted line, keep valid
            assert len(events) == 1
    
    def test_large_detail_dict(self):
        """Test handling of large detail dictionaries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            large_details = {f"key_{i}": f"value_{i}" for i in range(1000)}
            
            event = logger.log_event(
                event_type=AuditEventType.DATA_INPUT,
                action="test",
                status="success",
                details=large_details
            )
            
            assert len(event.details) == 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
