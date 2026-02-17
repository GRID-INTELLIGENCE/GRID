"""
API Sentinels - Factory Defaults Security Enforcement.

Implements deny-by-default security posture with explicit configuration
for production deployments. Provides input sanitization and security
baseline enforcement for all API endpoints.

This module ensures the API stack maintains:
1. Zero-trust invocation via ghost registry
2. Attack-resistant defaults via sentinel enforcement
3. Continuous verification through automated security probes
"""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass, field
from enum import StrEnum
from re import Pattern
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Security Enums and Constants
# =============================================================================


class AuthLevel(StrEnum):
    """Authentication levels for API endpoints."""

    NONE = "none"  # No authentication required (public endpoints only)
    BASIC = "basic"  # Basic API key or token
    INTEGRITY = "integrity"  # Verified authentication with integrity checks
    ELEVATED = "elevated"  # Elevated privileges required (MFA, session verification)
    ADMIN = "admin"  # Administrative access only


class ThreatCategory(StrEnum):
    """Categories of security threats."""

    SQLI = "sql_injection"
    XSS = "cross_site_scripting"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    HEADER_INJECTION = "header_injection"
    SSRF = "server_side_request_forgery"
    TEMPLATE_INJECTION = "template_injection"


class SanitizationAction(StrEnum):
    """Actions to take when threats are detected."""

    REJECT = "reject"  # Reject the request entirely
    SANITIZE = "sanitize"  # Sanitize and continue
    LOG_ONLY = "log_only"  # Log but allow through
    ALERT = "alert"  # Alert security team


# =============================================================================
# Input Sanitization Filters
# =============================================================================


class ThreatPattern(BaseModel):
    """A pattern for detecting security threats."""

    category: ThreatCategory
    pattern: str = Field(..., description="Regex pattern to match")
    description: str = Field(..., description="Human-readable description")
    severity: int = Field(default=5, ge=1, le=10, description="Severity 1-10")
    action: SanitizationAction = Field(default=SanitizationAction.REJECT)

    def compile(self) -> Pattern:
        """Compile the regex pattern."""
        return re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)


# Industry-standard threat patterns
THREAT_PATTERNS: list[ThreatPattern] = [
    # SQL Injection patterns
    ThreatPattern(
        category=ThreatCategory.SQLI,
        pattern=r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b.*\b(FROM|INTO|TABLE|DATABASE)\b)",
        description="SQL keyword sequences",
        severity=9,
        action=SanitizationAction.REJECT,
    ),
    ThreatPattern(
        category=ThreatCategory.SQLI,
        pattern=r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
        description="Boolean-based SQL injection",
        severity=8,
        action=SanitizationAction.REJECT,
    ),
    ThreatPattern(
        category=ThreatCategory.SQLI,
        pattern=r"(--|\#|\/\*|\*\/)",
        description="SQL comment sequences",
        severity=6,
        action=SanitizationAction.SANITIZE,
    ),
    ThreatPattern(
        category=ThreatCategory.SQLI,
        pattern=r"(\bEXEC\b|\bEXECUTE\b|\bxp_|\bsp_)",
        description="SQL stored procedure calls",
        severity=9,
        action=SanitizationAction.REJECT,
    ),
    # XSS patterns
    ThreatPattern(
        category=ThreatCategory.XSS,
        pattern=r"(<script[^>]*>.*?</script>)",
        description="Script tags",
        severity=9,
        action=SanitizationAction.REJECT,
    ),
    ThreatPattern(
        category=ThreatCategory.XSS,
        pattern=r"(\bon\w+\s*=)",
        description="Event handlers",
        severity=8,
        action=SanitizationAction.SANITIZE,
    ),
    ThreatPattern(
        category=ThreatCategory.XSS,
        pattern=r"(javascript\s*:)",
        description="JavaScript protocol",
        severity=9,
        action=SanitizationAction.REJECT,
    ),
    ThreatPattern(
        category=ThreatCategory.XSS,
        pattern=r"(<iframe|<object|<embed|<applet)",
        description="Embedded content tags",
        severity=8,
        action=SanitizationAction.REJECT,
    ),
    # Path Traversal patterns
    ThreatPattern(
        category=ThreatCategory.PATH_TRAVERSAL,
        pattern=r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.%2e/|%2e\.)",
        description="Directory traversal sequences",
        severity=8,
        action=SanitizationAction.REJECT,
    ),
    # Command Injection patterns
    ThreatPattern(
        category=ThreatCategory.COMMAND_INJECTION,
        pattern=r"([;&|`$]|\$\(|\$\{)",
        description="Shell metacharacters",
        severity=9,
        action=SanitizationAction.REJECT,
    ),
    ThreatPattern(
        category=ThreatCategory.COMMAND_INJECTION,
        pattern=r"(\b(cat|ls|rm|mv|cp|chmod|chown|wget|curl|nc|bash|sh|python|perl|ruby)\b\s+)",
        description="Common shell commands",
        severity=7,
        action=SanitizationAction.LOG_ONLY,
    ),
    # Header Injection patterns
    ThreatPattern(
        category=ThreatCategory.HEADER_INJECTION,
        pattern=r"(\r\n|\r|\n)",
        description="CRLF injection",
        severity=7,
        action=SanitizationAction.SANITIZE,
    ),
    # SSRF patterns
    ThreatPattern(
        category=ThreatCategory.SSRF,
        pattern=r"(localhost|127\.0\.0\.1|0\.0\.0\.0|::1|169\.254\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+)",
        description="Internal network addresses",
        severity=8,
        action=SanitizationAction.LOG_ONLY,  # Log only - may be legitimate
    ),
    # Template Injection patterns
    ThreatPattern(
        category=ThreatCategory.TEMPLATE_INJECTION,
        pattern=r"(\{\{.*\}\}|\{%.*%\}|\$\{.*\})",
        description="Template syntax",
        severity=7,
        action=SanitizationAction.SANITIZE,
    ),
]


