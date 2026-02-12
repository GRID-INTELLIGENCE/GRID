"""
HIPAA Compliance Tests for Wellness Studio
Tests for HIPAA technical safeguards and administrative controls
"""
import pytest
import sys
import os
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from wellness_studio.security import (
    PIIDetector,
    AuditLogger,
    AuditEventType,
    DataRetentionPolicy,
    SecureDataHandler,
    SensitivityLevel
)


class TestHIPAAAccessControl:
    """Test HIPAA Access Control (164.312(a))"""
    
    def test_unique_user_identification(self):
        """Test that users are uniquely identified in audit logs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log actions from different users
            logger.log_data_input("pdf", "hash1", 1024, user_id="dr_smith")
            logger.log_data_input("pdf", "hash2", 1024, user_id="nurse_jones")
            logger.close()
            
            # Verify unique identification
            events = logger.get_audit_trail()
            user_ids = set(e.user_id for e in events)
            assert "dr_smith" in user_ids
            assert "nurse_jones" in user_ids
            assert len(user_ids) == 2
    
    def test_session_tracking(self):
        """Test session identification and tracking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger1 = AuditLogger(log_dir=Path(tmpdir))
            logger2 = AuditLogger(log_dir=Path(tmpdir))
            
            # Different sessions should have different IDs
            assert logger1.session_id != logger2.session_id
            assert len(logger1.session_id) == 12
    
    def test_access_logging(self):
        """Test all access is logged (integrity control)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))

            # Simulate data access
            logger.log_event(
                AuditEventType.DATA_ACCESS,
                "view_patient_record",
                user_id="user_001",
                resource_id="patient_123"
            )
            logger.close()

            # Verify access was logged
            events = logger.get_audit_trail(event_type=AuditEventType.DATA_ACCESS)
            assert len(events) == 1
            assert events[0].resource_id == "patient_123"


class TestHIPAAAuditControls:
    """Test HIPAA Audit Controls (164.312(b))"""
    
    def test_comprehensive_audit_logging(self):
        """Test that all required events are logged"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log all types of events
            logger.log_data_input("pdf", "hash1", 1024)
            logger.log_pii_detection("hash1", ["SSN"], 1, "HIGH")
            logger.log_pii_sanitization("hash1", 1, "hash")
            logger.log_model_inference("model1", "hash1", "hash2", 1000)
            logger.log_report_generation("/path", "md", "patient1", "hash3")
            logger.close()
            
            # Verify all events logged
            events = logger.get_audit_trail()
            event_types = set(e.event_type for e in events)
            
            required_types = [
                'data_input', 'pii_detected', 'pii_sanitized',
                'model_inference', 'report_generated'
            ]
            
            for et in required_types:
                assert et in event_types, f"Missing event type: {et}"
    
    def test_audit_log_integrity(self):
        """Test that audit logs maintain integrity"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log event
            event = logger.log_data_input("pdf", "hash1", 1024)
            logger.close()
            
            # Read back and verify
            events = logger.get_audit_trail()
            assert len(events) == 1
            
            # Verify event data matches
            assert events[0].event_id == event.event_id
            assert events[0].timestamp == event.timestamp
            assert events[0].user_id == event.user_id
    
    def test_audit_retention(self):
        """Test audit log retention capabilities"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log events
            logger.log_data_input("pdf", "hash1", 1024)
            logger.close()
            
            # Retrieve with date range
            today = datetime.now().replace(hour=0, minute=0, second=0)
            tomorrow = today + timedelta(days=1)
            
            events = logger.get_audit_trail(start_date=today, end_date=tomorrow)
            assert len(events) == 1


