"""
Wellness Studio - Consent Management
GDPR/CCPA compliant consent tracking and privacy preferences
"""
import json
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path


class ConsentType(Enum):
    """Types of consent required"""
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    RESEARCH = "research"
    THIRD_PARTY_SHARING = "third_party_sharing"


class ConsentStatus(Enum):
    """Status of consent"""
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class ConsentRecord:
    """Single consent record"""
    consent_id: str
    user_id: str
    consent_type: str
    status: str
    granted_at: Optional[str]
    revoked_at: Optional[str]
    version: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ConsentManager:
    """
    Manages user consent and privacy preferences
    GDPR/CCPA compliant implementation
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("consent_data")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self._load_consent_data()
    
    def _get_user_file(self, user_id: str) -> Path:
        """Get file path for user consent data"""
        return self.storage_dir / f"user_{user_id}.json"
    
    def _load_consent_data(self):
        """Load consent data from storage"""
        for user_file in self.storage_dir.glob("user_*.json"):
            try:
                with open(user_file, 'r') as f:
                    data = json.load(f)
                    for consent_data in data.get('consents', []):
                        record = ConsentRecord(**consent_data)
                        self.consent_records[record.consent_id] = record
                    self.user_preferences[user_file.stem[5:]] = data.get('preferences', {})
            except (json.JSONDecodeError, KeyError):
                continue
    
    def _save_user_data(self, user_id: str):
        """Save user consent data to storage"""
        user_file = self._get_user_file(user_id)
        
        user_consents = [
            c.to_dict() for c in self.consent_records.values()
            if c.user_id == user_id
        ]
        
        data = {
            'user_id': user_id,
            'consents': user_consents,
            'preferences': self.user_preferences.get(user_id, {}),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(user_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def request_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        metadata: Optional[Dict] = None
    ) -> ConsentRecord:
        """
        Request consent from user
        
        Args:
            user_id: User identifier
            consent_type: Type of consent requested
            metadata: Additional metadata
            
        Returns:
            Pending consent record
        """
        consent_id = f"cons_{uuid.uuid4().hex[:16]}"
        
        record = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            consent_type=consent_type.value,
            status=ConsentStatus.PENDING.value,
            granted_at=None,
            revoked_at=None,
            version=1,
            metadata=metadata or {}
        )
        
        self.consent_records[consent_id] = record
        self._save_user_data(user_id)
        
        return record
    
    def grant_consent(
        self,
        consent_id: str,
        user_id: str
    ) -> ConsentRecord:
        """
        Grant consent
        
        Args:
            consent_id: Consent record ID
            user_id: User identifier
            
        Returns:
            Updated consent record
        """
        if consent_id not in self.consent_records:
            raise ValueError(f"Consent record {consent_id} not found")
        
        record = self.consent_records[consent_id]
        
        if record.user_id != user_id:
            raise ValueError("User ID mismatch")
        
        # Check if there's an existing granted consent of the same type (different ID)
        user_consents = [
            c for c in self.consent_records.values()
            if c.user_id == user_id and c.consent_type == record.consent_type
        ]
        
        for existing in user_consents:
            if existing.consent_id != consent_id and existing.status == ConsentStatus.GRANTED.value:
                # Revoke existing first
                self.revoke_consent(existing.consent_id, user_id)
        
        record.status = ConsentStatus.GRANTED.value
        record.granted_at = datetime.now().isoformat()
        record.revoked_at = None
        record.version += 1
        
        self._save_user_data(user_id)
        
        return record
    
    def revoke_consent(
        self,
        consent_id: str,
        user_id: str
    ) -> ConsentRecord:
        """
        Revoke consent
        
        Args:
            consent_id: Consent record ID
            user_id: User identifier
            
        Returns:
            Updated consent record
        """
        if consent_id not in self.consent_records:
            raise ValueError(f"Consent record {consent_id} not found")
        
        record = self.consent_records[consent_id]
        
        if record.user_id != user_id:
            raise ValueError("User ID mismatch")
        
        if record.status != ConsentStatus.GRANTED.value:
            raise ValueError("Consent not currently granted")
        
        # Create a new record for the revoked state to preserve audit trail
        revoked_record = ConsentRecord(
            consent_id=f"cons_{uuid.uuid4().hex[:16]}",
            user_id=user_id,
            consent_type=record.consent_type,
            status=ConsentStatus.REVOKED.value,
            granted_at=record.granted_at,
            revoked_at=datetime.now().isoformat(),
            version=record.version + 1,
            metadata=record.metadata.copy()
        )
        
        # Add the revoked record
        self.consent_records[revoked_record.consent_id] = revoked_record
        
        # Mark the original record as superseded (don't change its status)
        # This preserves the audit trail showing both 'granted' and 'revoked'
        record.metadata['superseded_by'] = revoked_record.consent_id
        record.metadata['superseded_at'] = revoked_record.revoked_at
        
        self._save_user_data(user_id)
        
        return revoked_record
    
    def get_current_consent(
        self,
        user_id: str,
        consent_type: str
    ) -> Optional[ConsentRecord]:
        """
        Get current consent status for a type
        
        Args:
            user_id: User identifier
            consent_type: Type of consent
            
        Returns:
            Current consent record or None
        """
        user_consents = [
            c for c in self.consent_records.values()
            if c.user_id == user_id and c.consent_type == consent_type
        ]
        
        # Sort by version descending and return latest
        user_consents.sort(key=lambda x: x.version, reverse=True)
        
        return user_consents[0] if user_consents else None
    
    def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Check if user has granted consent for a type
        
        Args:
            user_id: User identifier
            consent_type: Type of consent
            
        Returns:
            True if consent granted, False otherwise
        """
        consent = self.get_current_consent(user_id, consent_type.value)
        
        return consent is not None and consent.status == ConsentStatus.GRANTED.value
    
    def set_privacy_preference(
        self,
        user_id: str,
        preference_key: str,
        value: Any
    ):
        """
        Set a privacy preference
        
        Args:
            user_id: User identifier
            preference_key: Preference identifier
            value: Preference value
        """
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        self.user_preferences[user_id][preference_key] = value
        self._save_user_data(user_id)
    
    def get_privacy_preference(
        self,
        user_id: str,
        preference_key: str,
        default: Any = None
    ) -> Any:
        """
        Get a privacy preference
        
        Args:
            user_id: User identifier
            preference_key: Preference identifier
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        return self.user_preferences.get(user_id, {}).get(preference_key, default)
    
    def get_user_consent_summary(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get summary of user's consent status
        
        Args:
            user_id: User identifier
            
        Returns:
            Consent summary
        """
        user_consents = [
            c for c in self.consent_records.values()
            if c.user_id == user_id
        ]
        
        summary = {}
        
        for consent_type in ConsentType:
            current = self.get_current_consent(user_id, consent_type.value)
            summary[consent_type.value] = {
                'status': current.status if current else 'none',
                'granted_at': current.granted_at if current else None,
                'version': current.version if current else 0
            }
        
        return {
            'user_id': user_id,
            'consents': summary,
            'preferences': self.user_preferences.get(user_id, {}),
            'total_consents': len(user_consents)
        }
    
    def export_user_data(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Export all user data for GDPR data portability
        
        Args:
            user_id: User identifier
            
        Returns:
            All user data in portable format
        """
        user_consents = [
            c.to_dict() for c in self.consent_records.values()
            if c.user_id == user_id
        ]
        
        return {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'consent_records': user_consents,
            'privacy_preferences': self.user_preferences.get(user_id, {}),
            'total_records': len(user_consents)
        }
    
    def delete_user_data(
        self,
        user_id: str
    ) -> bool:
        """
        Delete all user data (GDPR right to be forgotten)
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful
        """
        # Remove from memory
        self.consent_records = {
            k: v for k, v in self.consent_records.items()
            if v.user_id != user_id
        }
        
        if user_id in self.user_preferences:
            del self.user_preferences[user_id]
        
        # Remove from storage
        user_file = self._get_user_file(user_id)
        if user_file.exists():
            user_file.unlink()
        
        return True
    
    def get_consent_audit_trail(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get audit trail of consent changes
        
        Args:
            user_id: User identifier
            
        Returns:
            List of consent changes
        """
        user_consents = [
            c for c in self.consent_records.values()
            if c.user_id == user_id
        ]
        
        audit_trail = []
        
        for consent in user_consents:
            audit_trail.append({
                'consent_id': consent.consent_id,
                'consent_type': consent.consent_type,
                'status': consent.status,
                'granted_at': consent.granted_at,
                'revoked_at': consent.revoked_at,
                'version': consent.version,
                'metadata': consent.metadata
            })
        
        audit_trail.sort(key=lambda x: x.get('version', 0), reverse=True)
        
        return audit_trail
