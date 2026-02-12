from __future__ import annotations

import logging
import os
from typing import Optional

from .production import Environment, ProductionSecurityManager, security_manager
from .secrets import Secret, SecretsManager, get_secrets_manager, initialize_secrets_manager
from .templates import (
    DEVELOPMENT_CONFIG,
    PRODUCTION_CONFIG,
    STAGING_CONFIG,
    generate_docker_compose,
    generate_env_file,
    generate_kubernetes_manifests,
)

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
        # Detect environment
        environment = os.getenv("GRID_ENV", "development").lower()

        # Initialize secrets manager (includes local-first approach)
        initialize_secrets_manager(environment)

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

        logger.info(f"Security initialized for {environment} environment")
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

        # Generate Docker configuration
        from .templates import DOCKER_PRODUCTION_CONFIG

        generate_docker_compose(DOCKER_PRODUCTION_CONFIG, "docker-compose.prod.yml")

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
    # Templates
    "DEVELOPMENT_CONFIG",
    "PRODUCTION_CONFIG",
    "STAGING_CONFIG",
    "generate_docker_compose",
    "generate_env_file",
    "generate_kubernetes_manifests",
    # General
    "initialize_security",
    "get_security_status",
    "generate_deployment_configs",
    "ensure_security_initialized",
]
