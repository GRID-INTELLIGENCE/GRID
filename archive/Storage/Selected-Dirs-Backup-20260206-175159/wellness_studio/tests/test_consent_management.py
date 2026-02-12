"""
Comprehensive tests for Consent Management module
Tests GDPR/CCPA compliance features
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from wellness_studio.security import (
    ConsentManager,
    ConsentType,
    ConsentStatus,
    ConsentRecord
)


class TestConsentManagement:
    """Test consent management functionality"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def consent_manager(self, temp_storage):
        """Create consent manager with temp storage"""
        return ConsentManager(storage_dir=temp_storage)
    
    def test_request_consent(self, consent_manager):
        """Test requesting consent from user"""
        record = consent_manager.request_consent(
            user_id="user_001",
            consent_type=ConsentType.DATA_PROCESSING,
            metadata={"purpose": "medical_analysis"}
        )
        
        assert record.status == ConsentStatus.PENDING.value
        assert record.user_id == "user_001"
        assert record.consent_type == ConsentType.DATA_PROCESSING.value
        assert record.granted_at is None
        assert record.version == 1
    
    def test_grant_consent(self, consent_manager):
        """Test granting consent"""
        record = consent_manager.request_consent(
            user_id="user_001",
            consent_type=ConsentType.DATA_PROCESSING
        )
        
        granted = consent_manager.grant_consent(record.consent_id, "user_001")
        
        assert granted.status == ConsentStatus.GRANTED.value
        assert granted.granted_at is not None
        assert granted.version == 2
    
    def test_revoke_consent(self, consent_manager):
        """Test revoking consent"""
        record = consent_manager.request_consent(
            user_id="user_001",
            consent_type=ConsentType.DATA_PROCESSING
        )
        consent_manager.grant_consent(record.consent_id, "user_001")
        
        revoked = consent_manager.revoke_consent(record.consent_id, "user_001")
        
        assert revoked.status == ConsentStatus.REVOKED.value
        assert revoked.revoked_at is not None
    
    def test_check_consent_granted(self, consent_manager):
        """Test checking if consent is granted"""
        record = consent_manager.request_consent(
            user_id="user_001",
            consent_type=ConsentType.DATA_PROCESSING
        )
        consent_manager.grant_consent(record.consent_id, "user_001")
        
        assert consent_manager.check_consent("user_001", ConsentType.DATA_PROCESSING) is True
        assert consent_manager.check_consent("user_001", ConsentType.MARKETING) is False
    
    def test_check_consent_denied(self, consent_manager):
        """Test checking when consent is not granted"""
        assert consent_manager.check_consent("user_001", ConsentType.DATA_PROCESSING) is False
    
    def test_get_current_consent(self, consent_manager):
        """Test getting current consent"""
        record = consent_manager.request_consent(
            user_id="user_001",
            consent_type=ConsentType.DATA_PROCESSING
        )
        consent_manager.grant_consent(record.consent_id, "user_001")
        
        current = consent_manager.get_current_consent("user_001", ConsentType.DATA_PROCESSING.value)
        
        assert current is not None
        assert current.status == ConsentStatus.GRANTED.value
    
    def test_consent_replacement(self, consent_manager):
        """Test that granting new consent revokes old one"""
        record1 = consent_manager.request_consent(
            user_id="user_001",
            consent_type=ConsentType.DATA_PROCESSING
        )
        consent_manager.grant_consent(record1.consent_id, "user_001")
        
        record2 = consent_manager.request_consent(
            user_id="user_001",
            consent_type=ConsentType.DATA_PROCESSING
        )
        consent_manager.grant_consent(record2.consent_id, "user_001")
        
        # Check that record1 was superseded (audit trail preserved)
        assert 'superseded_by' in consent_manager.consent_records[record1.consent_id].metadata
        
        # Check that record2 is granted
        granted = consent_manager.consent_records[record2.consent_id]
        assert granted.status == ConsentStatus.GRANTED.value
    
    def test_set_privacy_preference(self, consent_manager):
        """Test setting privacy preferences"""
        consent_manager.set_privacy_preference(
            user_id="user_001",
            preference_key="data_retention_days",
            value=30
        )
        
        value = consent_manager.get_privacy_preference("user_001", "data_retention_days")
        assert value == 30
    
    def test_get_privacy_preference_default(self, consent_manager):
        """Test getting privacy preference with default"""
        value = consent_manager.get_privacy_preference("user_001", "nonexistent", "default")
        assert value == "default"
    
    def test_get_user_consent_summary(self, consent_manager):
        """Test getting user consent summary"""
        for consent_type in [ConsentType.DATA_PROCESSING, ConsentType.ANALYTICS]:
            record = consent_manager.request_consent("user_001", consent_type)
            consent_manager.grant_consent(record.consent_id, "user_001")
        
        summary = consent_manager.get_user_consent_summary("user_001")
        
        assert summary['user_id'] == "user_001"
        assert 'consents' in summary
        assert summary['total_consents'] >= 2
    
    def test_export_user_data(self, consent_manager):
        """Test GDPR data portability export"""
        record = consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        consent_manager.grant_consent(record.consent_id, "user_001")
        
        export = consent_manager.export_user_data("user_001")
        
        assert export['user_id'] == "user_001"
        assert 'export_date' in export
        assert 'consent_records' in export
        assert len(export['consent_records']) >= 1
    
    def test_delete_user_data(self, consent_manager):
        """Test GDPR right to be forgotten"""
        record = consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        consent_manager.grant_consent(record.consent_id, "user_001")
        
        result = consent_manager.delete_user_data("user_001")
        
        assert result is True
        assert consent_manager.check_consent("user_001", ConsentType.DATA_PROCESSING) is False
    
    def test_get_consent_audit_trail(self, consent_manager):
        """Test getting consent audit trail"""
        record = consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        consent_manager.grant_consent(record.consent_id, "user_001")
        consent_manager.revoke_consent(record.consent_id, "user_001")
        
        trail = consent_manager.get_consent_audit_trail("user_001")
        
        assert len(trail) >= 1
        assert any(t['status'] == ConsentStatus.GRANTED.value for t in trail)
        assert any(t['status'] == ConsentStatus.REVOKED.value for t in trail)
    
    def test_multiple_consent_types(self, consent_manager):
        """Test managing multiple consent types"""
        consent_types = [
            ConsentType.DATA_PROCESSING,
            ConsentType.ANALYTICS,
            ConsentType.RESEARCH
        ]
        
        for consent_type in consent_types:
            record = consent_manager.request_consent("user_001", consent_type)
            consent_manager.grant_consent(record.consent_id, "user_001")
        
        summary = consent_manager.get_user_consent_summary("user_001")
        
        for consent_type in consent_types:
            assert summary['consents'][consent_type.value]['status'] == ConsentStatus.GRANTED.value
    
    def test_invalid_consent_id(self, consent_manager):
        """Test handling invalid consent ID"""
        with pytest.raises(ValueError):
            consent_manager.grant_consent("invalid_id", "user_001")
    
    def test_user_id_mismatch(self, consent_manager):
        """Test user ID mismatch handling"""
        record = consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        
        with pytest.raises(ValueError):
            consent_manager.grant_consent(record.consent_id, "user_002")
    
    def test_revoke_non_granted_consent(self, consent_manager):
        """Test revoking consent that wasn't granted"""
        record = consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        
        with pytest.raises(ValueError):
            consent_manager.revoke_consent(record.consent_id, "user_001")
    
    def test_consent_persistence(self, consent_manager, temp_storage):
        """Test that consent data persists across instances"""
        record = consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        consent_manager.grant_consent(record.consent_id, "user_001")
        
        # Create new instance with same storage
        new_manager = ConsentManager(storage_dir=temp_storage)
        
        assert new_manager.check_consent("user_001", ConsentType.DATA_PROCESSING) is True