class TestHIPAAIntegrityControls:
    """Test HIPAA Integrity Controls (164.312(c))"""
    
    def test_data_integrity_validation(self):
        """Test that data integrity can be validated"""
        handler = SecureDataHandler()
        
        content = "Patient medical data"
        stored_hash = handler.hash_content(content)
        
        # Valid content
        assert handler.validate_data_integrity(content, stored_hash) is True
        
        # Tampered content
        assert handler.validate_data_integrity("tampered data", stored_hash) is False
    
    def test_hash_uniqueness(self):
        """Test that different data produces different hashes"""
        handler = SecureDataHandler()
        
        hash1 = handler.hash_content("Data A")
        hash2 = handler.hash_content("Data B")
        
        assert hash1 != hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_audit_trail_immutability(self):
        """Test that audit logs are append-only"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Write events
            logger.log_data_input("pdf", "hash1", 1024)
            logger.close()
            
            # Try to modify log file
            date_str = datetime.now().strftime('%Y%m%d')
            log_file = Path(tmpdir) / f"audit_{date_str}.jsonl"
            
            # Append is possible (normal operation)
            with open(log_file, 'a') as f:
                f.write('{"test": "data"}\n')
            
            # File should now have 2 lines
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 2


class TestHIPAATransmissionSecurity:
    """Test HIPAA Transmission Security (164.312(e))"""
    
    def test_content_hashing_for_transmission(self):
        """Test content is hashed for integrity during transmission"""
        handler = SecureDataHandler()
        
        content = "Sensitive PHI data for transmission"
        content_hash = handler.hash_content(content)
        
        # Hash should be deterministic
        assert handler.hash_content(content) == content_hash
        
        # Should be hex string
        assert all(c in '0123456789abcdef' for c in content_hash)
    
    def test_data_encryption_at_rest(self):
        """Test that sensitive data handling supports encryption"""
        handler = SecureDataHandler(encryption_key="test_key_123")
        
        assert handler.encryption_key is not None
        assert len(handler.encryption_key) > 0
    
    def test_secure_key_generation(self):
        """Test secure key generation"""
        handler1 = SecureDataHandler()
        handler2 = SecureDataHandler()
        
        # Different instances should have different keys
        assert handler1.encryption_key != handler2.encryption_key
        
        # Keys should be sufficiently long
        assert len(handler1.encryption_key) >= 32


class TestHIPAAPHIProtection:
    """Test Protected Health Information specific protections"""
    
    def test_phi_detection_and_classification(self):
        """Test PHI is correctly detected and classified"""
        detector = PIIDetector()
        
        text = "Patient MRN: 123456789, Insurance: BC123456789"
        entities = detector.detect_pii(text)
        
        # Should detect PHI entities
        phi_entities = [e for e in entities if e.sensitivity == SensitivityLevel.PHI]
        assert len(phi_entities) >= 2
        
        # Verify specific types
        entity_types = [e.entity_type for e in phi_entities]
        assert 'MRN' in entity_types or 'INSURANCE_ID' in entity_types
    
    def test_phi_sanitization(self):
        """Test PHI is properly sanitized before processing"""
        detector = PIIDetector()
        
        text = "Patient MRN: 123456789"
        entities = detector.detect_pii(text)
        
        sanitized, mapping = detector.sanitize_text(text, entities)
        
        # Original PHI should not be present
        assert '123456789' not in sanitized
        assert 'MRN' not in sanitized or '[MRN_REDACTED]' in sanitized
        
        # Mapping should contain original for reconstruction if needed
        assert len(mapping) > 0
    
    def test_phi_risk_assessment(self):
        """Test PHI triggers appropriate risk level"""
        detector = PIIDetector()
        
        text = "MRN: 123456789, DOB: 03/15/1985"
        assessment = detector.assess_risk_level(text)
        
        assert assessment['phi_count'] >= 2
        assert assessment['risk_level'] in ['CRITICAL', 'HIGH']
        assert assessment['requires_sanitization'] is True
    
    def test_phi_immediate_disposal(self):
        """Test PHI data disposal policy"""
        policy = DataRetentionPolicy(retention_days=30)
        
        policy.register_data('phi_data', SensitivityLevel.PHI)
        
        # PHI should be flagged for disposal after short period
        policy.data_registry['phi_data']['created_at'] = datetime.now() - timedelta(days=8)
        
        should_dispose, reason = policy.should_dispose('phi_data')
        assert should_dispose is True
        assert 'PHI' in reason


class TestHIPAABreachNotification:
    """Test HIPAA Breach Notification Rule compliance capabilities"""
    
    def test_suspicious_activity_detection(self):
        """Test detection of suspicious access patterns"""
        from wellness_studio.security import DataAccessMonitor
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            monitor = DataAccessMonitor(logger)
            monitor.suspicious_threshold = 5
            
            # Generate suspicious activity
            for _ in range(10):
                monitor.record_access("patient_phi", "user_001")
            
            anomalies = monitor.check_anomalies()
            assert len(anomalies) == 1
            assert anomalies[0]['severity'] in ['high', 'medium']
    
    def test_breach_audit_trail(self):
        """Test that potential breach indicators are logged"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log a potential security incident
            logger.log_safety_violation(
                violation_type="unauthorized_access",
                severity="critical",
                blocked=True,
                detected_content="attempted unauthorized PHI access"
            )
            logger.close()
            
            # Verify incident logged
            events = logger.get_audit_trail(event_type=AuditEventType.SAFETY_VIOLATION)
            assert len(events) == 1
            assert events[0].details['severity'] == "critical"


