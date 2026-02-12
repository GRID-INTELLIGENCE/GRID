"""
Comprehensive Security Tests for Wellness Studio
Tests for PII detection, data sanitization, and privacy safeguards
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from wellness_studio.security import (
    PIIDetector, 
    SensitivityLevel,
    PIIEntity,
    DataRetentionPolicy,
    SecureDataHandler
)


class TestPIIDetection:
    """Test PII detection and classification"""
    
    def test_detect_ssn(self):
        """Test SSN pattern detection"""
        detector = PIIDetector()
        text = "Patient SSN is 123-45-6789 for insurance verification"
        entities = detector.detect_pii(text)
        
        assert len(entities) >= 1
        ssn_entities = [e for e in entities if e.entity_type == 'SSN']
        assert len(ssn_entities) == 1
        assert ssn_entities[0].value == '123-45-6789'
        assert ssn_entities[0].sensitivity == SensitivityLevel.PII
    
    def test_detect_phone_numbers(self):
        """Test phone number detection"""
        detector = PIIDetector()
        text = "Contact me at 555-123-4567 or (555) 987-6543"
        entities = detector.detect_pii(text)
        
        phone_entities = [e for e in entities if e.entity_type == 'PHONE']
        assert len(phone_entities) == 2
    
    def test_detect_email(self):
        """Test email detection"""
        detector = PIIDetector()
        text = "Send results to john.doe@email.com"
        entities = detector.detect_pii(text)
        
        email_entities = [e for e in entities if e.entity_type == 'EMAIL']
        assert len(email_entities) == 1
        assert 'john.doe@email.com' in email_entities[0].value
    
    def test_detect_mrn(self):
        """Test Medical Record Number detection"""
        detector = PIIDetector()
        text = "MRN: 123456789 for patient visit"
        entities = detector.detect_pii(text)
        
        mrn_entities = [e for e in entities if e.entity_type == 'MRN']
        assert len(mrn_entities) >= 1
        assert mrn_entities[0].sensitivity == SensitivityLevel.PHI
    
    def test_detect_dob(self):
        """Test date of birth detection"""
        detector = PIIDetector()
        text = "Patient DOB: 03/15/1985"
        entities = detector.detect_pii(text)
        
        dob_entities = [e for e in entities if e.entity_type in ['DATE_OF_BIRTH', 'DOB_ALT']]
        assert len(dob_entities) >= 1
    
    def test_detect_credit_card(self):
        """Test credit card detection"""
        detector = PIIDetector()
        text = "Payment card: 4532-1234-5678-9012"
        entities = detector.detect_pii(text)
        
        cc_entities = [e for e in entities if e.entity_type == 'CREDIT_CARD']
        assert len(cc_entities) == 1
    
    def test_no_pii_in_safe_text(self):
        """Test that safe text returns no entities"""
        detector = PIIDetector()
        text = "The patient reports feeling better today. No specific concerns."
        entities = detector.detect_pii(text)
        
        assert len(entities) == 0


class TestPIISanitization:
    """Test PII sanitization methods"""
    
    def test_hash_sanitization(self):
        """Test hash-based sanitization"""
        detector = PIIDetector()
        text = "Patient SSN is 123-45-6789"
        sanitized, mapping = detector.sanitize_text(text, replacement_mode='hash')
        
        assert '123-45-6789' not in sanitized
        assert '[ID_' in sanitized
        assert len(mapping) == 1
    
    def test_mask_sanitization(self):
        """Test mask-based sanitization"""
        detector = PIIDetector()
        text = "Patient SSN is 123-45-6789"
        sanitized, mapping = detector.sanitize_text(text, replacement_mode='mask')
        
        assert '123-45-6789' not in sanitized
        assert 'XXX-XX-' in sanitized
        assert '6789' in sanitized  # Last 4 preserved
    
    def test_remove_sanitization(self):
        """Test redaction sanitization"""
        detector = PIIDetector()
        text = "Patient SSN is 123-45-6789"
        entities = detector.detect_pii(text)
        sanitized, mapping = detector.sanitize_text(text, entities, replacement_mode='remove')
        
        assert '[SSN_REDACTED]' in sanitized
        assert '123-45-6789' not in sanitized
    
    def test_multiple_entities_sanitization(self):
        """Test sanitizing multiple PII types"""
        detector = PIIDetector()
        text = "John Smith, SSN: 123-45-6789, Phone: 555-123-4567"
        sanitized, mapping = detector.sanitize_text(text, replacement_mode='hash')
        
        assert '123-45-6789' not in sanitized
        assert '555-123-4567' not in sanitized
        assert len(mapping) >= 2
    
    def test_email_masking(self):
        """Test email-specific masking"""
        detector = PIIDetector()
        text = "Contact john.doe@example.com"
        entities = detector.detect_pii(text)
        sanitized, _ = detector.sanitize_text(text, entities, replacement_mode='mask')
        
        assert 'john.doe@example.com' not in sanitized
        assert '***' in sanitized or '***@' in sanitized


class TestRiskAssessment:
    """Test risk assessment functionality"""
    
    def test_critical_risk_level(self):
        """Test critical risk assessment"""
        detector = PIIDetector()
        text = "SSN: 123-45-6789, MRN: 123456789, DOB: 03/15/1985"
        assessment = detector.assess_risk_level(text)
        
        assert assessment['risk_level'] in ['CRITICAL', 'HIGH']
        assert assessment['phi_count'] >= 2
        assert assessment['requires_sanitization'] is True
    
    def test_high_risk_level(self):
        """Test high risk assessment"""
        detector = PIIDetector()
        text = "Patient John Smith, SSN: 123-45-6789"
        assessment = detector.assess_risk_level(text)
        
        assert assessment['risk_level'] in ['HIGH', 'MEDIUM', 'CRITICAL']
        assert assessment['pii_count'] >= 1
    
    def test_low_risk_level(self):
        """Test low risk assessment"""
        detector = PIIDetector()
        text = "Patient reports mild headache"
        assessment = detector.assess_risk_level(text)
        
        assert assessment['risk_level'] == 'LOW'
        assert assessment['score'] == 0
        assert assessment['requires_sanitization'] is False


class TestDataRetention:
    """Test data retention policy enforcement"""
    
    def test_data_registration(self):
        """Test data registration"""
        policy = DataRetentionPolicy(retention_days=30)
        policy.register_data('data_001', SensitivityLevel.PHI)
        
        assert 'data_001' in policy.data_registry
        assert policy.data_registry['data_001']['sensitivity'] == SensitivityLevel.PHI
    
    def test_expiration_check(self):
        """Test expiration detection"""
        policy = DataRetentionPolicy(retention_days=1)
        policy.register_data('old_data', SensitivityLevel.INTERNAL)
        
        # Manually set creation date to past
        policy.data_registry['old_data']['created_at'] = datetime.now() - timedelta(days=2)
        
        assert policy.check_expiration('old_data') is True
    
    def test_phi_immediate_disposal(self):
        """Test PHI disposal policy"""
        policy = DataRetentionPolicy(retention_days=30)
        policy.register_data('phi_data', SensitivityLevel.PHI)
        
        # PHI should be disposed quickly
        policy.data_registry['phi_data']['created_at'] = datetime.now() - timedelta(days=10)
        
        should_dispose, reason = policy.should_dispose('phi_data')
        assert should_dispose is True
        assert 'PHI' in reason
    
    def test_active_data_not_expired(self):
        """Test that recent data is not expired"""
        policy = DataRetentionPolicy(retention_days=30)
        policy.register_data('new_data', SensitivityLevel.CONFIDENTIAL)
        
        assert policy.check_expiration('new_data') is False
        should_dispose, _ = policy.should_dispose('new_data')
        assert should_dispose is False


class TestSecureDataHandler:
    """Test secure data handling"""
    
    def test_content_hashing(self):
        """Test content integrity hashing"""
        handler = SecureDataHandler()
        content = "Sensitive patient data"
        hash1 = handler.hash_content(content)
        hash2 = handler.hash_content(content)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex
    
    def test_different_content_different_hashes(self):
        """Test that different content produces different hashes"""
        handler = SecureDataHandler()
        hash1 = handler.hash_content("Content A")
        hash2 = handler.hash_content("Content B")
        
        assert hash1 != hash2
    
    def test_access_logging(self):
        """Test access logging"""
        handler = SecureDataHandler()
        handler.log_access('read', 'data_001', 'user_123', success=True)
        
        assert len(handler.access_log) == 1
        assert handler.access_log[0]['operation'] == 'read'
        assert handler.access_log[0]['user_id'] == 'user_123'
    
    def test_audit_retrieval(self):
        """Test audit trail retrieval"""
        handler = SecureDataHandler()
        handler.log_access('read', 'data_001', 'user_123')
        handler.log_access('write', 'data_001', 'user_123')
        handler.log_access('read', 'data_002', 'user_456')
        
        data_001_logs = handler.get_access_audit('data_001')
        assert len(data_001_logs) == 2
    
    def test_integrity_validation(self):
        """Test data integrity validation"""
        handler = SecureDataHandler()
        content = "Important medical data"
        stored_hash = handler.hash_content(content)
        
        assert handler.validate_data_integrity(content, stored_hash) is True
        assert handler.validate_data_integrity("tampered data", stored_hash) is False


class TestPIIEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_text(self):
        """Test handling of empty text"""
        detector = PIIDetector()
        entities = detector.detect_pii("")
        assert len(entities) == 0
        
        assessment = detector.assess_risk_level("")
        assert assessment['risk_level'] == 'LOW'
    
    def test_very_long_text(self):
        """Test handling of very long text"""
        detector = PIIDetector()
        text = "Patient data. " * 10000
        text += "SSN: 123-45-6789"
        entities = detector.detect_pii(text)
        
        ssn_entities = [e for e in entities if e.entity_type == 'SSN']
        assert len(ssn_entities) == 1
    
    def test_multiple_ssns(self):
        """Test detection of multiple SSNs"""
        detector = PIIDetector()
        text = "SSNs: 123-45-6789 and 987-65-4321"
        entities = detector.detect_pii(text)
        
        ssn_entities = [e for e in entities if e.entity_type == 'SSN']
        assert len(ssn_entities) == 2
    
    def test_partial_ssn(self):
        """Test that partial SSNs are not detected"""
        detector = PIIDetector()
        text = "Last 4 digits: 6789"
        entities = detector.detect_pii(text)
        
        ssn_entities = [e for e in entities if e.entity_type == 'SSN']
        assert len(ssn_entities) == 0
    
    def test_similar_but_not_pii(self):
        """Test that similar patterns are not flagged"""
        detector = PIIDetector()
        text = "Room 123-4567 is the conference room"  # Not a phone
        entities = detector.detect_pii(text)
        
        # Should not detect as phone (too short for US phone number)
        phone_entities = [e for e in entities if e.entity_type == 'PHONE']
        assert len(phone_entities) == 0


class TestDetectionLogging:
    """Test audit logging of PII detection"""
    
    def test_detection_logged(self):
        """Test that detections are logged"""
        detector = PIIDetector()
        text = "SSN: 123-45-6789"
        detector.detect_pii(text)
        
        assert len(detector.detection_log) == 1
        assert detector.detection_log[0]['entity_count'] == 1
        assert detector.detection_log[0]['phi_detected'] is False  # SSN is PII not PHI
    
    def test_phi_detection_logged(self):
        """Test PHI detection logging"""
        detector = PIIDetector()
        text = "MRN: 123456789"
        detector.detect_pii(text)
        
        assert detector.detection_log[0]['phi_detected'] is True
    
    def test_summary_stats(self):
        """Test detection summary"""
        detector = PIIDetector()
        detector.detect_pii("SSN: 123-45-6789")
        detector.detect_pii("Email: test@test.com")
        
        summary = detector.get_detection_summary()
        assert summary['total_scans'] == 2
        assert summary['total_entities_detected'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
