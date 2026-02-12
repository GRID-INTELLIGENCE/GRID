"""
Core Layer
==========
Core components for Coinbase system.
"""

from .attention_allocator import AttentionAllocator, FocusAllocation, FocusLevel
from .auth import (
    AuthConfig,
    AuthenticationError,
    AuthManager,
    AuthorizationError,
    UserRole,
    UserSession,
    get_auth_manager,
    require_auth,
)
from .backup_manager import (
    BackupConfig,
    BackupInfo,
    BackupManager,
    create_backup,
    get_backup_manager,
    restore_from_backup,
)
from .skill_cache import (
    CacheEntry,
    SkillCache,
    cache_skill_result,
    cached_skill_execution,
    get_cached_skill_result,
    get_skill_cache,
    invalidate_skill_cache,
)
from .webhook_manager import (
    WebhookConfig,
    WebhookEvent,
    WebhookManager,
    WebhookPayload,
    get_webhook_manager,
    register_price_webhook,
    trigger_price_alert,
)

__all__ = [
    "AttentionAllocator",
    "FocusAllocation",
    "FocusLevel",
    "SkillCache",
    "CacheEntry",
    "get_skill_cache",
    "cached_skill_execution",
    "invalidate_skill_cache",
    "cache_skill_result",
    "get_cached_skill_result",
    "BackupManager",
    "BackupConfig",
    "BackupInfo",
    "get_backup_manager",
    "create_backup",
    "restore_from_backup",
    "AuthManager",
    "AuthConfig",
    "UserSession",
    "UserRole",
    "get_auth_manager",
    "require_auth",
    "AuthenticationError",
    "AuthorizationError",
    "WebhookManager",
    "WebhookConfig",
    "WebhookPayload",
    "WebhookEvent",
    "get_webhook_manager",
    "register_price_webhook",
    "trigger_price_alert",
]