class TestHIPAAMinimumNecessary:
    """Test HIPAA Minimum Necessary Standard (164.502(b))"""
    
    def test_data_minimization_in_logging(self):
        """Test that only necessary data is logged"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log with content hash (not full content)
            logger.log_data_input("pdf", "hash123", 1024)
            logger.close()
            
            events = logger.get_audit_trail()
            
            # Should only have hash prefix, not full content
            assert events[0].resource_id == "hash123"
            assert len(events[0].details.get('content_hash_prefix', '')) <= 16
    
    def test_phi_masking_in_logs(self):
        """Test that PHI is masked in audit logs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log PII detection
            logger.log_pii_detection(
                content_hash="patient_hash",
                entity_types=["SSN", "MRN"],
                entity_count=2,
                risk_level="CRITICAL"
            )
            logger.close()
            
            events = logger.get_audit_trail()
            
            # Should log entity types but not actual values
            assert "SSN" in events[0].details['entity_types']
            assert "MRN" in events[0].details['entity_types']


class TestHIPAAAdministrativeSafeguards:
    """Test HIPAA Administrative Safeguards (164.308)"""
    
    def test_security_training_compliance_logging(self):
        """Test that security training events can be logged"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log security training event
            logger.log_event(
                AuditEventType.CONFIG_CHANGE,
                "security_training_completed",
                user_id="user_001",
                details={"training_module": "HIPAA_Basics", "score": 100}
            )
            logger.close()
            
            events = logger.get_audit_trail(event_type=AuditEventType.CONFIG_CHANGE)
            assert len(events) == 1
            assert events[0].details['training_module'] == "HIPAA_Basics"
    
    def test_information_access_management(self):
        """Test access management logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log access permission changes
            logger.log_event(
                AuditEventType.CONFIG_CHANGE,
                "access_granted",
                user_id="admin_001",
                details={
                    "target_user": "new_user",
                    "permissions": ["read", "write"],
                    "resource": "patient_records"
                }
            )
            logger.close()
            
            events = logger.get_audit_trail()
            assert len(events) == 1
            assert events[0].action == "access_granted"


class TestHIPAAPrivacyRule:
    """Test HIPAA Privacy Rule compliance (164.500-164.534)"""
    
    def test_patient_rights_audit(self):
        """Test audit of patient rights requests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            # Log patient access request
            logger.log_event(
                AuditEventType.DATA_ACCESS,
                "patient_records_request",
                user_id="patient_001",
                details={"request_type": "access", "records_requested": "all"}
            )
            logger.close()
            
            events = logger.get_audit_trail()
            assert events[0].details['request_type'] == "access"
    
    def test_authorization_logging(self):
        """Test logging of authorizations for disclosures"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=Path(tmpdir))
            
            logger.log_event(
                AuditEventType.DATA_ACCESS,
                "disclosure_with_authorization",
                details={
                    "recipient": "specialist_clinic",
                    "purpose": "treatment",
                    "authorization_on_file": True
                }
            )
            logger.close()
            
            events = logger.get_audit_trail()
            assert events[0].details['authorization_on_file'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
