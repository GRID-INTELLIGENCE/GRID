"""
Mothership Configuration Module.

Provides fine-tuned control over all configuration aspects,
including inference abrasiveness settings with controlled automation.

Database notes:
- Supports primary DB selection (Databricks or standard SQLAlchemy URL).
- Supports a fallback DB URL (typically SQLite) for local-first resiliency.
  The fallback is used when Databricks is enabled but not configured, or
  when the connection cannot be validated.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

# Check for quiet mode early to suppress warnings in CLI tools
_quiet_mode = os.environ.get("GRID_QUIET", "").lower() in ("1", "true", "yes")
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

try:
    from ..security.secret_validation import (  # type: ignore[import-not-found]
        SecretValidationError,
        validate_secret_strength,
    )
except ImportError:
    # Fallback if security module not available
    SecretValidationError = Exception

    def validate_secret_strength(secret: str, environment: str) -> str:
        """Fallback validation."""
        if not secret or len(secret) < 32:
            return "weak"
        return "acceptable"


class Environment(str, Enum):
    """Deployment environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse boolean from environment variable string."""
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "y", "on"}


def _parse_list(value: str | None, separator: str = ",") -> list[str]:
    """Parse comma-separated list from environment variable."""
    if not value:
        return []
    return [item.strip() for item in value.split(separator) if item.strip()]


@dataclass
class ServerSettings:
    """HTTP server configuration."""

    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 4
    reload: bool = False
    debug: bool = False
    root_path: str = ""
    proxy_headers: bool = True

    @classmethod
    def from_env(cls) -> ServerSettings:
        """Load server settings from environment variables."""
        env = os.environ
        return cls(
            host=env.get("MOTHERSHIP_HOST", "0.0.0.0"),
            port=int(env.get("MOTHERSHIP_PORT", "8080")),
            workers=int(env.get("MOTHERSHIP_WORKERS", "4")),
            reload=_parse_bool(env.get("MOTHERSHIP_RELOAD")),
            debug=_parse_bool(env.get("MOTHERSHIP_DEBUG")),
            root_path=env.get("MOTHERSHIP_ROOT_PATH", ""),
            proxy_headers=_parse_bool(env.get("MOTHERSHIP_PROXY_HEADERS"), True),
        )


@dataclass
class DatabaseSettings:
    """Database connection configuration.

    Behavior:
    - If Databricks is enabled and configured, `url` becomes a `databricks://...` URL.
    - If Databricks is enabled but missing config (or fails validation at runtime),
      the app should fall back to `fallback_url` (usually SQLite).
    """

    # Primary database URL used by the application.
    # Examples:
    # - sqlite:///./mothership.db
    # - postgresql://user:pass@localhost/mothership
    # - databricks://token:{token}@{hostname}:443{http_path}
    url: str = os.getenv("MOTHERSHIP_DATABASE_URL", "sqlite:///./mothership.db")

    # Fallback database URL (recommended for local-first resiliency).
    # Used when Databricks is enabled but not configured, or when connection fails.
    fallback_url: str = os.getenv("MOTHERSHIP_DB_FALLBACK_URL", "sqlite:///./mothership_fallback.db")

    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    echo: bool = False

    # Databricks configuration
    use_databricks: bool = False
    databricks_server_hostname: str = ""
    databricks_http_path: str = ""
    databricks_access_token: str = ""

    # Redis for caching/pubsub and rate limiting
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False  # Default to False for Local-First

    # SQLite settings (Local-First)
    sqlite_file: str = "grid.db"

    @classmethod
    def from_env(cls) -> DatabaseSettings:
        """Load database settings from environment variables."""
        env = os.environ

        # Fallback URL (SQLite by default)
        fallback_db_url = env.get("MOTHERSHIP_DB_FALLBACK_URL", "").strip() or "sqlite:///./mothership_fallback.db"
        sqlite_file = env.get("SQLITE_DB_PATH", "grid.db")

        # Check for Databricks configuration
        use_databricks = _parse_bool(env.get("USE_DATABRICKS") or env.get("MOTHERSHIP_USE_DATABRICKS"))

        if use_databricks:
            # Build Databricks connection URL
            server_hostname = env.get("DATABRICKS_SERVER_HOSTNAME", "").strip()
            http_path = env.get("DATABRICKS_HTTP_PATH", "").strip()
            # Prefer local_databricks env var, fallback to DATABRICKS_ACCESS_TOKEN
            access_token = env.get("local_databricks", "").strip() or env.get("DATABRICKS_ACCESS_TOKEN", "").strip()

            if server_hostname and http_path and access_token:
                # Format: databricks://token:{token}@{hostname}:443{http_path}
                default_db_url = f"databricks://token:{access_token}@{server_hostname}:443{http_path}"
            else:
                # Missing Databricks config, fall back to fallback URL
                if not _quiet_mode:
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        "USE_DATABRICKS=true but missing required environment variables. "
                        "Falling back to MOTHERSHIP_DB_FALLBACK_URL / SQLite. "
                        "Need: DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, DATABRICKS_ACCESS_TOKEN"
                    )
                use_databricks = False
                default_db_url = fallback_db_url
                # Clear Databricks config variables when falling back
                server_hostname = ""
                http_path = ""
                access_token = ""
        else:
            # Default to PostgreSQL in production, SQLite in development
            default_db_url = env.get("MOTHERSHIP_DATABASE_URL", "").strip()
            if not default_db_url:
                env_mode = env.get("MOTHERSHIP_ENVIRONMENT", "development").lower()
                if env_mode == "production":
                    default_db_url = "postgresql://user:pass@localhost/mothership"
                else:
                    default_db_url = "sqlite:///./mothership.db"

            # Set empty strings when not using Databricks
            server_hostname = ""
            http_path = ""
            access_token = ""

        return cls(
            url=default_db_url,
            fallback_url=fallback_db_url,
            pool_size=int(env.get("MOTHERSHIP_DB_POOL_SIZE", "5")),
            max_overflow=int(env.get("MOTHERSHIP_DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(env.get("MOTHERSHIP_DB_POOL_TIMEOUT", "30")),
            echo=_parse_bool(env.get("MOTHERSHIP_DB_ECHO")),
            use_databricks=use_databricks,
            databricks_server_hostname=server_hostname,
            databricks_http_path=http_path,
            databricks_access_token=access_token,
            redis_url=env.get("MOTHERSHIP_REDIS_URL", "redis://localhost:6379/0"),
            redis_enabled=_parse_bool(env.get("MOTHERSHIP_REDIS_ENABLED"), False),
            sqlite_file=sqlite_file,
        )


@dataclass
class CacheSettings:
    """Caching configuration (Local File/Memory vs Redis)."""

    backend: str = "memory"  # memory, sqlite, redis
    ttl: int = 300

    @classmethod
    def from_env(cls) -> CacheSettings:
        env = os.environ
        return cls(
            backend=env.get("CACHE_BACKEND", "memory"),
            ttl=int(env.get("CACHE_TTL", "300")),
        )


@dataclass
class SecuritySettings:
    """Security and authentication configuration."""

    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    api_key_header: str = "X-API-Key"
    cors_origins: list[str] = field(default_factory=list)  # Deny by default, require explicit config
    cors_allow_credentials: bool = False  # Secure default
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    max_request_size_bytes: int = 10 * 1024 * 1024  # 10MB default

    # Explicit security mode fields (previously accessed via getattr fallbacks)
    strict_mode: bool = False  # Enable strict security mode (blocks violations instead of logging)
    input_sanitization_enabled: bool = True  # Enable input sanitization for all requests
    circuit_breaker_enabled: bool = False  # Enable circuit breaker for external service calls
    block_insecure_transport: bool = False  # Block HTTP requests (require HTTPS) in strict mode
    # Parasite Guard (Total Rickall Defense)
    parasite_guard_enabled: bool = True  # Enable/disable the guard system
    parasite_guard_pruning_enabled: bool = True  # Enable automatic pruning of parasitic code paths (Production Ready)

    @classmethod
    def from_env(cls) -> SecuritySettings:
        """Load security settings from environment variables."""
        env = os.environ
        return cls(
            secret_key=env.get("MOTHERSHIP_SECRET_KEY", ""),
            algorithm=env.get("MOTHERSHIP_JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(env.get("MOTHERSHIP_ACCESS_TOKEN_EXPIRE", "30")),
            refresh_token_expire_days=int(env.get("MOTHERSHIP_REFRESH_TOKEN_EXPIRE", "7")),
            api_key_header=env.get("MOTHERSHIP_API_KEY_HEADER", "X-API-Key"),
            cors_origins=_parse_list(env.get("MOTHERSHIP_CORS_ORIGINS", "")),  # Empty = deny all by default
            cors_allow_credentials=_parse_bool(env.get("MOTHERSHIP_CORS_CREDENTIALS"), False),  # Secure default
            rate_limit_enabled=_parse_bool(env.get("MOTHERSHIP_RATE_LIMIT_ENABLED"), True),
            rate_limit_requests=int(env.get("MOTHERSHIP_RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window_seconds=int(env.get("MOTHERSHIP_RATE_LIMIT_WINDOW", "60")),
            max_request_size_bytes=int(env.get("MOTHERSHIP_MAX_REQUEST_SIZE_BYTES", str(10 * 1024 * 1024))),
            # Explicit security mode fields
            strict_mode=_parse_bool(env.get("MOTHERSHIP_SECURITY_STRICT_MODE"), False),
            input_sanitization_enabled=_parse_bool(env.get("MOTHERSHIP_INPUT_SANITIZATION_ENABLED"), True),
            circuit_breaker_enabled=_parse_bool(env.get("MOTHERSHIP_CIRCUIT_BREAKER_ENABLED"), False),
            block_insecure_transport=_parse_bool(env.get("MOTHERSHIP_BLOCK_INSECURE_TRANSPORT"), False),
            # Parasite Guard
            parasite_guard_enabled=_parse_bool(env.get("MOTHERSHIP_PARASITE_GUARD_ENABLED"), True),
            parasite_guard_pruning_enabled=_parse_bool(env.get("MOTHERSHIP_PARASITE_GUARD_PRUNING_ENABLED"), True),
        )

    def validate(self, environment: str | None = None, fail_fast: bool = False) -> list[str]:
        """
        Validate security settings with enhanced security checks.

        Args:
            environment: Environment (production, development, etc.). Defaults to MOTHERSHIP_ENVIRONMENT env var.
            fail_fast: If True and in production, raise exceptions for critical issues instead of returning them.

        Returns:
            List of validation issues (warnings and critical issues)

        Raises:
            SecretValidationError: If fail_fast=True and in production with critical security issues
        """
        from ..security.secret_validation import (
            SecretStrength,
            SecretValidationError,
            validate_secret_strength,
        )

        if environment is None:
            environment = os.getenv("MOTHERSHIP_ENVIRONMENT", "production").lower()
        else:
            environment = environment.lower()

        issues = []
        critical_issues = []

        # Enhanced secret validation with environment-aware behavior
        if not self.secret_key or not self.secret_key.strip():
            if environment == "production":
                critical_msg = (
                    "CRITICAL: MOTHERSHIP_SECRET_KEY is not set. "
                    "This is a CRITICAL security issue in production. "
                    "Set MOTHERSHIP_SECRET_KEY to a secure value "
                    "(use generate_secure_secret() to create one)."
                )
                if fail_fast:
                    raise SecretValidationError(critical_msg)
                critical_issues.append(critical_msg)
            else:
                issues.append(
                    "WARNING: MOTHERSHIP_SECRET_KEY is not set. This is INSECURE and must be fixed before production."
                )
        else:
            try:
                strength = validate_secret_strength(self.secret_key, environment)
                if strength == SecretStrength.WEAK:
                    if environment == "production":
                        critical_msg = (
                            "CRITICAL: JWT secret key is too weak for production. "
                            f"Length: {len(self.secret_key)}. "
                            "Must be at least 32 characters with good entropy. "
                            "Generate with: python -c 'from application.mothership.security.secret_validation "
                            "import generate_secure_secret; print(generate_secure_secret(64))'"
                        )
                        if fail_fast:
                            raise SecretValidationError(critical_msg)
                        critical_issues.append(critical_msg)
                    else:
                        issues.append(
                            f"WARNING: JWT secret key is weak (length={len(self.secret_key)}). "
                            "Recommended: at least 64 characters. "
                            "Generate with: from application.mothership.security.secret_validation "
                            "import generate_secure_secret; print(generate_secure_secret(64))"
                        )
                elif len(self.secret_key) < 32:
                    if environment == "production":
                        critical_msg = (
                            "CRITICAL: Secret key should be at least 32 characters for HS256 algorithm. "
                            f"Current length: {len(self.secret_key)}. "
                            "Generate with: generate_secure_secret(64)"
                        )
                        if fail_fast:
                            raise SecretValidationError(critical_msg)
                        critical_issues.append(critical_msg)
                    else:
                        issues.append(
                            f"WARNING: Secret key should be at least 32 characters for HS256 algorithm "
                            f"(current: {len(self.secret_key)})"
                        )
            except SecretValidationError as e:
                if environment == "production":
                    if fail_fast:
                        raise
                    critical_issues.append(f"CRITICAL: {str(e)}")
                else:
                    issues.append(f"WARNING: {str(e)}")
            except Exception as e:
                issues.append(f"Secret validation error: {str(e)}")

            # Security audit log (masked) - log successful secret loading
            if self.secret_key and not critical_issues:
                # Only log if secret is present and validation passed
                try:
                    import hashlib

                    from ..security.secret_validation import mask_secret

                    secret_hash = hashlib.sha256(self.secret_key.encode()).hexdigest()[:16]
                    masked_secret = mask_secret(self.secret_key)
                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"Security: Secret key loaded (length={len(self.secret_key)}, "
                        f"masked={masked_secret}, hash={secret_hash}, environment={environment})"
                    )
                except Exception:
                    # If security module not available, log minimal info
                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"Security: Secret key loaded (length={len(self.secret_key)}, environment={environment})"
                    )

        # CORS security checks with environment awareness
        if "*" in self.cors_origins:
            if environment == "production":
                critical_msg = (
                    "CRITICAL: CORS wildcard (*) detected - not allowed in production. "
                    "Use explicit origins in MOTHERSHIP_CORS_ORIGINS environment variable."
                )
                if fail_fast:
                    raise SecretValidationError(critical_msg)
                critical_issues.append(critical_msg)
            else:
                issues.append("WARNING: CORS wildcard (*) detected - should use explicit origins in production")

        # Request size limits
        if self.max_request_size_bytes > 100 * 1024 * 1024:  # 100MB
            issues.append(
                f"WARNING: Request size limit ({self.max_request_size_bytes} bytes) is very large - "
                "consider reducing for security (recommended: 10MB or less)"
            )

        # Rate limiting validation with environment awareness
        if not self.rate_limit_enabled:
            if environment == "production":
                issues.append(
                    "WARNING: Rate limiting is disabled - recommended for production security. "
                    "Set MOTHERSHIP_RATE_LIMIT_ENABLED=true"
                )
            else:
                issues.append("INFO: Rate limiting is disabled (development mode)")

        # Return critical issues first, then warnings
        return critical_issues + issues


@dataclass
class IntegrationSettings:
    """External integration configuration."""

    # Gemini Cloud Integration
    gemini_enabled: bool = True
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    gemini_timeout: int = 120

    # Grid Core Integration
    grid_api_url: str = "http://localhost:8000"
    grid_api_key: str = ""
    grid_timeout: int = 30

    # Webhook Configuration
    webhook_enabled: bool = False
    webhook_endpoints: list[str] = field(default_factory=list)
    webhook_timeout: int = 10
    webhook_retry_count: int = 3

    @classmethod
    def from_env(cls) -> IntegrationSettings:
        """Load integration settings from environment variables."""
        env = os.environ
        return cls(
            gemini_enabled=_parse_bool(env.get("MOTHERSHIP_GEMINI_ENABLED")),
            # Note: API key should be loaded via security.ai_safety for validation
            gemini_api_key=env.get("GEMINI_API_KEY", ""),
            gemini_model=env.get("GEMINI_MODEL", "gemini-1.5-pro"),
            gemini_timeout=int(env.get("GEMINI_TIMEOUT", "120")),
            grid_api_url=env.get("GRID_API_URL", "http://localhost:8000"),
            grid_api_key=env.get("GRID_API_KEY", ""),
            grid_timeout=int(env.get("GRID_TIMEOUT", "30")),
            webhook_enabled=_parse_bool(env.get("MOTHERSHIP_WEBHOOK_ENABLED")),
            webhook_endpoints=_parse_list(env.get("MOTHERSHIP_WEBHOOK_ENDPOINTS", "")),
            webhook_timeout=int(env.get("MOTHERSHIP_WEBHOOK_TIMEOUT", "10")),
            webhook_retry_count=int(env.get("MOTHERSHIP_WEBHOOK_RETRY", "3")),
        )


@dataclass
class TelemetrySettings:
    """Telemetry and monitoring configuration."""

    enabled: bool = True
    metrics_enabled: bool = True
    metrics_path: str = "/metrics"
    tracing_enabled: bool = False
    tracing_sample_rate: float = 0.1
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"
    log_file: str | None = None
    health_check_interval: int = 30

    @classmethod
    def from_env(cls) -> TelemetrySettings:
        """Load telemetry settings from environment variables."""
        env = os.environ
        log_level_str = env.get("MOTHERSHIP_LOG_LEVEL", "INFO").upper()
        try:
            log_level = LogLevel(log_level_str)
        except ValueError:
            log_level = LogLevel.INFO

        return cls(
            enabled=_parse_bool(env.get("MOTHERSHIP_TELEMETRY_ENABLED"), True),
            metrics_enabled=_parse_bool(env.get("MOTHERSHIP_METRICS_ENABLED"), True),
            metrics_path=env.get("MOTHERSHIP_METRICS_PATH", "/metrics"),
            tracing_enabled=_parse_bool(env.get("MOTHERSHIP_TRACING_ENABLED")),
            tracing_sample_rate=float(env.get("MOTHERSHIP_TRACING_SAMPLE_RATE", "0.1")),
            log_level=log_level,
            log_format=env.get("MOTHERSHIP_LOG_FORMAT", "json"),
            log_file=env.get("MOTHERSHIP_LOG_FILE"),
            health_check_interval=int(env.get("MOTHERSHIP_HEALTH_CHECK_INTERVAL", "30")),
        )


@dataclass
class PaymentSettings:
    """Payment gateway configuration."""

    # bKash settings (DEPRECATED: Use Stripe)
    bkash_app_key: str = ""
    bkash_app_secret: str = ""
    bkash_username: str = ""
    bkash_password: str = ""
    bkash_base_url: str = "https://tokenized.sandbox.bka.sh/v1.2.0-beta"
    bkash_enabled: bool = False  # Decommissioned

    # Stripe settings
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""
    stripe_enabled: bool = False

    # Payment defaults
    default_gateway: str = "stripe"  # "bkash" or "stripe"
    currency: str = "USD"
    default_timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> PaymentSettings:
        """Load payment settings from environment variables."""
        env = os.environ
        default_gateway = env.get("MOTHERSHIP_PAYMENT_DEFAULT_GATEWAY", "stripe")
        if default_gateway == "bkash":
            from .utils import ghost_config_trap  # type: ignore[import-not-found]

            ghost_config_trap("config", "default_gateway=bkash")
            default_gateway = "stripe"  # Force to stripe after trapping
        bkash_force_disable = _parse_bool(env.get("MOTHERSHIP_BKASH_FORCE_DISABLE"), False)
        bkash_enabled = _parse_bool(env.get("BKASH_ENABLED")) if not bkash_force_disable else False

        return cls(
            bkash_app_key=env.get("BKASH_APP_KEY", ""),
            bkash_app_secret=env.get("BKASH_APP_SECRET", ""),
            bkash_username=env.get("BKASH_USERNAME", ""),
            bkash_password=env.get("BKASH_PASSWORD", ""),
            bkash_base_url=env.get("BKASH_BASE_URL", "https://tokenized.sandbox.bka.sh/v1.2.0-beta"),
            bkash_enabled=bkash_enabled,
            stripe_secret_key=env.get("STRIPE_SECRET_KEY", ""),
            stripe_webhook_secret=env.get("STRIPE_WEBHOOK_SECRET", ""),
            stripe_publishable_key=env.get("STRIPE_PUBLISHABLE_KEY", ""),
            stripe_enabled=_parse_bool(env.get("STRIPE_ENABLED")),
            default_gateway=default_gateway,
            currency=env.get("MOTHERSHIP_PAYMENT_CURRENCY", "USD"),
            default_timeout_seconds=int(env.get("MOTHERSHIP_PAYMENT_TIMEOUT", "30")),
        )

    def validate(self) -> list[str]:
        """Validate payment settings."""
        issues = []
        if self.default_gateway == "bkash" and not self.bkash_enabled:
            issues.append("bKash is set as default gateway but not enabled")
        if self.default_gateway == "stripe" and not self.stripe_enabled:
            issues.append("Stripe is set as default gateway but not enabled")
        return issues


@dataclass
class BillingSettings:
    """Billing and subscription configuration."""

    # Tier definitions (usage limits per month)
    free_tier_relationship_analyses: int = 100
    free_tier_entity_extractions: int = 1000
    starter_tier_relationship_analyses: int = 1000
    starter_tier_entity_extractions: int = 10000
    pro_tier_relationship_analyses: int = 10000
    pro_tier_entity_extractions: int = 100000

    # Resonance Tier definitions (usage limits per month)
    free_tier_resonance_events: int = 1000
    free_tier_high_impact_events: int = 50
    starter_tier_resonance_events: int = 10000
    starter_tier_high_impact_events: int = 500
    pro_tier_resonance_events: int = 100000
    pro_tier_high_impact_events: int = 5000

    # Pricing (in cents)
    starter_monthly_price: int = 4900  # $49.00
    pro_monthly_price: int = 19900  # $199.00

    # Overage pricing (per unit)
    relationship_analysis_overage_cents: int = 5  # $0.05
    entity_extraction_overage_cents: int = 1  # $0.01
    resonance_event_overage_cents: int = 1  # $0.01 per event
    high_impact_event_overage_cents: int = 5  # $0.05 per event

    # Billing cycle
    billing_cycle_days: int = 30

    @classmethod
    def from_env(cls) -> BillingSettings:
        """Load billing settings from environment variables."""
        env = os.environ
        return cls(
            free_tier_relationship_analyses=int(env.get("BILLING_FREE_RELATIONSHIP_ANALYSES", "100")),
            free_tier_entity_extractions=int(env.get("BILLING_FREE_ENTITY_EXTRACTIONS", "1000")),
            starter_tier_relationship_analyses=int(env.get("BILLING_STARTER_RELATIONSHIP_ANALYSES", "1000")),
            starter_tier_entity_extractions=int(env.get("BILLING_STARTER_ENTITY_EXTRACTIONS", "10000")),
            pro_tier_relationship_analyses=int(env.get("BILLING_PRO_RELATIONSHIP_ANALYSES", "10000")),
            pro_tier_entity_extractions=int(env.get("BILLING_PRO_ENTITY_EXTRACTIONS", "100000")),
            starter_monthly_price=int(env.get("BILLING_STARTER_PRICE_CENTS", "4900")),
            pro_monthly_price=int(env.get("BILLING_PRO_PRICE_CENTS", "19900")),
            relationship_analysis_overage_cents=int(env.get("BILLING_RELATIONSHIP_OVERAGE_CENTS", "5")),
            entity_extraction_overage_cents=int(env.get("BILLING_ENTITY_OVERAGE_CENTS", "1")),
            free_tier_resonance_events=int(env.get("BILLING_FREE_RESONANCE_EVENTS", "1000")),
            free_tier_high_impact_events=int(env.get("BILLING_FREE_HIGH_IMPACT_EVENTS", "50")),
            starter_tier_resonance_events=int(env.get("BILLING_STARTER_RESONANCE_EVENTS", "10000")),
            starter_tier_high_impact_events=int(env.get("BILLING_STARTER_HIGH_IMPACT_EVENTS", "500")),
            pro_tier_resonance_events=int(env.get("BILLING_PRO_RESONANCE_EVENTS", "100000")),
            pro_tier_high_impact_events=int(env.get("BILLING_PRO_HIGH_IMPACT_EVENTS", "5000")),
            resonance_event_overage_cents=int(env.get("BILLING_RESONANCE_OVERAGE_CENTS", "1")),
            high_impact_event_overage_cents=int(env.get("BILLING_HIGH_IMPACT_OVERAGE_CENTS", "5")),
            billing_cycle_days=int(env.get("BILLING_CYCLE_DAYS", "30")),
        )


@dataclass
class CockpitSettings:
    """Cockpit-specific operational settings."""

    # Session management
    session_timeout_minutes: int = 60
    max_concurrent_sessions: int = 100

    # Task management
    task_queue_size: int = 1000
    task_timeout_seconds: int = 300
    task_retry_limit: int = 3

    # Real-time features
    websocket_enabled: bool = True
    websocket_heartbeat_interval: int = 30
    websocket_max_connections: int = 500

    # Dashboard features
    dashboard_refresh_rate: int = 5
    dashboard_history_hours: int = 24

    # Auto-scaling thresholds
    autoscale_enabled: bool = False
    autoscale_min_workers: int = 1
    autoscale_max_workers: int = 10
    autoscale_cpu_threshold: float = 0.8

    @classmethod
    def from_env(cls) -> CockpitSettings:
        """Load cockpit settings from environment variables."""
        env = os.environ
        return cls(
            session_timeout_minutes=int(env.get("MOTHERSHIP_SESSION_TIMEOUT", "60")),
            max_concurrent_sessions=int(env.get("MOTHERSHIP_MAX_SESSIONS", "100")),
            task_queue_size=int(env.get("MOTHERSHIP_TASK_QUEUE_SIZE", "1000")),
            task_timeout_seconds=int(env.get("MOTHERSHIP_TASK_TIMEOUT", "300")),
            task_retry_limit=int(env.get("MOTHERSHIP_TASK_RETRY_LIMIT", "3")),
            websocket_enabled=_parse_bool(env.get("MOTHERSHIP_WEBSOCKET_ENABLED"), True),
            websocket_heartbeat_interval=int(env.get("MOTHERSHIP_WS_HEARTBEAT", "30")),
            websocket_max_connections=int(env.get("MOTHERSHIP_WS_MAX_CONNECTIONS", "500")),
            dashboard_refresh_rate=int(env.get("MOTHERSHIP_DASHBOARD_REFRESH", "5")),
            dashboard_history_hours=int(env.get("MOTHERSHIP_DASHBOARD_HISTORY", "24")),
            autoscale_enabled=_parse_bool(env.get("MOTHERSHIP_AUTOSCALE_ENABLED")),
            autoscale_min_workers=int(env.get("MOTHERSHIP_AUTOSCALE_MIN", "1")),
            autoscale_max_workers=int(env.get("MOTHERSHIP_AUTOSCALE_MAX", "10")),
            autoscale_cpu_threshold=float(env.get("MOTHERSHIP_AUTOSCALE_CPU_THRESHOLD", "0.8")),
        )


@dataclass
class MothershipSettings:
    """
    Top-level Mothership Cockpit configuration.

    Aggregates all configuration subsystems into a single,
    easy-to-use settings object with validation support.
    """

    app_name: str = "Mothership Cockpit"
    app_version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    base_path: Path = field(default_factory=lambda: Path.cwd())

    # Subsystem settings
    server: ServerSettings = field(default_factory=ServerSettings.from_env)
    database: DatabaseSettings = field(default_factory=DatabaseSettings.from_env)
    cache: CacheSettings = field(default_factory=CacheSettings.from_env)
    security: SecuritySettings = field(default_factory=SecuritySettings.from_env)
    integrations: IntegrationSettings = field(default_factory=IntegrationSettings.from_env)
    telemetry: TelemetrySettings = field(default_factory=TelemetrySettings.from_env)
    cockpit: CockpitSettings = field(default_factory=CockpitSettings.from_env)
    payment: PaymentSettings = field(default_factory=PaymentSettings.from_env)
    billing: BillingSettings = field(default_factory=BillingSettings.from_env)

    # Inference abrasiveness configuration (fine-tuned control)
    # Lazy import to avoid circular dependencies - use getattr or lazy property
    inference_abrasiveness: Any | None = field(default=None)

    @classmethod
    def from_env(cls) -> MothershipSettings:
        """Load all settings from environment variables."""
        env = os.environ
        env_str = env.get("MOTHERSHIP_ENVIRONMENT", "development").lower()
        try:
            environment = Environment(env_str)
        except ValueError:
            environment = Environment.DEVELOPMENT

        base_path_str = env.get("MOTHERSHIP_BASE_PATH")
        base_path = Path(base_path_str) if base_path_str else Path.cwd()

        settings = cls(
            app_name=env.get("MOTHERSHIP_APP_NAME", "Mothership Cockpit"),
            app_version=env.get("MOTHERSHIP_APP_VERSION", "1.0.0"),
            environment=environment,
            base_path=base_path,
        )

        # Lazy import inference abrasiveness config to avoid circular deps
        try:
            from .inference_abrasiveness import InferenceAbrasivenessConfig

            settings.inference_abrasiveness = InferenceAbrasivenessConfig.from_env()
        except (ImportError, AttributeError):
            settings.inference_abrasiveness = None

        return settings

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == Environment.TESTING

    @property
    def debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.server.debug or self.is_development

    def validate(self, fail_fast: bool = False) -> list[str]:
        """
        Validate all settings and return list of issues.

        Args:
            fail_fast: If True and in production, raise exceptions for critical issues.

        Returns:
            List of validation issues (warnings and critical issues)

        Raises:
            SecretValidationError: If fail_fast=True and in production with critical security issues
            ValueError: If fail_fast=True and in production with critical configuration issues
        """
        from ..security.secret_validation import SecretValidationError

        environment = self.environment.value.lower()
        issues = []

        # Security validation (includes enhanced secret validation with environment awareness)
        try:
            security_issues = self.security.validate(environment=environment, fail_fast=fail_fast)
            issues.extend(security_issues)
        except SecretValidationError as e:
            if fail_fast:
                raise
            issues.append(f"CRITICAL: {str(e)}")

        # Production-specific validation with fail-fast
        if self.is_production:
            if self.server.debug:
                critical_msg = (
                    "CRITICAL: Debug mode should be disabled in production. "
                    "Set MOTHERSHIP_DEBUG=false or MOTHERSHIP_SERVER_DEBUG=false"
                )
                if fail_fast:
                    raise ValueError(critical_msg)
                issues.append(critical_msg)

            if self.server.reload:
                critical_msg = "CRITICAL: Auto-reload should be disabled in production. Set MOTHERSHIP_RELOAD=false"
                if fail_fast:
                    raise ValueError(critical_msg)
                issues.append(critical_msg)

            # CORS validation (handled in SecuritySettings, but check again for clarity)
            if "*" in self.security.cors_origins:
                # Already handled in SecuritySettings.validate(), but ensure consistent message
                pass

            # AI API key validation (if AI integrations are enabled)
            if self.integrations.gemini_enabled:
                if not self.integrations.gemini_api_key or not self.integrations.gemini_api_key.strip():
                    issues.append(
                        "WARNING: Gemini is enabled but GEMINI_API_KEY is not set. "
                        "Integration will fail at runtime. "
                        "Set GEMINI_API_KEY environment variable or disable with MOTHERSHIP_GEMINI_ENABLED=false"
                    )
                elif len(self.integrations.gemini_api_key) < 32:
                    issues.append(
                        "WARNING: Gemini API key appears to be too short. Verify GEMINI_API_KEY is set correctly."
                    )

        return issues

    def validate_critical_settings(self) -> None:
        """
        Validate critical settings and fail fast in production.

        This method validates only critical settings that would prevent secure operation.
        In production, it raises exceptions immediately. In other environments, it logs warnings.

        Raises:
            SecretValidationError: If critical security settings are invalid
            ValueError: If critical configuration settings are invalid
        """
        environment = self.environment.value.lower()
        is_production = environment == "production"

        # Use fail_fast=True in production to get immediate exceptions
        issues = self.validate(fail_fast=is_production)

        # If we get here with fail_fast=False (non-production), log warnings
        if not is_production and issues:
            critical_issues = [issue for issue in issues if issue.startswith("CRITICAL")]
            if critical_issues:
                logger = logging.getLogger(__name__)
                logger.warning("Critical configuration issues detected (non-production mode - startup allowed):")
                for issue in critical_issues:
                    logger.warning(f"  - {issue}")
                logger.warning("These MUST be fixed before production deployment.")

    def to_dict(self, mask_secrets: bool = True) -> dict[str, Any]:
        """Export settings as dictionary with optional secret masking."""

        def mask_value(key: str, value: Any) -> Any:
            if not mask_secrets:
                return value
            secret_keys = {"secret_key", "api_key", "password", "token"}
            if any(s in key.lower() for s in secret_keys):
                if isinstance(value, str) and value:
                    return f"{value[:4]}***" if len(value) > 4 else "***"
            return value

        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment.value,
            "base_path": str(self.base_path),
            "debug_enabled": self.debug_enabled,
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "workers": self.server.workers,
            },
            "database": {
                "url": self.database.url,
                "pool_size": self.database.pool_size,
                "echo": self.database.echo,
            },
            "security": {
                "algorithm": self.security.algorithm,
                "access_token_expire_minutes": self.security.access_token_expire_minutes,
                "refresh_token_expire_days": self.security.refresh_token_expire_days,
                "api_key_header": self.security.api_key_header,
                "cors_origins": self.security.cors_origins,
                "rate_limit_enabled": self.security.rate_limit_enabled,
                "rate_limit_requests": self.security.rate_limit_requests,
                "rate_limit_window_seconds": self.security.rate_limit_window_seconds,
            },
            "integrations": {
                "gemini_enabled": self.integrations.gemini_enabled,
                "gemini_model": self.integrations.gemini_model,
                "gemini_timeout": self.integrations.gemini_timeout,
                "grid_api_url": self.integrations.grid_api_url,
                "grid_timeout": self.integrations.grid_timeout,
                "webhook_enabled": self.integrations.webhook_enabled,
                "webhook_timeout": self.integrations.webhook_timeout,
                "webhook_retry_count": self.integrations.webhook_retry_count,
            },
            "telemetry": {
                "enabled": self.telemetry.enabled,
                "metrics_enabled": self.telemetry.metrics_enabled,
                "metrics_path": self.telemetry.metrics_path,
                "tracing_enabled": self.telemetry.tracing_enabled,
                "tracing_sample_rate": self.telemetry.tracing_sample_rate,
                "log_level": self.telemetry.log_level.value,
            },
            "cockpit": {
                "websocket_enabled": self.cockpit.websocket_enabled,
                "max_concurrent_sessions": self.cockpit.max_concurrent_sessions,
            },
        }


# Module-level singleton
_settings: MothershipSettings | None = None


@lru_cache(maxsize=1)
def get_settings() -> MothershipSettings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure settings are only loaded once
    and remain consistent throughout the application lifecycle.
    """
    global _settings
    if _settings is None:
        _settings = MothershipSettings.from_env()
    return _settings