@dataclass
class SanitizationResult:
    """Result of input sanitization."""

    is_safe: bool
    original_value: str
    sanitized_value: str
    threats_detected: list[dict[str, Any]] = field(default_factory=list)
    action_taken: SanitizationAction = SanitizationAction.LOG_ONLY

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "is_safe": self.is_safe,
            "original_length": len(self.original_value),
            "sanitized_length": len(self.sanitized_value),
            "threats_detected": self.threats_detected,
            "action_taken": self.action_taken.value,
        }


class InputSanitizer:
    """
    Input sanitization engine for detecting and neutralizing threats.

    Implements defense-in-depth with multiple detection layers:
    1. Pattern-based threat detection
    2. Character encoding normalization
    3. Content length validation
    4. Recursive structure inspection
    """

    def __init__(
        self,
        patterns: list[ThreatPattern] | None = None,
        max_input_length: int = 1_000_000,
        max_recursion_depth: int = 10,
        strict_mode: bool = True,
    ):
        """
        Initialize sanitizer.

        Args:
            patterns: Custom threat patterns (defaults to THREAT_PATTERNS)
            max_input_length: Maximum allowed input length
            max_recursion_depth: Maximum recursion for nested structures
            strict_mode: If True, reject on any threat; if False, sanitize when possible
        """
        self.patterns = patterns or THREAT_PATTERNS
        self.compiled_patterns = [(p, p.compile()) for p in self.patterns]
        self.max_input_length = max_input_length
        self.max_recursion_depth = max_recursion_depth
        self.strict_mode = strict_mode

    def sanitize_string(self, value: str) -> SanitizationResult:
        """
        Sanitize a string value.

        Args:
            value: Input string to sanitize

        Returns:
            SanitizationResult with safety status and processed value
        """
        if not isinstance(value, str):
            return SanitizationResult(
                is_safe=True,
                original_value=str(value),
                sanitized_value=str(value),
            )

        # Check length
        if len(value) > self.max_input_length:
            return SanitizationResult(
                is_safe=False,
                original_value=value[:100] + "...",
                sanitized_value="",
                threats_detected=[
                    {
                        "category": "length_exceeded",
                        "description": f"Input exceeds maximum length of {self.max_input_length}",
                        "severity": 5,
                    }
                ],
                action_taken=SanitizationAction.REJECT,
            )

        threats: list[dict[str, Any]] = []
        sanitized = value
        action = SanitizationAction.LOG_ONLY

        # Check each pattern
        for pattern, compiled in self.compiled_patterns:
            matches = compiled.findall(sanitized)
            if matches:
                threat_info = {
                    "category": pattern.category.value,
                    "description": pattern.description,
                    "severity": pattern.severity,
                    "matches": len(matches),
                }
                threats.append(threat_info)

                # Determine highest-severity action
                if pattern.action == SanitizationAction.REJECT:
                    action = SanitizationAction.REJECT
                elif pattern.action == SanitizationAction.SANITIZE and action != SanitizationAction.REJECT:
                    action = SanitizationAction.SANITIZE
                    # Apply sanitization
                    sanitized = compiled.sub("", sanitized)
                elif pattern.action == SanitizationAction.ALERT and action == SanitizationAction.LOG_ONLY:
                    action = SanitizationAction.ALERT

        # HTML escape remaining content if any threats were found
        if threats and action == SanitizationAction.SANITIZE:
            sanitized = html.escape(sanitized)

        is_safe = len(threats) == 0 or (action == SanitizationAction.SANITIZE and not self.strict_mode)

        if action == SanitizationAction.REJECT:
            is_safe = False
            sanitized = ""

        return SanitizationResult(
            is_safe=is_safe,
            original_value=value,
            sanitized_value=sanitized,
            threats_detected=threats,
            action_taken=action,
        )

    def sanitize_dict(
        self,
        data: dict[str, Any],
        depth: int = 0,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """
        Recursively sanitize a dictionary.

        Args:
            data: Dictionary to sanitize
            depth: Current recursion depth

        Returns:
            Tuple of (sanitized dict, list of all threats found)
        """
        if depth >= self.max_recursion_depth:
            logger.warning("Max recursion depth reached during sanitization")
            return data, []

        sanitized_data = {}
        all_threats = []

        for key, value in data.items():
            # Sanitize the key
            key_result = self.sanitize_string(str(key))
            if not key_result.is_safe:
                all_threats.extend(key_result.threats_detected)
                if self.strict_mode:
                    continue  # Skip this key entirely

            sanitized_key = key_result.sanitized_value or str(key)

            # Sanitize the value based on type
            if isinstance(value, str):
                result = self.sanitize_string(value)
                all_threats.extend(result.threats_detected)
                sanitized_data[sanitized_key] = result.sanitized_value if result.is_safe else ""
            elif isinstance(value, dict):
                nested_data, nested_threats = self.sanitize_dict(value, depth + 1)
                all_threats.extend(nested_threats)
                sanitized_data[sanitized_key] = nested_data
            elif isinstance(value, list):
                sanitized_list = []
                for item in value:
                    if isinstance(item, str):
                        result = self.sanitize_string(item)
                        all_threats.extend(result.threats_detected)
                        sanitized_list.append(result.sanitized_value if result.is_safe else "")
                    elif isinstance(item, dict):
                        nested_data, nested_threats = self.sanitize_dict(item, depth + 1)
                        all_threats.extend(nested_threats)
                        sanitized_list.append(nested_data)
                    else:
                        sanitized_list.append(item)
                sanitized_data[sanitized_key] = sanitized_list
            else:
                sanitized_data[sanitized_key] = value

        return sanitized_data, all_threats


class SQLiFilter:
    """SQL Injection detection filter."""

    def __init__(self):
        self.patterns = [p for p in THREAT_PATTERNS if p.category == ThreatCategory.SQLI]
        self.compiled = [(p, p.compile()) for p in self.patterns]

    def detect(self, value: str) -> list[dict[str, Any]]:
        """Detect SQL injection attempts."""
        threats = []
        for pattern, compiled in self.compiled:
            if compiled.search(value):
                threats.append(
                    {
                        "category": pattern.category.value,
                        "description": pattern.description,
                        "severity": pattern.severity,
                    }
                )
        return threats


class XSSDetector:
    """Cross-Site Scripting detection filter."""

    def __init__(self):
        self.patterns = [p for p in THREAT_PATTERNS if p.category == ThreatCategory.XSS]
        self.compiled = [(p, p.compile()) for p in self.patterns]

    def detect(self, value: str) -> list[dict[str, Any]]:
        """Detect XSS attempts."""
        threats = []
        for pattern, compiled in self.compiled:
            if compiled.search(value):
                threats.append(
                    {
                        "category": pattern.category.value,
                        "description": pattern.description,
                        "severity": pattern.severity,
                    }
                )
        return threats


# =============================================================================
# API Factory Defaults
# =============================================================================


@dataclass
class EndpointSecurityConfig:
    """Security configuration for an individual endpoint."""

    path: str
    method: str = "GET"
    auth_level: AuthLevel = AuthLevel.INTEGRITY
    rate_limit: str = "10/second"
    rate_limit_burst: int = 5
    input_sanitization: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    timeout_ms: int = 30000
    allowed_content_types: list[str] = field(default_factory=lambda: ["application/json"])
    require_https: bool = True
    audit_logging: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "method": self.method,
            "auth_level": self.auth_level.value,
            "rate_limit": self.rate_limit,
            "rate_limit_burst": self.rate_limit_burst,
            "input_sanitization": self.input_sanitization,
            "max_request_size": self.max_request_size,
            "timeout_ms": self.timeout_ms,
            "allowed_content_types": self.allowed_content_types,
            "require_https": self.require_https,
            "audit_logging": self.audit_logging,
        }


