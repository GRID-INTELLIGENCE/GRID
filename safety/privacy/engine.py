import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class PrivacyLevel(StrEnum):
    STRICT = "strict"
    BALANCED = "balanced"
    MINIMAL = "minimal"


class MaskingStrategy(StrEnum):
    REDACT = "redact"
    PARTIAL = "partial"
    HASH = "hash"
    TOKENIZE = "tokenize"
    AUDIT = "audit"
    NOOP = "noop"


@dataclass
class DetectedEntity:
    type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0
    context: str | None = None


@dataclass
class PrivacyResult:
    masked_text: str
    detected_entities: list[DetectedEntity]
    applied_rules: list[str]
    processing_time: float
    level: PrivacyLevel


class PrivacyEngine:
    """Privacy engine for PII detection and masking"""

    def __init__(self, level: PrivacyLevel = PrivacyLevel.BALANCED):
        self.level = level
        self.patterns = self._load_patterns()
        self.masking_rules = self._load_masking_rules()

    def _load_patterns(self) -> dict[str, dict[str, Any]]:
        """Load PII detection patterns"""
        return {
            "email": {
                "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "description": "Email addresses",
            },
            "phone_us": {
                "pattern": r"\b(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b",
                "description": "US phone numbers",
            },
            "phone_international": {
                "pattern": r"\+\d{1,3}[-.\s]?\d{3,}[-.\s]?\d{3,}[-.\s]?\d{3,}",
                "description": "International phone numbers",
            },
            "ssn": {"pattern": r"\b\d{3}[-]?\d{2}[-]?\d{4}\b", "description": "US Social Security Numbers"},
            "credit_card": {
                "pattern": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
                "description": "Credit card numbers",
            },
            "ip_address": {"pattern": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "description": "IP addresses"},
            "url": {
                "pattern": r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)",
                "description": "URLs",
            },
            "date_of_birth": {"pattern": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", "description": "Dates of birth"},
        }

    def _load_masking_rules(self) -> dict[str, dict[str, Any]]:
        """Load masking rules based on privacy level"""
        rules = {
            PrivacyLevel.STRICT: {
                "email": MaskingStrategy.REDACT,
                "phone_us": MaskingStrategy.REDACT,
                "phone_international": MaskingStrategy.REDACT,
                "ssn": MaskingStrategy.REDACT,
                "credit_card": MaskingStrategy.REDACT,
                "ip_address": MaskingStrategy.REDACT,
                "url": MaskingStrategy.REDACT,
                "date_of_birth": MaskingStrategy.REDACT,
            },
            PrivacyLevel.BALANCED: {
                "email": MaskingStrategy.PARTIAL,
                "phone_us": MaskingStrategy.PARTIAL,
                "phone_international": MaskingStrategy.PARTIAL,
                "ssn": MaskingStrategy.HASH,
                "credit_card": MaskingStrategy.PARTIAL,
                "ip_address": MaskingStrategy.REDACT,
                "url": MaskingStrategy.AUDIT,
                "date_of_birth": MaskingStrategy.PARTIAL,
            },
            PrivacyLevel.MINIMAL: {
                "email": MaskingStrategy.AUDIT,
                "phone_us": MaskingStrategy.AUDIT,
                "phone_international": MaskingStrategy.AUDIT,
                "ssn": MaskingStrategy.REDACT,
                "credit_card": MaskingStrategy.REDACT,
                "ip_address": MaskingStrategy.REDACT,
                "url": MaskingStrategy.NOOP,
                "date_of_birth": MaskingStrategy.AUDIT,
            },
        }
        return rules.get(self.level, rules[PrivacyLevel.BALANCED])

    def detect(self, text: str) -> list[DetectedEntity]:
        """Detect PII entities in text"""
        detected = []
        detected.extend(
            DetectedEntity(
                type=entity_type,
                value=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=1.0,
                context=self._get_context(text, match.start(), match.end()),
            )
            for entity_type, config in self.patterns.items()
            for match in re.finditer(config["pattern"], text, re.IGNORECASE)
        )
        return detected

    def mask_text(self, text: str) -> PrivacyResult:
        """Mask PII entities in text"""
        import time

        start_time = time.time()

        detected_entities = self.detect(text)
        masked_text = text

        # Apply masking in reverse order to maintain positions
        for entity in reversed(detected_entities):
            strategy = self.masking_rules.get(entity.type, MaskingStrategy.AUDIT)
            replacement = self._apply_masking(entity, strategy)
            masked_text = masked_text[: entity.start] + replacement + masked_text[entity.end :]

        processing_time = time.time() - start_time
        applied_rules = [
            f"{entity.type}:{strategy.value}"
            for entity in detected_entities
            for strategy in [self.masking_rules.get(entity.type, MaskingStrategy.AUDIT)]
        ]

        return PrivacyResult(
            masked_text=masked_text,
            detected_entities=detected_entities,
            applied_rules=list(set(applied_rules)),
            processing_time=processing_time,
            level=self.level,
        )

    def _apply_masking(self, entity: DetectedEntity, strategy: MaskingStrategy) -> str:
        """Apply masking strategy to entity"""
        if strategy == MaskingStrategy.REDACT:
            return "[REDACTED]"
        elif strategy == MaskingStrategy.PARTIAL:
            return self._partial_mask(entity.value)
        elif strategy == MaskingStrategy.HASH:
            return self._hash_value(entity.value)
        elif strategy == MaskingStrategy.TOKENIZE:
            return f"[TOKEN_{entity.type.upper()}]"
        elif strategy == MaskingStrategy.AUDIT:
            return f"[AUDIT_{entity.type.upper()}]"
        else:  # NOOP
            return entity.value

    def _partial_mask(self, value: str) -> str:
        """Apply partial masking"""
        if len(value) <= 2:
            return "[PARTIAL]"
        elif "@" in value:  # Email
            parts = value.split("@")
            return f"{parts[0][:2]}***@{parts[1]}"
        elif len(value) >= 10:  # Phone/credit card
            return f"{value[:3]}***{value[-3:]}"
        else:
            return f"{value[0]}***{value[-1]}"

    def _hash_value(self, value: str) -> str:
        """Hash the value"""
        import hashlib

        return hashlib.sha256(value.encode()).hexdigest()[:8]

    def _get_context(self, text: str, start: int, end: int, window: int = 20) -> str:
        """Get context around entity"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()

    def batch_process(self, texts: list[str]) -> list[PrivacyResult]:
        """Process multiple texts"""
        return [self.mask_text(text) for text in texts]