def reload_settings() -> MothershipSettings:
    """Force reload settings from environment."""
    global _settings
    get_settings.cache_clear()
    _settings = MothershipSettings.from_env()
    return _settings


# Convenience export
settings = get_settings()

try:
    from .inference_abrasiveness import (
        AbrasivenessCadence,
        AbrasivenessThresholds,
        InferenceAbrasivenessConfig,
        InferenceAbrasivenessLevel,
        InferenceCleanupSettings,
    )
except ImportError:
    # Fallback if module not available
    AbrasivenessCadence = None  # type: ignore
    AbrasivenessThresholds = None  # type: ignore
    InferenceAbrasivenessConfig = None  # type: ignore
    InferenceAbrasivenessLevel = None  # type: ignore
    InferenceCleanupSettings = None  # type: ignore

__all__ = [
    # Main configuration
    "MothershipSettings",
    "get_settings",
    # Subsystem settings
    "ServerSettings",
    "DatabaseSettings",
    "SecuritySettings",
    "IntegrationSettings",
    "TelemetrySettings",
    "CockpitSettings",
    "PaymentSettings",
    "BillingSettings",
    # Enums
    "Environment",
    "LogLevel",
    # Inference abrasiveness (if available)
    *(["AbrasivenessCadence"] if AbrasivenessCadence is not None else []),
    *(["AbrasivenessThresholds"] if AbrasivenessThresholds is not None else []),
    *(["InferenceAbrasivenessConfig"] if InferenceAbrasivenessConfig is not None else []),
    *(["InferenceAbrasivenessLevel"] if InferenceAbrasivenessLevel is not None else []),
    *(["InferenceCleanupSettings"] if InferenceCleanupSettings is not None else []),
]
