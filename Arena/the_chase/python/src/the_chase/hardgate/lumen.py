"""
Lumen guardian for boundary validation
"""

import re
from dataclasses import dataclass
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

    PATTERNS: dict[str, re.Pattern[str]] = {
        "PERSON_NAME": re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b"),
        "SSN": re.compile(r"\b(\d{3}-\d{2}-\d{4})\b"),
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "PHONE": re.compile(r"\b(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"),
        "CREDIT_CARD": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    }

    def detect_pii(self, text: str) -> list[PIIEntity]:
        """Detect all PII/PHI entities in text"""
        entities: list[PIIEntity] = []
        for entity_type, pattern in self.PATTERNS.items():
            for match in pattern.finditer(text):
                sensitivity = (
                    SensitivityLevel.PII
                    if entity_type in ["PERSON_NAME", "EMAIL", "PHONE", "CREDIT_CARD"]
                    else SensitivityLevel.PHI
                )
                entities.append(
                    PIIEntity(
                        entity_type=entity_type,
                        value=match.group(),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        sensitivity=sensitivity,
                        confidence=0.95,
                    )
                )
        return entities


class Lumen:
    """Boundary validation guardian (enhanced with PIIDetector)"""

    def __init__(self) -> None:
        self.pii_detector = PIIDetector()  # Reuse Wellness Studio implementation

    def validate_boundary(self, data: str) -> bool:
        """Validate data contains no PII"""
        pii_entities = self.pii_detector.detect_pii(data)
        return len(pii_entities) == 0
