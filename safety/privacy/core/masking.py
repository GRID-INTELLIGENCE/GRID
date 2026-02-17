"""
Masking strategies for PII redaction.

Provides multiple redaction approaches with compliance presets.
Supports GDPR, HIPAA, and custom configurations.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable

# (Fixed: removed redundant/duplicated _hash_value)


class MaskStrategyType(StrEnum):
    """Types of masking strategies available."""

    REDACT = "redact"  # Replace with [TYPE]
    PARTIAL = "partial"  # Partial reveal (first/last chars)
    HASH = "hash"  # One-way hash
    TOKENIZE = "tokenize"  # Replace with placeholder token
    AUDIT = "audit"  # Replace with audit reference
    NOOP = "noop"  # No masking (for testing)


def _hash_value(value: str) -> str:
    """One-way hash of a PII value. Never store the plaintext."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


@dataclass
class MaskResult:
    """Result of a masking operation.

    ``original_hash`` stores a truncated SHA-256 of the original text so that
    results can be correlated without retaining plaintext PII.
    """

    original_hash: str
    masked: str
    replacements: list[dict[str, Any]] = field(default_factory=list)
    strategy_used: MaskStrategyType = MaskStrategyType.REDACT


class MaskingStrategy(ABC):
    """Base class for masking strategies."""

    @abstractmethod
    def mask(self, value: str, pii_type: str, **kwargs) -> MaskResult:
        """Apply masking to a value."""
        pass

    @abstractmethod
    def get_strategy_type(self) -> MaskStrategyType:
        """Return the strategy type."""
        pass


class RedactStrategy(MaskingStrategy):
    """Replace PII with [TYPE] format."""

    def mask(self, value: str, pii_type: str, **kwargs) -> MaskResult:
        return MaskResult(
            original_hash=_hash_value(value),
            masked=f"[{pii_type}]",
            replacements=[{"type": pii_type, "replacement": f"[{pii_type}]"}],
            strategy_used=self.get_strategy_type(),
        )

    def get_strategy_type(self) -> MaskStrategyType:
        return MaskStrategyType.REDACT


class PartialMaskStrategy(MaskingStrategy):
    """Partially reveal characters (e.g., j***@email.com)."""

    def __init__(self, reveal_chars: int = 3):
        self.reveal_chars = reveal_chars

    def mask(self, value: str, pii_type: str, **kwargs) -> MaskResult:
        value_len = len(value)

        if value_len <= self.reveal_chars:
            # Too short, redact completely
            return RedactStrategy().mask(value, pii_type)

        # Partial reveal based on type
        if "@" in value and pii_type in ("EMAIL",):
            # Email: show first part of local, full domain
            parts = value.split("@", 1)
            local = parts[0]
            domain = parts[1] if len(parts) > 1 else ""

            if len(local) <= 3:
                masked_local = local[0] + "*" * (len(local) - 1)
            else:
                masked_local = local[: self.reveal_chars] + "*" * (len(local) - self.reveal_chars)

            masked = f"{masked_local}@{domain}"

        elif pii_type in ("PHONE", "SSN"):
            # Phone/SSN: show last 4
            visible = value[-4:] if len(value) >= 4 else value
            masked = "*" * (len(value) - len(visible)) + visible

        else:
            # Default: show first and last chars
            if value_len <= 4:
                masked = "*" * value_len
            else:
                masked = value[0] + "*" * (value_len - 2) + value[-1]

        return MaskResult(
            original_hash=_hash_value(value),
            masked=masked,
            replacements=[{"type": pii_type, "replacement": masked}],
            strategy_used=self.get_strategy_type(),
        )

    def get_strategy_type(self) -> MaskStrategyType:
        return MaskStrategyType.PARTIAL


class HashStrategy(MaskingStrategy):
    """Replace with one-way hash for audit trails."""

    def __init__(self, salt: str = ""):
        self.salt = salt

    def mask(self, value: str, pii_type: str, **kwargs) -> MaskResult:
        to_hash = f"{self.salt}{value}".encode()
        hashed = hashlib.sha256(to_hash).hexdigest()[:16]

        return MaskResult(
            original_hash=_hash_value(value),
            masked=f"[{pii_type}_HASH:{hashed}]",
            replacements=[{"type": pii_type, "hash": hashed}],
            strategy_used=self.get_strategy_type(),
        )

    def get_strategy_type(self) -> MaskStrategyType:
        return MaskStrategyType.HASH


