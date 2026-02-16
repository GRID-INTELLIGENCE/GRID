from __future__ import annotations

import logging
import os
from typing import Optional

from .environment import environment_settings
from .path_manager import PathManagerReport, PathValidationResult, SecurePathManager
from .path_validator import PathValidator, SecurityError
from .production import Environment, ProductionSecurityManager, security_manager
from .secrets import Secret, SecretsManager, get_secrets_manager, initialize_secrets_manager
from .startup import (
    ENABLE_HARDENING,
    EnvironmentReport,
    HardeningLevel,
    get_environment_status,
    get_hardening_level,
    harden_environment,
    should_harden_environment,
)
from .templates import (
    DEVELOPMENT_CONFIG,
    PRODUCTION_CONFIG,
    STAGING_CONFIG,
    generate_env_file,
    generate_kubernetes_manifests,
)

# Import new threat profile and hardened security components
try:
    from .hardened_middleware import (
        AdaptiveRateLimiter,
        HardenedInputValidator,
        HardenedSecurityMiddleware,
        SecurityContext,
        ThreatResponseHandler,
        add_hardened_security,
        get_security_context,
        security_context_manager,
        set_security_context,
    )
    from .security_runner import (
        ComplianceChecker,
        SecurityValidator,
        ValidationReport,
        ValidationResult,
        ValidationStatus,
        run_compliance_check,
        run_security_validation,
    )
    from .threat_profile import (
        DetectionThreshold,
        MitigationAction,
        MitigationRule,
        MitigationStrategies,
        PreventionFramework,
        SecurityAssertion,
        SecurityGuardrails,
        ThreatCategory,
        ThreatIndicator,
        ThreatProfile,
        ThreatSeverity,
        check_threat,
        get_guardrails,
        get_mitigation_strategies,
        get_prevention_framework,
        get_threat_profile,
    )
    from .threat_profile import (
        get_security_status as get_comprehensive_security_status,
    )
    from .threat_profile import (
        initialize_security as initialize_threat_profile,
    )

    THREAT_PROFILE_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Threat profile components not available: {e}")
    THREAT_PROFILE_AVAILABLE = False

# Import local secrets manager
try:
    from .audit_logger import AuditEventType, AuditLogger, get_audit_logger, initialize_audit_logger
    from .encryption import DataEncryption, generate_encryption_key, initialize_encryption
    from .gcp_secrets import GCPSecretsProvider, get_gcp_provider
    from .local_secrets_manager import LocalSecretsManager, get_local_secrets_manager
    from .pii_redaction import PIIRedactor, RedactionMode, get_redactor, redact_log_message

    LOCAL_SECRETS_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Local secrets manager not available: {e}")
    LOCAL_SECRETS_AVAILABLE = False

logger = logging.getLogger(__name__)


def initialize_security() -> bool:
    """Initialize security system based on environment."""
    try:
        # Initialize secrets manager (includes local-first approach)
        initialize_secrets_manager()

        # Validate security configuration
        validation = security_manager.validate_environment()

        if not validation["valid"]:
            logger.error("Security validation failed:")
            for issue in validation["issues"]:
                logger.error(f"  - {issue}")
            return False

        if validation["warnings"]:
            logger.warning("Security warnings:")
            for warning in validation["warnings"]:
                logger.warning(f"  - {warning}")

        logger.info(f"Security initialized for {environment_settings.MOTHERSHIP_ENVIRONMENT} environment")
        logger.info(f"Security level: {security_manager.config.security_level.value}")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize security: {e}")
        return False


def get_security_status() -> dict:
    """Get current security status and configuration."""
    return {
        "environment": security_manager.environment.value,
        "security_level": security_manager.config.security_level.value,
        "denylisted_commands": security_manager.config.denylisted_commands,
        "min_contribution_score": security_manager.config.min_contribution_score,
        "check_contribution": security_manager.config.check_contribution,
        "use_secrets_manager": security_manager.config.use_secrets_manager,
        "secrets_provider": security_manager.config.secrets_provider,
        "enable_audit_logging": security_manager.config.enable_audit_logging,
        "validation": security_manager.validate_environment(),
    }