class TestConsentGDPRCompliance:
    """Test GDPR compliance features"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def consent_manager(self, temp_storage):
        """Create consent manager with temp storage"""
        return ConsentManager(storage_dir=temp_storage)
    
    def test_right_to_access(self, consent_manager):
        """Test GDPR right to access data"""
        consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        
        export = consent_manager.export_user_data("user_001")
        
        assert 'consent_records' in export
        assert 'privacy_preferences' in export
        assert 'export_date' in export
    
    def test_right_to_rectification(self, consent_manager):
        """Test GDPR right to rectification"""
        consent_manager.set_privacy_preference("user_001", "email", "old@example.com")
        consent_manager.set_privacy_preference("user_001", "email", "new@example.com")
        
        value = consent_manager.get_privacy_preference("user_001", "email")
        
        assert value == "new@example.com"
    
    def test_right_to_erasure(self, consent_manager):
        """Test GDPR right to erasure (right to be forgotten)"""
        consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        consent_manager.grant_consent(
            consent_manager.get_current_consent("user_001", ConsentType.DATA_PROCESSING.value).consent_id,
            "user_001"
        )
        
        consent_manager.delete_user_data("user_001")
        
        assert consent_manager.check_consent("user_001", ConsentType.DATA_PROCESSING) is False
    
    def test_right_to_withdraw_consent(self, consent_manager):
        """Test GDPR right to withdraw consent"""
        record = consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        consent_manager.grant_consent(record.consent_id, "user_001")
        
        assert consent_manager.check_consent("user_001", ConsentType.DATA_PROCESSING) is True
        
        consent_manager.revoke_consent(record.consent_id, "user_001")
        
        assert consent_manager.check_consent("user_001", ConsentType.DATA_PROCESSING) is False
    
    def test_consent_audit_trail_completeness(self, consent_manager):
        """Test that audit trail captures all consent changes"""
        record = consent_manager.request_consent("user_001", ConsentType.DATA_PROCESSING)
        consent_manager.grant_consent(record.consent_id, "user_001")
        consent_manager.revoke_consent(record.consent_id, "user_001")
        
        trail = consent_manager.get_consent_audit_trail("user_001")
        
        statuses = [t['status'] for t in trail]
        assert ConsentStatus.GRANTED.value in statuses
        assert ConsentStatus.REVOKED.value in statuses
