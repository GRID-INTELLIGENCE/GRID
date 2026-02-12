"""
Wellness Studio - Security & Privacy Guardrails
PII detection, data sanitization, and security safeguards
"""
import re
import hashlib
import secrets
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SensitivityLevel(Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PHI = "phi"  # Protected Health Information
    PII = "pii"  # Personally Identifiable Information


@dataclass
class PIIEntity:
    """Detected PII entity"""
    entity_type: str
    value: str
    start_pos: int
    end_pos: int
    sensitivity: SensitivityLevel
    confidence: float


class PIIDetector:
    """
    Detects and handles Personally Identifiable Information (PII)
    and Protected Health Information (PHI)
    """
    
    # PII Patterns
    PATTERNS = {
        # Names
        'PERSON_NAME': re.compile(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'),
        
        # Government IDs
        'SSN': re.compile(r'\b(\d{3}-\d{2}-\d{4})\b'),
        'MEDICARE_ID': re.compile(r'\b([A-Z0-9]{9,11})\b'),
        'PASSPORT': re.compile(r'\b([A-Z]{1,2}\d{6,9})\b'),
        
        # Contact Info
        'PHONE': re.compile(r'\b(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b'),
        'EMAIL': re.compile(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'),
        
        # Financial
        'CREDIT_CARD': re.compile(r'\b(\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4})\b'),
        'BANK_ACCOUNT': re.compile(r'\b(\d{8,17})\b'),
        
        # Health-specific
        'MRN': re.compile(r'\b(MRN|Medical\s+Record)\s*:?\s*(\d{6,12})\b', re.IGNORECASE),
        'INSURANCE_ID': re.compile(r'\b([A-Z]{2,4}\d{6,12})\b'),
        
        # Addresses
        'ADDRESS': re.compile(r'\b(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Plaza|Plz)[.,]?\s*(?:Apt|Unit|Suite)?\s*\d*)\b', re.IGNORECASE),
        
        # Dates (potential DOB)
        'DATE_OF_BIRTH': re.compile(r'\b((?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2})\b'),
        'DOB_ALT': re.compile(r'\b(?:born|birth|dob)[\s:]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE),
    }
    
    # PHI Keywords
    PHI_KEYWORDS = [
        'diagnosis', 'treatment', 'medication', 'prescription',
        'doctor', 'physician', 'hospital', 'clinic', 'patient',
        'medical record', 'health condition', 'symptoms',
        'test results', 'lab results', 'blood pressure',
        'cholesterol', 'diabetes', 'cancer', 'mental health'
    ]
    
    def __init__(self):
        self.detection_log: List[Dict] = []
    
    def detect_pii(self, text: str) -> List[PIIEntity]:
        """Detect all PII/PHI entities in text"""
        entities = []
        
        for entity_type, pattern in self.PATTERNS.items():
            for match in pattern.finditer(text):
                entity = PIIEntity(
                    entity_type=entity_type,
                    value=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    sensitivity=self._classify_sensitivity(entity_type),
                    confidence=0.9
                )
                entities.append(entity)
        
        entities.sort(key=lambda x: x.start_pos)
        self._log_detection(text, entities)
        return entities
    
    def _count_phi_keywords(self, text: str) -> int:
        """Count PHI keywords in text for risk assessment"""
        text_lower = text.lower()
        count = 0
        for keyword in self.PHI_KEYWORDS:
            if keyword in text_lower:
                count += 1
        return count
    
    def _classify_sensitivity(self, entity_type: str) -> SensitivityLevel:
        """Classify sensitivity level of entity type"""
        phi_types = {'MRN', 'INSURANCE_ID', 'DATE_OF_BIRTH', 'DOB_ALT', 'MEDICARE_ID'}
        pii_types = {'SSN', 'PASSPORT', 'CREDIT_CARD', 'BANK_ACCOUNT', 'PHONE', 'EMAIL'}
        
        if entity_type in phi_types:
            return SensitivityLevel.PHI
        elif entity_type in pii_types:
            return SensitivityLevel.PII
        elif entity_type in {'PERSON_NAME', 'ADDRESS'}:
            return SensitivityLevel.CONFIDENTIAL
        else:
            return SensitivityLevel.INTERNAL
    
    def sanitize_text(
        self, 
        text: str, 
        entities: Optional[List[PIIEntity]] = None,
        replacement_mode: str = "hash"
    ) -> Tuple[str, Dict[str, str]]:
        """Sanitize PII from text"""
        if entities is None:
            entities = self.detect_pii(text)
        
        entities_sorted = sorted(entities, key=lambda x: x.start_pos, reverse=True)
        sanitized = text
        mapping = {}
        
        for entity in entities_sorted:
            if replacement_mode == "hash":
                replacement = self._hash_identifier(entity.value)
            elif replacement_mode == "mask":
                replacement = self._mask_value(entity.value, entity.entity_type)
            elif replacement_mode == "remove":
                replacement = f"[{entity.entity_type}_REDACTED]"
            else:
                replacement = f"[{entity.entity_type}]"
            
            mapping[replacement] = entity.value
            sanitized = sanitized[:entity.start_pos] + replacement + sanitized[entity.end_pos:]
        
        return sanitized, mapping
    
    def _hash_identifier(self, value: str) -> str:
        """Create hash-based anonymized identifier"""
        hash_obj = hashlib.sha256(value.encode())
        short_hash = hash_obj.hexdigest()[:12]
        return f"[ID_{short_hash}]"
    
    def _mask_value(self, value: str, entity_type: str) -> str:
        """Mask value with appropriate pattern"""
        if entity_type == 'SSN':
            return "XXX-XX-" + value[-4:] if len(value) > 4 else "XXX-XX-XXXX"
        elif entity_type == 'PHONE':
            return "(XXX) XXX-" + value[-4:] if len(value) > 4 else "(XXX) XXX-XXXX"
        elif entity_type == 'EMAIL':
            parts = value.split('@')
            if len(parts) == 2:
                return f"{parts[0][:2]}***@{parts[1]}"
            return "***@***.com"
        elif entity_type == 'CREDIT_CARD':
            return "XXXX-XXXX-XXXX-" + value[-4:] if len(value) > 4 else "XXXX-XXXX-XXXX-XXXX"
        elif entity_type == 'PERSON_NAME':
            parts = value.split()
            return " ".join([p[0] + "." for p in parts])
        else:
            return "X" * min(len(value), 8)
    
    def _log_detection(self, text: str, entities: List[PIIEntity]):
        """Log PII detection for audit purposes"""
        self.detection_log.append({
            'timestamp': datetime.now().isoformat(),
            'text_hash': hashlib.sha256(text.encode()).hexdigest()[:16],
            'entity_count': len(entities),
            'entity_types': list(set(e.entity_type for e in entities)),
            'phi_detected': any(e.sensitivity == SensitivityLevel.PHI for e in entities)
        })
    
    def assess_risk_level(self, text: str) -> Dict[str, Any]:
        """Assess risk level of text containing PII/PHI"""
        entities = self.detect_pii(text)
        
        if not entities:
            return {
                'risk_level': 'LOW',
                'score': 0,
                'categories': [],
                'recommendation': 'No PII detected',
                'requires_sanitization': False
            }
        
        phi_count = sum(1 for e in entities if e.sensitivity == SensitivityLevel.PHI)
        pii_count = sum(1 for e in entities if e.sensitivity == SensitivityLevel.PII)
        conf_count = sum(1 for e in entities if e.sensitivity == SensitivityLevel.CONFIDENTIAL)
        
        # Count PHI keywords for additional context
        keyword_count = self._count_phi_keywords(text)
        
        # Boost score if PHI keywords present alongside PII
        keyword_boost = min(keyword_count, 3) * 2 if (pii_count > 0 or phi_count > 0) else 0
        
        risk_score = (phi_count * 10) + (pii_count * 5) + (conf_count * 2) + keyword_boost
        
        if risk_score >= 20 or phi_count >= 2:
            risk_level = 'CRITICAL'
            recommendation = 'Immediate sanitization required. High PHI exposure.'
        elif risk_score >= 10 or phi_count >= 1:
            risk_level = 'HIGH'
            recommendation = 'Sanitization strongly recommended. PHI present.'
        elif risk_score >= 5:
            risk_level = 'MEDIUM'
            recommendation = 'Review and sanitize if sharing externally.'
        else:
            risk_level = 'LOW'
            recommendation = 'Standard handling acceptable.'
        
        return {
            'risk_level': risk_level,
            'score': risk_score,
            'phi_count': phi_count,
            'pii_count': pii_count,
            'confidential_count': conf_count,
            'total_entities': len(entities),
            'entity_types': list(set(e.entity_type for e in entities)),
            'recommendation': recommendation,
            'requires_sanitization': risk_level in ['CRITICAL', 'HIGH']
        }
    
    def get_detection_summary(self) -> Dict:
        """Get summary of PII detection activity"""
        return {
            'total_scans': len(self.detection_log),
            'total_entities_detected': sum(log['entity_count'] for log in self.detection_log),
            'phi_detected_count': sum(1 for log in self.detection_log if log['phi_detected']),
            'recent_activity': self.detection_log[-10:] if self.detection_log else []
        }


class DataRetentionPolicy:
    """Enforces data retention and disposal policies"""
    
    def __init__(self, retention_days: int = 30, auto_dispose: bool = False):
        self.retention_days = retention_days
        self.auto_dispose = auto_dispose
        self.data_registry: Dict[str, Dict] = {}
    
    def register_data(self, data_id: str, sensitivity: SensitivityLevel):
        """Register data with retention tracking"""
        self.data_registry[data_id] = {
            'created_at': datetime.now(),
            'sensitivity': sensitivity,
            'access_count': 0,
            'last_accessed': datetime.now()
        }
    
    def check_expiration(self, data_id: str) -> bool:
        """Check if data has exceeded retention period"""
        if data_id not in self.data_registry:
            return True
        entry = self.data_registry[data_id]
        age = (datetime.now() - entry['created_at']).days
        return age > self.retention_days
    
    def should_dispose(self, data_id: str) -> Tuple[bool, str]:
        """Determine if data should be disposed"""
        if data_id not in self.data_registry:
            return True, "Not registered"
        
        entry = self.data_registry[data_id]
        age_days = (datetime.now() - entry['created_at']).days
        
        if age_days > self.retention_days:
            return True, f"Exceeded retention period ({age_days} days)"
        
        # PHI data has stricter rules
        if entry['sensitivity'] == SensitivityLevel.PHI:
            if age_days > 7:  # PHI processed immediately after use
                return True, "PHI immediate disposal policy"
        
        return False, "Within retention period"


class SecureDataHandler:
    """Handles secure data operations with encryption and access control"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or secrets.token_hex(32)
        self.access_log: List[Dict] = []
    
    def hash_content(self, content: str) -> str:
        """Create secure hash of content for integrity verification"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def log_access(
        self, 
        operation: str, 
        data_id: str, 
        user_id: Optional[str] = None,
        success: bool = True
    ):
        """Log all data access operations"""
        self.access_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'data_id': data_id,
            'user_id': user_id or 'system',
            'success': success
        })
    
    def get_access_audit(self, data_id: Optional[str] = None) -> List[Dict]:
        """Get audit trail for data access"""
        if data_id:
            return [log for log in self.access_log if log['data_id'] == data_id]
        return self.access_log
    
    def validate_data_integrity(self, content: str, stored_hash: str) -> bool:
        """Validate data hasn't been tampered with"""
        return self.hash_content(content) == stored_hash