def generate_deployment_configs() -> None:
    """Generate all deployment configuration templates."""
    try:
        # Generate environment files
        generate_env_file(DEVELOPMENT_CONFIG, ".env.development")
        generate_env_file(STAGING_CONFIG, ".env.staging")
        generate_env_file(PRODUCTION_CONFIG, ".env.production")

        # Generate Kubernetes manifests
        from .templates import KUBERNETES_CONFIG

        generate_kubernetes_manifests(KUBERNETES_CONFIG, "k8s/")

        logger.info("Deployment configuration templates generated successfully")

    except Exception as e:
        logger.error(f"Failed to generate deployment configs: {e}")


# Auto-initialize on import
_security_initialized = False


def ensure_security_initialized() -> None:
    """Ensure security system is initialized."""
    global _security_initialized
    if not _security_initialized:
        _security_initialized = initialize_security()


# Export key components
__all__ = [
    # Core security
    "ProductionSecurityManager",
    "security_manager",
    "Environment",
    "SecretsManager",
    "get_secrets_manager",
    "initialize_secrets_manager",
    "Secret",
    # Local secrets
    "LocalSecretsManager",
    "get_local_secrets_manager",
    "set_local_secret",
    "get_local_secret",
    "LOCAL_SECRETS_AVAILABLE",
    # GCP secrets
    "GCPSecretsProvider",
    "get_gcp_provider",
    # PII redaction
    "PIIRedactor",
    "get_redactor",
    "redact_log_message",
    "RedactionMode",
    # Audit logging
    "AuditLogger",
    "AuditEventType",
    "get_audit_logger",
    "initialize_audit_logger",
    # Encryption
    "DataEncryption",
    "generate_encryption_key",
    "initialize_encryption",
    "environment_settings",
    # Templates
    "DEVELOPMENT_CONFIG",
    "PRODUCTION_CONFIG",
    "STAGING_CONFIG",
    "generate_env_file",
    "generate_kubernetes_manifests",
    # Path management
    "SecurePathManager",
    "PathManagerReport",
    "PathValidationResult",
    "PathValidator",
    "SecurityError",
    # Startup hardening
    "harden_environment",
    "EnvironmentReport",
    "HardeningLevel",
    "get_environment_status",
    "get_hardening_level",
    "should_harden_environment",
    "ENABLE_HARDENING",
    # Threat Profile (NEW)
    "ThreatProfile",
    "ThreatSeverity",
    "ThreatCategory",
    "ThreatIndicator",
    "SecurityGuardrails",
    "DetectionThreshold",
    "MitigationStrategies",
    "MitigationAction",
    "MitigationRule",
    "PreventionFramework",
    "SecurityAssertion",
    "get_threat_profile",
    "get_guardrails",
    "get_mitigation_strategies",
    "get_prevention_framework",
    "check_threat",
    "get_comprehensive_security_status",
    "initialize_threat_profile",
    "THREAT_PROFILE_AVAILABLE",
    # Hardened Middleware (NEW)
    "HardenedSecurityMiddleware",
    "SecurityContext",
    "ThreatResponseHandler",
    "AdaptiveRateLimiter",
    "HardenedInputValidator",
    "add_hardened_security",
    "get_security_context",
    "set_security_context",
    "security_context_manager",
    # Security Validation (NEW)
    "SecurityValidator",
    "ValidationStatus",
    "ValidationResult",
    "ValidationReport",
    "ComplianceChecker",
    "run_security_validation",
    "run_compliance_check",
    # General
    "initialize_security",
    "get_security_status",
    "generate_deployment_configs",
    "ensure_security_initialized",
]
