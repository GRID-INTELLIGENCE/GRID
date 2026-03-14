"""
Shared Configuration Library for GRID ecosystem.

Provides modern, reusable configuration patterns extracted from Mothership:
- Dataclass-first architecture with frozen/slots optimizations
- Factory pattern (replaces singleton anti-pattern)
- Environment-aware validation
- Database fallback chains
- Secret redaction utilities

Usage:
    from infrastructure.config import SettingsBase, SettingsFactory
    from infrastructure.config.parsing import parse_bool, parse_list
    from infrastructure.config.validation import EnvironmentAwareValidator

Database:
    from infrastructure.config.database import (
        DatabaseFallbackChain,
        normalize_async_url,
        ConnectionRetry,
    )

Security:
    from infrastructure.config.security import (
        mask_secret,
        validate_secret_strength,
        generate_secure_secret,
    )

Testing:
    from infrastructure.config.testing import test_settings_env, mock_env
"""

from .base import EnvironmentInfo, SettingsBase
from .factory import (
    FactoryConfig,
    SettingsFactory,
    cached_settings,
    clear_all_caches,
    get_factory,
    get_registered_settings,
    register_factory,
)
from .parsing import (
    EnvParser,
    parse_bool,
    parse_float,
    parse_int,
    parse_json,
    parse_list,
    parse_path,
    parse_url,
)
from .validation import (
    EnvironmentAwareValidator,
    ValidationBuilder,
    ValidationIssue,
    ValidationMode,
    ValidationSeverity,
    validate_production_ready,
)

__all__ = [
    # Base classes
    "SettingsBase",
    "EnvironmentInfo",
    # Factory
    "SettingsFactory",
    "FactoryConfig",
    "register_factory",
    "get_factory",
    "get_registered_settings",
    "clear_all_caches",
    "cached_settings",
    # Parsing utilities
    "parse_bool",
    "parse_int",
    "parse_float",
    "parse_list",
    "parse_json",
    "parse_url",
    "parse_path",
    "EnvParser",
    # Validation
    "EnvironmentAwareValidator",
    "ValidationMode",
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationBuilder",
    "validate_production_ready",
]
