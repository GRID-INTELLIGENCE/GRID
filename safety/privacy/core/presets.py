from enum import Enum
from typing import Any

from safety.privacy.core.types import PrivacyAction


class PrivacyPreset(str, Enum):
    """Pre-configured privacy settings."""

    BALANCED = "balanced"  # Default: Ask user, good coverage
    STRICT = "strict"  # Block/Mask everything
    MINIMAL = "minimal"  # Only critical secrets
    GDPR_COMPLIANT = "gdpr"  # EU privacy standards
    HIPAA_COMPLIANT = "hipaa"  # Healthcare standards
    PCI_COMPLIANT = "pci"  # Payment card standards
    COLLABORATIVE = "collaborative"  # Team workspace: Balanced with audit logging


def get_preset_config(preset: PrivacyPreset) -> dict[str, Any]:
    """
    Get configuration dictionary for a privacy preset.

    Args:
        preset: PrivacyPreset enum value

    Returns:
        Dictionary with PrivacyConfig parameters
    """
    # Common PII types
    identifiers = ["EMAIL", "PHONE_US", "IP_ADDRESS", "IPV6", "US_ZIP", "DATE_MDY"]
    financial = ["CREDIT_CARD", "IBAN"]
    secrets = ["AWS_KEY", "API_KEY", "PASSWORD", "PRIVATE_KEY", "SSN"]

    all_patterns = identifiers + financial + secrets

    if preset == PrivacyPreset.STRICT:
        return {
            "enable_detection": True,
            "enabled_patterns": all_patterns,
            "default_action": PrivacyAction.MASK,
            "enable_cache": True,
        }

    elif preset == PrivacyPreset.MINIMAL:
        return {
            "enable_detection": True,
            "enabled_patterns": secrets,
            "default_action": PrivacyAction.BLOCK,  # Block leaks of secrets
            "enable_cache": True,
        }

    elif preset == PrivacyPreset.GDPR_COMPLIANT:
        return {
            "enable_detection": True,
            "enabled_patterns": identifiers + financial + ["SSN"],
            "default_action": PrivacyAction.ASK,
            "per_type_actions": {
                "EMAIL": PrivacyAction.MASK,
                "PHONE_US": PrivacyAction.MASK,
                "IP_ADDRESS": PrivacyAction.MASK,
                "IPV6": PrivacyAction.MASK,
            },
            "enable_cache": True,
        }

    elif preset == PrivacyPreset.HIPAA_COMPLIANT:
        # HIPAA requires strict protection of PHI (Identifiers + Dates)
        return {
            "enable_detection": True,
            "enabled_patterns": identifiers + ["SSN", "DATE_MDY"],
            "default_action": PrivacyAction.MASK,
            "enable_cache": True,
        }

    elif preset == PrivacyPreset.PCI_COMPLIANT:
        # PCI DSS focuses on cardholder data
        return {
            "enable_detection": True,
            "enabled_patterns": financial,
            "default_action": PrivacyAction.MASK,
            "per_type_actions": {
                "CREDIT_CARD": PrivacyAction.MASK,  # Must mask PAN
                "IBAN": PrivacyAction.MASK,
            },
            "enable_cache": True,
        }

    elif preset == PrivacyPreset.COLLABORATIVE:
        # Collaborative workspace: Balanced settings with enhanced audit
        return {
            "enable_detection": True,
            "enabled_patterns": all_patterns,
            "default_action": PrivacyAction.ASK,  # Ask for team consensus
            "per_type_actions": {
                "PASSWORD": PrivacyAction.BLOCK,
                "PRIVATE_KEY": PrivacyAction.BLOCK,
                "AWS_KEY": PrivacyAction.BLOCK,
                "API_KEY": PrivacyAction.BLOCK,
            },
            "enable_cache": True,
            "cache_ttl": 7200,  # Longer cache for collaborative contexts
        }

    else:  # PrivacyPreset.BALANCED (Default)
        return {
            "enable_detection": True,
            "enabled_patterns": all_patterns,
            "default_action": PrivacyAction.ASK,
            "per_type_actions": {
                "PASSWORD": PrivacyAction.BLOCK,
                "PRIVATE_KEY": PrivacyAction.BLOCK,
                "AWS_KEY": PrivacyAction.BLOCK,
                "API_KEY": PrivacyAction.BLOCK,
            },
            "enable_cache": True,
        }