class TokenizeStrategy(MaskingStrategy):
    """Replace with a consistent token for correlation."""

    def __init__(self):
        # Key by hash of original value to prevent reversibility
        self._token_cache: dict[str, str] = {}

    def mask(self, value: str, pii_type: str, **kwargs) -> MaskResult:
        # Hash the value for cache lookup — never store plaintext
        value_hash = hashlib.sha256(value.encode()).hexdigest()[:16]

        if value_hash in self._token_cache:
            token = self._token_cache[value_hash]
        else:
            # Generate new token
            idx = len(self._token_cache) + 1
            token = f"[{pii_type}_TOKEN:{idx:06d}]"
            self._token_cache[value_hash] = token

        return MaskResult(
            original_hash=_hash_value(value),
            masked=token,
            replacements=[{"type": pii_type, "token": token, "original_hash": value_hash}],
            strategy_used=self.get_strategy_type(),
        )

    def get_strategy_type(self) -> MaskStrategyType:
        return MaskStrategyType.TOKENIZE


class AuditStrategy(MaskingStrategy):
    """Replace with audit reference for compliance logging."""

    def __init__(self):
        self._audit_counter = 0

    def mask(self, value: str, pii_type: str, **kwargs) -> MaskResult:
        self._audit_counter += 1
        audit_id = f"REF-{self._audit_counter:08d}"
        value_hash = hashlib.sha256(value.encode()).hexdigest()[:16]

        return MaskResult(
            original_hash=_hash_value(value),
            masked=f"[{pii_type}_AUDIT:{audit_id}]",
            replacements=[{"type": pii_type, "audit_ref": audit_id, "original_hash": value_hash}],
            strategy_used=self.get_strategy_type(),
        )

    def get_strategy_type(self) -> MaskStrategyType:
        return MaskStrategyType.AUDIT


class NoopStrategy(MaskingStrategy):
    """No masking - for testing/development."""

    def mask(self, value: str, pii_type: str, **kwargs) -> MaskResult:
        return MaskResult(
            original_hash=_hash_value(value),
            masked=value,
            replacements=[],
            strategy_used=self.get_strategy_type(),
        )

    def get_strategy_type(self) -> MaskStrategyType:
        return MaskStrategyType.NOOP


# Strategy factory
_STRATEGIES: dict[MaskStrategyType, Callable[[], MaskingStrategy]] = {
    MaskStrategyType.REDACT: RedactStrategy,
    MaskStrategyType.PARTIAL: lambda: PartialMaskStrategy(),
    MaskStrategyType.HASH: lambda: HashStrategy(),
    MaskStrategyType.TOKENIZE: lambda: TokenizeStrategy(),
    MaskStrategyType.AUDIT: lambda: AuditStrategy(),
    MaskStrategyType.NOOP: lambda: NoopStrategy(),
}


def get_strategy(strategy_type: MaskStrategyType) -> MaskingStrategy:
    """Get a masking strategy instance by type."""
    factory = _STRATEGIES.get(strategy_type)
    if factory is None:
        return RedactStrategy()
    return factory()


class MaskingEngine:
    """
    Main masking engine that applies strategies to detected PII.

    Supports per-type strategy configuration and compliance presets.
    """

    def __init__(
        self,
        default_strategy: MaskStrategyType = MaskStrategyType.REDACT,
        strategy_overrides: dict[str, MaskStrategyType] | None = None,
    ):
        self._default_strategy = default_strategy
        self._strategy_overrides = strategy_overrides or {}

        # Create strategy instances
        self._strategy_cache: dict[MaskStrategyType, MaskingStrategy] = {}

    def _get_strategy(self, pii_type: str) -> MaskingStrategy:
        """Get strategy for a PII type."""
        strategy_type = self._strategy_overrides.get(
            pii_type,
            self._default_strategy,
        )

        if strategy_type not in self._strategy_cache:
            self._strategy_cache[strategy_type] = get_strategy(strategy_type)

        return self._strategy_cache[strategy_type]

    def mask_text(
        self,
        text: str,
        detections: list[dict[str, Any]],
    ) -> MaskResult:
        """
        Mask all detected PII in text.

        Args:
            text: The text containing PII
            detections: List of detection results from AsyncPIIDetector

        Returns:
            MaskResult with masked text and all replacements
        """
        if not detections:
            return MaskResult(
                original_hash=_hash_value(text),
                masked=text,
                replacements=[],
            )

        # Sort by position (reverse) to mask from end to start
        # This preserves position indices for earlier detections
        sorted_detections = sorted(
            detections,
            key=lambda d: d.get("start", 0),
            reverse=True,
        )

        masked_text = text
        all_replacements = []

        for detection in sorted_detections:
            pii_type = detection.get("pii_type", "UNKNOWN")
            start = detection.get("start", 0)
            end = detection.get("end", len(text))
            value = detection.get("value", "")

            if start >= len(text) or end > len(text):
                continue

            strategy = self._get_strategy(pii_type)
            result = strategy.mask(value, pii_type)

            # Replace in text
            masked_text = masked_text[:start] + result.masked + masked_text[end:]
            all_replacements.extend(result.replacements)

        # Re-sort replacements by original position
        all_replacements.sort(key=lambda r: text.find(r.get("replacement", "")))

        return MaskResult(
            original_hash=_hash_value(text),
            masked=masked_text,
            replacements=all_replacements,
        )

    def mask_single(
        self,
        value: str,
        pii_type: str,
    ) -> MaskResult:
        """Mask a single value."""
        strategy = self._get_strategy(pii_type)
        return strategy.mask(value, pii_type)


