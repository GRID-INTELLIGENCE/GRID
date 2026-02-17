"""
Security module for Mothership Cockpit.

Provides JWT authentication, secret validation, RBAC, and API security utilities.
Implements deny-by-default security posture with factory defaults enforcement.
"""

from .api_sentinels import (
    API_DEFAULTS,
    THREAT_PATTERNS,
    APISecurityDefaults,
    # Enums
    AuthLevel,
    # Defaults
    EndpointSecurityConfig,
    InputSanitizer,
    SanitizationAction,
    SanitizationResult,
    # Verification
    SecurityAuditResult,
    SQLiFilter,
    ThreatCategory,
    # Sanitization
    ThreatPattern,
    XSSDetector,
    apply_security_defaults,
    audit_endpoint_security,
    get_api_defaults,
    verify_api_against_defaults,
)
from .defaults import (
    SecurityDefaults,
    get_security_defaults,
)
from .jwt import (
    JWTManager,
    TokenPair,
    TokenPayload,
    get_jwt_manager,
    reset_jwt_manager,
)
from .rbac import (
    Permission,
    Role,
    get_permissions_for_role,
    has_permission,
)
from .secret_validation import (
    MIN_SECRET_LENGTH,
    RECOMMENDED_SECRET_LENGTH,
    SecretStrength,
    SecretValidationError,
    generate_secure_secret,
    get_secret_from_env,
    mask_secret,
    validate_secret_strength,
)

__all__ = [
    # JWT
    "JWTManager",
    "TokenPair",
    "TokenPayload",
    "get_jwt_manager",
    "reset_jwt_manager",
    # Secret validation
    "SecretValidationError",
    "SecretStrength",
    "generate_secure_secret",
    "validate_secret_strength",
    "get_secret_from_env",
    "mask_secret",
    "MIN_SECRET_LENGTH",
    "RECOMMENDED_SECRET_LENGTH",
    # RBAC
    "Role",
    "Permission",
    "get_permissions_for_role",
    "has_permission",
    # API Sentinels - Enums
    "AuthLevel",
    "ThreatCategory",
    "SanitizationAction",
    # API Sentinels - Sanitization
    "ThreatPattern",
    "THREAT_PATTERNS",
    "SanitizationResult",
    "InputSanitizer",
    "SQLiFilter",
    "XSSDetector",
    # API Sentinels - Defaults
    "EndpointSecurityConfig",
    "APISecurityDefaults",
    "API_DEFAULTS",
    "get_api_defaults",
    "apply_security_defaults",
    # API Sentinels - Verification
    "SecurityAuditResult",
    "audit_endpoint_security",
    "verify_api_against_defaults",
    # Security Defaults
    "SecurityDefaults",
    "get_security_defaults",
]
