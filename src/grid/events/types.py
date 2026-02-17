"""
Event Type Definitions for GRID Event-Driven I/O System.

Provides enumerated event types and categories for consistent
event classification across the GRID processing pipeline.

Categories:
- INPUT: Events from input gateways (CLI, API, File, WebSocket)
- PROCESSING: Events from processing pipeline stages
- OUTPUT: Events for response handling and formatting
- SECURITY: Security-related events (threats, access, content)
- SYSTEM: System lifecycle and error events
- NAVIGATION: Navigation agent system events
"""

from __future__ import annotations

from enum import Enum


class EventCategory(str, Enum):
    """High-level event categories for filtering and routing."""

    INPUT = "input"
    PROCESSING = "processing"
    OUTPUT = "output"
    SECURITY = "security"
    SYSTEM = "system"
    NAVIGATION = "navigation"
    LEARNING = "learning"
    INTEGRATION = "integration"


class EventType(str, Enum):
    """
    Enumeration of all event types in GRID.

    Naming convention: {CATEGORY}_{SUBCATEGORY}_{ACTION}
    """

    # ─────────────────────────────────────────────────────────────
    # Input Layer Events
    # ─────────────────────────────────────────────────────────────
    CLI_INPUT = "input:cli:received"
    CLI_COMMAND = "input:cli:command"
    CLI_ARGS_PARSED = "input:cli:args_parsed"

    API_INPUT = "input:api:received"
    API_REQUEST = "input:api:request"
    API_VALIDATED = "input:api:validated"

    FILE_INPUT = "input:file:received"
    FILE_CHANGED = "input:file:changed"
    FILE_CREATED = "input:file:created"
    FILE_DELETED = "input:file:deleted"

    WEBSOCKET_INPUT = "input:websocket:received"
    WEBSOCKET_CONNECTED = "input:websocket:connected"
    WEBSOCKET_DISCONNECTED = "input:websocket:disconnected"
    WEBSOCKET_MESSAGE = "input:websocket:message"

    # ─────────────────────────────────────────────────────────────
    # Processing Layer Events
    # ─────────────────────────────────────────────────────────────
    PROCESSING_STARTED = "processing:pipeline:started"
    PROCESSING_COMPLETED = "processing:pipeline:completed"
    PROCESSING_FAILED = "processing:pipeline:failed"

    TOKENIZATION_STARTED = "processing:tokenizer:started"
    TOKENIZATION_COMPLETED = "processing:tokenizer:completed"

    OPTIMIZATION_STARTED = "processing:optimizer:started"
    OPTIMIZATION_COMPLETED = "processing:optimizer:completed"

    CLASSIFICATION_STARTED = "processing:classifier:started"
    CLASSIFICATION_COMPLETED = "processing:classifier:completed"

    ANALYSIS_STARTED = "processing:analysis:started"
    ANALYSIS_COMPLETED = "processing:analysis:completed"

    ENTITY_EXTRACTED = "processing:entity:extracted"
    PATTERN_DETECTED = "processing:pattern:detected"

    # ─────────────────────────────────────────────────────────────
    # Output Layer Events
    # ─────────────────────────────────────────────────────────────
    RESPONSE_READY = "output:response:ready"
    RESPONSE_FORMATTED = "output:response:formatted"
    RESPONSE_SENT = "output:response:sent"

    OUTPUT_CLI = "output:cli:sent"
    OUTPUT_API = "output:api:sent"
    OUTPUT_FILE = "output:file:written"
    OUTPUT_WEBSOCKET = "output:websocket:emitted"

    ERROR_RESPONSE = "output:error:sent"

    # ─────────────────────────────────────────────────────────────
    # Security Events
    # ─────────────────────────────────────────────────────────────
    SECURITY_CHECK_STARTED = "security:check:started"
    SECURITY_CHECK_PASSED = "security:check:passed"
    SECURITY_CHECK_FAILED = "security:check:failed"

    THREAT_DETECTED = "security:threat:detected"
    THREAT_BLOCKED = "security:threat:blocked"
    THREAT_REPORTED = "security:threat:reported"

    ACCESS_REQUESTED = "security:access:requested"
    ACCESS_GRANTED = "security:access:granted"
    ACCESS_DENIED = "security:access:denied"

    AUTH_ATTEMPTED = "security:auth:attempted"
    AUTH_SUCCESS = "security:auth:success"
    AUTH_FAILURE = "security:auth:failure"
    AUTH_TOKEN_GENERATED = "security:auth:token_generated"
    AUTH_TOKEN_EXPIRED = "security:auth:token_expired"

    CONTENT_ANALYZED = "security:content:analyzed"
    CONTENT_BLOCKED = "security:content:blocked"
    CONTENT_SANITIZED = "security:content:sanitized"

    PRIVACY_PII_DETECTED = "security:privacy:pii_detected"
    PRIVACY_DATA_ANONYMIZED = "security:privacy:anonymized"

    AUDIT_LOGGED = "security:audit:logged"
    AUDIT_ALERT = "security:audit:alert"

    RATE_LIMIT_CHECKED = "security:rate:checked"
    RATE_LIMIT_EXCEEDED = "security:rate:exceeded"

    # ─────────────────────────────────────────────────────────────
    # System Events
    # ─────────────────────────────────────────────────────────────
    SYSTEM_STARTUP = "system:lifecycle:startup"
    SYSTEM_SHUTDOWN = "system:lifecycle:shutdown"
    SYSTEM_READY = "system:lifecycle:ready"

    ERROR_OCCURRED = "system:error:occurred"
    ERROR_HANDLED = "system:error:handled"
    ERROR_CRITICAL = "system:error:critical"

    CONFIG_LOADED = "system:config:loaded"
    CONFIG_CHANGED = "system:config:changed"

    HEALTH_CHECK = "system:health:check"
    HEALTH_DEGRADED = "system:health:degraded"
    HEALTH_RESTORED = "system:health:restored"

    METRICS_COLLECTED = "system:metrics:collected"
    PERFORMANCE_ALERT = "system:performance:alert"

    # ─────────────────────────────────────────────────────────────
    # Navigation Agent Events
    # ─────────────────────────────────────────────────────────────
    NAVIGATION_REQUESTED = "navigation:request:received"
    NAVIGATION_STARTED = "navigation:request:started"
    NAVIGATION_COMPLETED = "navigation:request:completed"
    NAVIGATION_FAILED = "navigation:request:failed"

    PATH_GENERATED = "navigation:path:generated"
    PATH_SELECTED = "navigation:path:selected"
    PATH_OPTIMIZED = "navigation:path:optimized"
    PATH_REJECTED = "navigation:path:rejected"

    AGENT_REGISTERED = "navigation:agent:registered"
    AGENT_STARTED = "navigation:agent:started"
    AGENT_STOPPED = "navigation:agent:stopped"
    AGENT_ERROR = "navigation:agent:error"

    # ─────────────────────────────────────────────────────────────
    # Learning Events
    # ─────────────────────────────────────────────────────────────
    LEARNING_UPDATED = "learning:model:updated"
    LEARNING_EPOCH_COMPLETED = "learning:epoch:completed"
    LEARNING_ADAPTATION_TRIGGERED = "learning:adaptation:triggered"

    OUTCOME_RECORDED = "learning:outcome:recorded"
    PATTERN_LEARNED = "learning:pattern:learned"
    WEIGHT_ADJUSTED = "learning:weight:adjusted"

    ACCURACY_IMPROVED = "learning:accuracy:improved"
    ACCURACY_DEGRADED = "learning:accuracy:degraded"

    # ─────────────────────────────────────────────────────────────
    # Integration Events
    # ─────────────────────────────────────────────────────────────
    EXTERNAL_SERVICE_CALLED = "integration:external:called"
    EXTERNAL_SERVICE_SUCCESS = "integration:external:success"
    EXTERNAL_SERVICE_FAILURE = "integration:external:failure"

    WEBHOOK_RECEIVED = "integration:webhook:received"
    WEBHOOK_SENT = "integration:webhook:sent"

    CACHE_HIT = "integration:cache:hit"
    CACHE_MISS = "integration:cache:miss"
    CACHE_INVALIDATED = "integration:cache:invalidated"

    @classmethod
    def get_category(cls, event_type: EventType) -> EventCategory:
        """Get the category for an event type."""
        type_str = event_type.value
        prefix = type_str.split(":")[0]

        category_map = {
            "input": EventCategory.INPUT,
            "processing": EventCategory.PROCESSING,
            "output": EventCategory.OUTPUT,
            "security": EventCategory.SECURITY,
            "system": EventCategory.SYSTEM,
            "navigation": EventCategory.NAVIGATION,
            "learning": EventCategory.LEARNING,
            "integration": EventCategory.INTEGRATION,
        }

        return category_map.get(prefix, EventCategory.SYSTEM)

    @classmethod
    def get_by_category(cls, category: EventCategory) -> list[EventType]:
        """Get all event types for a category."""
        prefix = category.value
        return [et for et in cls if et.value.startswith(prefix)]

    @classmethod
    def is_error_event(cls, event_type: EventType) -> bool:
        """Check if an event type represents an error."""
        error_keywords = ["error", "failed", "failure", "denied", "blocked", "exceeded"]
        return any(kw in event_type.value.lower() for kw in error_keywords)

    @classmethod
    def is_security_event(cls, event_type: EventType) -> bool:
        """Check if an event type is security-related."""
        return event_type.value.startswith("security:")

    @classmethod
    def requires_audit(cls, event_type: EventType) -> bool:
        """Check if an event type requires audit logging."""
        audit_required = [
            "security:",
            "auth:",
            "access:",
            "error:critical",
            "threat:",
        ]
        return any(event_type.value.startswith(prefix) or prefix in event_type.value for prefix in audit_required)