# Compliance preset configurations
class CompliancePreset(StrEnum):
    """Compliance presets for common regulations."""

    GDPR = "gdpr"  # EU General Data Protection
    HIPAA = "hipaa"  # US Health Insurance Portability
    PCI_DSS = "pci_dss"  # Payment Card Industry
    SOC2 = "soc2"  # Service Organization Control
    LGPD = "lgpd"  # Brazil General Data Protection Law
    CCPA = "ccpa"  # California Consumer Privacy Act
    CUSTOM = "custom"


# Default strategy mappings per compliance preset
_GDPR_STRATEGIES: dict[str, MaskStrategyType] = {
    "EMAIL": MaskStrategyType.PARTIAL,
    "PHONE": MaskStrategyType.PARTIAL,
    "SSN": MaskStrategyType.AUDIT,
    "CREDIT_CARD": MaskStrategyType.HASH,
    "IP_ADDRESS": MaskStrategyType.REDACT,
    "DATE": MaskStrategyType.REDACT,
    "NAME": MaskStrategyType.PARTIAL,
    "ADDRESS": MaskStrategyType.REDACT,
    "IBAN": MaskStrategyType.HASH,
    "AWS_KEY": MaskStrategyType.REDACT,
    "API_KEY": MaskStrategyType.REDACT,
    "PASSWORD": MaskStrategyType.REDACT,
    "PRIVATE_KEY": MaskStrategyType.REDACT,
}

_HIPAA_STRATEGIES: dict[str, MaskStrategyType] = {
    "EMAIL": MaskStrategyType.AUDIT,
    "PHONE": MaskStrategyType.AUDIT,
    "SSN": MaskStrategyType.AUDIT,
    "DATE": MaskStrategyType.PARTIAL,  # Keep partial for medical records
    "NAME": MaskStrategyType.AUDIT,
    "ADDRESS": MaskStrategyType.AUDIT,
    "MEDICAL_RECORD": MaskStrategyType.AUDIT,
    "INSURANCE": MaskStrategyType.AUDIT,
    "DIAGNOSIS": MaskStrategyType.AUDIT,
}

_PCI_DSS_STRATEGIES: dict[str, MaskStrategyType] = {
    "CREDIT_CARD": MaskStrategyType.PARTIAL,  # Show last 4 only
    "SSN": MaskStrategyType.REDACT,
}

_SOC2_STRATEGIES: dict[str, MaskStrategyType] = {
    "PASSWORD": MaskStrategyType.REDACT,
    "PRIVATE_KEY": MaskStrategyType.REDACT,
    "API_KEY": MaskStrategyType.REDACT,
    "SECRET": MaskStrategyType.REDACT,
}

_COMPLIANCE_STRATEGIES: dict[CompliancePreset, dict[str, MaskStrategyType]] = {
    CompliancePreset.GDPR: _GDPR_STRATEGIES,
    CompliancePreset.HIPAA: _HIPAA_STRATEGIES,
    CompliancePreset.PCI_DSS: _PCI_DSS_STRATEGIES,
    CompliancePreset.SOC2: _SOC2_STRATEGIES,
    CompliancePreset.LGPD: _GDPR_STRATEGIES,  # Similar to GDPR
    CompliancePreset.CCPA: _GDPR_STRATEGIES,
    CompliancePreset.CUSTOM: {},
}


def create_compliance_engine(
    preset: CompliancePreset,
    custom_overrides: dict[str, MaskStrategyType] | None = None,
) -> MaskingEngine:
    """
    Create a masking engine configured for a compliance preset.

    Args:
        preset: The compliance preset to use
        custom_overrides: Optional custom strategy overrides

    Returns:
        Configured MaskingEngine
    """
    strategies = _COMPLIANCE_STRATEGIES.get(preset, {})

    if custom_overrides:
        strategies = {**strategies, **custom_overrides}

    return MaskingEngine(
        default_strategy=MaskStrategyType.REDACT,
        strategy_overrides=strategies,
    )


# Global engines for common presets
_gdpr_engine: MaskingEngine | None = None
_hipaa_engine: MaskingEngine | None = None


def get_gdpr_engine() -> MaskingEngine:
    """Get GDPR-compliant masking engine."""
    global _gdpr_engine
    if _gdpr_engine is None:
        _gdpr_engine = create_compliance_engine(CompliancePreset.GDPR)
    return _gdpr_engine


def get_hipaa_engine() -> MaskingEngine:
    """Get HIPAA-compliant masking engine."""
    global _hipaa_engine
    if _hipaa_engine is None:
        _hipaa_engine = create_compliance_engine(CompliancePreset.HIPAA)
    return _hipaa_engine