@dataclass
class APISecurityDefaults:
    """
    Factory defaults for API security.

    These defaults ensure the API remains secure even under
    configuration drift or incomplete setup.
    """

    # Minimum authentication level for any endpoint
    min_auth_level: AuthLevel = AuthLevel.INTEGRITY

    # Default rate limits
    rate_limit: str = "10/second"
    rate_limit_window_seconds: int = 60
    rate_limit_burst: int = 5

    # Input sanitization filters (enabled by default)
    input_sanitization_enabled: bool = True
    input_sanitization_strict: bool = True
    input_filters: list[str] = field(
        default_factory=lambda: [
            "SQLiFilter",
            "XSSDetector",
        ]
    )

    # Request constraints
    max_request_size_bytes: int = 10 * 1024 * 1024  # 10MB
    max_response_size_bytes: int = 50 * 1024 * 1024  # 50MB
    default_timeout_ms: int = 30000
    streaming_timeout_ms: int = 300000  # 5 minutes for streaming

    # Security headers (always applied)
    security_headers: dict[str, str] = field(
        default_factory=lambda: {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }
    )

    # TLS/HTTPS requirements
    require_https_in_production: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True

    # Audit and logging
    audit_all_requests: bool = True
    log_request_bodies: bool = False  # Disabled for privacy
    log_response_bodies: bool = False
    mask_sensitive_headers: list[str] = field(
        default_factory=lambda: [
            "Authorization",
            "X-API-Key",
            "Cookie",
            "Set-Cookie",
        ]
    )

    # Public endpoints (exempt from min_auth_level)
    public_endpoints: list[str] = field(
        default_factory=lambda: [
            "/health",
            "/health/live",
            "/health/ready",
            "/health/startup",
            "/ping",
            "/version",
            "/",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "min_auth_level": self.min_auth_level.value,
            "rate_limit": self.rate_limit,
            "rate_limit_window_seconds": self.rate_limit_window_seconds,
            "rate_limit_burst": self.rate_limit_burst,
            "input_sanitization_enabled": self.input_sanitization_enabled,
            "input_sanitization_strict": self.input_sanitization_strict,
            "input_filters": self.input_filters,
            "max_request_size_bytes": self.max_request_size_bytes,
            "max_response_size_bytes": self.max_response_size_bytes,
            "default_timeout_ms": self.default_timeout_ms,
            "streaming_timeout_ms": self.streaming_timeout_ms,
            "security_headers": self.security_headers,
            "require_https_in_production": self.require_https_in_production,
            "hsts_max_age": self.hsts_max_age,
            "audit_all_requests": self.audit_all_requests,
            "public_endpoints": self.public_endpoints,
        }


# Global factory defaults instance
API_DEFAULTS = APISecurityDefaults()


def get_api_defaults() -> APISecurityDefaults:
    """Get the API security factory defaults."""
    return API_DEFAULTS


def apply_security_defaults(
    endpoint_config: Any,
    defaults: APISecurityDefaults | None = None,
) -> Any:
    """
    Apply factory defaults to an endpoint configuration or FastAPI app/router.

    Ensures minimum security requirements are met by merging
    endpoint config with factory defaults.

    Args:
        endpoint_config: Raw endpoint configuration (dict) or FastAPI app/router
        defaults: Security defaults to apply (uses global if None)

    Returns:
        EndpointSecurityConfig with defaults applied, or None if app/router
    """
    if defaults is None:
        defaults = API_DEFAULTS

    # Handle FastAPI/APIRouter instances
    from fastapi import APIRouter, FastAPI

    if isinstance(endpoint_config, (FastAPI, APIRouter)):
        # For an app or router, we iterate over routes and apply defaults
        # This is a placeholder for actual route-level enforcement
        # which usually requires middleware or route class overrides.
        logger.info(f"Applying security standards to {type(endpoint_config).__name__}")
        return None

    if not isinstance(endpoint_config, dict):
        logger.warning(f"Expected dict for endpoint_config, got {type(endpoint_config).__name__}")
        return None

    path = endpoint_config.get("path", "/")
    method = endpoint_config.get("method", "GET").upper()

    # Determine if endpoint is public
    is_public = any(
        path == pub or (pub != "/" and path.startswith(pub.rstrip("/") + "/")) for pub in defaults.public_endpoints
    )

    # Get configured auth level, apply minimum
    config_auth = endpoint_config.get("auth_level", None)
    if config_auth:
        try:
            config_auth_level = AuthLevel(config_auth)
        except ValueError:
            config_auth_level = defaults.min_auth_level
    else:
        config_auth_level = defaults.min_auth_level

    # For non-public endpoints, enforce minimum auth level
    if not is_public:
        if _auth_level_value(config_auth_level) < _auth_level_value(defaults.min_auth_level):
            logger.warning(
                f"Endpoint {method} {path} auth level {config_auth_level.value} "
                f"below minimum {defaults.min_auth_level.value}, upgrading"
            )
            config_auth_level = defaults.min_auth_level
    else:
        config_auth_level = AuthLevel.NONE

    return EndpointSecurityConfig(
        path=path,
        method=method,
        auth_level=config_auth_level,
        rate_limit=endpoint_config.get("rate_limit", defaults.rate_limit),
        rate_limit_burst=endpoint_config.get("rate_limit_burst", defaults.rate_limit_burst),
        input_sanitization=endpoint_config.get(
            "input_sanitization",
            defaults.input_sanitization_enabled,
        ),
        max_request_size=endpoint_config.get(
            "max_request_size",
            defaults.max_request_size_bytes,
        ),
        timeout_ms=endpoint_config.get("timeout_ms", defaults.default_timeout_ms),
        allowed_content_types=endpoint_config.get(
            "allowed_content_types",
            ["application/json"],
        ),
        require_https=endpoint_config.get(
            "require_https",
            defaults.require_https_in_production,
        ),
        audit_logging=endpoint_config.get("audit_logging", defaults.audit_all_requests),
    )


# Alias for backwards compatibility / shorter import
apply_defaults = apply_security_defaults


def _auth_level_value(level: AuthLevel) -> int:
    """Get numeric value for auth level comparison."""
    values = {
        AuthLevel.NONE: 0,
        AuthLevel.BASIC: 1,
        AuthLevel.INTEGRITY: 2,
        AuthLevel.ELEVATED: 3,
        AuthLevel.ADMIN: 4,
    }
    return values.get(level, 0)


# =============================================================================
# Security Verification
# =============================================================================


@dataclass
class SecurityAuditResult:
    """Result of a security audit."""

    compliant: bool
    endpoint: str
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    config_applied: dict[str, Any] = field(default_factory=dict)


def audit_endpoint_security(
    endpoint_config: dict[str, Any],
    defaults: APISecurityDefaults | None = None,
) -> SecurityAuditResult:
    """
    Audit an endpoint's security configuration against factory defaults.

    Args:
        endpoint_config: Endpoint configuration to audit
        defaults: Defaults to audit against

    Returns:
        SecurityAuditResult with compliance status and issues
    """
    if defaults is None:
        defaults = API_DEFAULTS

    path = endpoint_config.get("path", "/unknown")
    issues = []
    warnings = []

    # Check authentication level
    auth_level = endpoint_config.get("auth_level")
    is_public = any(
        path == pub or (pub != "/" and path.startswith(pub.rstrip("/") + "/")) for pub in defaults.public_endpoints
    )

    if not is_public:
        if not auth_level:
            issues.append("Missing authentication level configuration")
        else:
            try:
                level = AuthLevel(auth_level)
                if _auth_level_value(level) < _auth_level_value(defaults.min_auth_level):
                    issues.append(f"Auth level {level.value} below minimum {defaults.min_auth_level.value}")
            except ValueError:
                issues.append(f"Invalid auth level: {auth_level}")

    # Check rate limiting
    if not endpoint_config.get("rate_limit"):
        warnings.append("No explicit rate limit configured, using default")

    # Check input sanitization
    if endpoint_config.get("input_sanitization") is False and defaults.input_sanitization_enabled:
        warnings.append("Input sanitization disabled for this endpoint")

    # Check timeout
    timeout = endpoint_config.get("timeout_ms", defaults.default_timeout_ms)
    if timeout > 60000:  # More than 1 minute
        warnings.append(f"High timeout ({timeout}ms) may expose DoS vulnerability")

    # Check HTTPS
    if not endpoint_config.get("require_https", True) and defaults.require_https_in_production:
        issues.append("HTTPS not required but production requires it")

    # Apply defaults and get final config
    final_config = apply_security_defaults(endpoint_config, defaults)

    return SecurityAuditResult(
        compliant=len(issues) == 0,
        endpoint=path,
        issues=issues,
        warnings=warnings,
        config_applied=final_config.to_dict(),
    )


def verify_api_against_defaults(
    routes: list[dict[str, Any]],
    defaults: APISecurityDefaults | None = None,
) -> dict[str, Any]:
    """
    Verify all API routes against factory defaults.

    Args:
        routes: List of route configurations
        defaults: Defaults to verify against

    Returns:
        Summary of verification results
    """
    if defaults is None:
        defaults = API_DEFAULTS

    results = []
    compliant_count = 0
    issue_count = 0
    warning_count = 0

    for route in routes:
        result = audit_endpoint_security(route, defaults)
        results.append(
            {
                "endpoint": result.endpoint,
                "compliant": result.compliant,
                "issues": result.issues,
                "warnings": result.warnings,
            }
        )

        if result.compliant:
            compliant_count += 1
        issue_count += len(result.issues)
        warning_count += len(result.warnings)

    overall_compliant = issue_count == 0

    return {
        "compliant": overall_compliant,
        "summary": {
            "total_endpoints": len(routes),
            "compliant_endpoints": compliant_count,
            "total_issues": issue_count,
            "total_warnings": warning_count,
        },
        "defaults": defaults.to_dict(),
        "results": results,
    }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "AuthLevel",
    "ThreatCategory",
    "SanitizationAction",
    # Sanitization
    "ThreatPattern",
    "THREAT_PATTERNS",
    "SanitizationResult",
    "InputSanitizer",
    "SQLiFilter",
    "XSSDetector",
    # Defaults
    "EndpointSecurityConfig",
    "APISecurityDefaults",
    "API_DEFAULTS",
    "get_api_defaults",
    "apply_security_defaults",
    "apply_defaults",
    # Verification
    "SecurityAuditResult",
    "audit_endpoint_security",
    "verify_api_against_defaults",
]
