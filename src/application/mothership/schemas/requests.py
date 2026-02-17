"""
Mothership Cockpit Request Schemas.

Pydantic models for validating incoming API requests with comprehensive
field validation, custom validators, and documentation.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

# =============================================================================
# Base Configuration
# =============================================================================


class BaseRequest(BaseModel):
    """Base request model with common configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        populate_by_name=True,
    )


# =============================================================================
# Enums for Request Validation
# =============================================================================


class TaskPriorityRequest(StrEnum):
    """Task priority levels for requests."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class AlertSeverityRequest(StrEnum):
    """Alert severity levels for requests."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ComponentTypeRequest(StrEnum):
    """Component types for requests."""

    API_SERVER = "api_server"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    WORKER = "worker"
    SCHEDULER = "scheduler"
    INTEGRATION = "integration"
    WEBSOCKET = "websocket"
    MONITOR = "monitor"


class OperationModeRequest(StrEnum):
    """Cockpit operation modes for requests."""

    NORMAL = "normal"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"
    READONLY = "readonly"
    RECOVERY = "recovery"


# =============================================================================
# Session Requests
# =============================================================================


class SessionCreateRequest(BaseRequest):
    """Request to create a new session."""

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique identifier of the user",
        examples=["user_abc123"],
    )
    username: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Display name of the user",
        examples=["john.doe"],
    )
    permissions: list[str] = Field(
        default_factory=list,
        description="List of permission strings",
        examples=[["read", "write", "admin"]],
    )
    ip_address: str | None = Field(
        default=None,
        description="Client IP address",
        examples=["192.168.1.1"],
    )
    user_agent: str | None = Field(
        default=None,
        max_length=512,
        description="Client user agent string",
    )
    ttl_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
        description="Session time-to-live in minutes",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional session metadata",
    )

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: list[str]) -> list[str]:
        """Ensure permissions are lowercase and unique."""
        return list(set(p.lower().strip() for p in v if p.strip()))

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: str | None) -> str | None:
        """Basic IP address validation."""
        if v is None:
            return v
        # Simple validation - in production use ipaddress module
        parts = v.split(".")
        if len(parts) == 4:
            try:
                if all(0 <= int(p) <= 255 for p in parts):
                    return v
            except ValueError:
                pass
        # Allow IPv6 or other formats through
        if ":" in v:
            return v
        raise ValueError("Invalid IP address format")


class SessionUpdateRequest(BaseRequest):
    """Request to update an existing session."""

    permissions: list[str] | None = Field(
        default=None,
        description="Updated permissions list",
    )
    extend_minutes: int | None = Field(
        default=None,
        ge=1,
        le=1440,
        description="Extend session by this many minutes",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Updated metadata (merged with existing)",
    )


class SessionTerminateRequest(BaseRequest):
    """Request to terminate sessions."""

    session_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of session IDs to terminate",
    )
    reason: str | None = Field(
        default=None,
        max_length=256,
        description="Reason for termination",
    )
    force: bool = Field(
        default=False,
        description="Force terminate even active sessions",
    )


# =============================================================================
# Task Requests
# =============================================================================


class TaskCreateRequest(BaseRequest):
    """Request to create and schedule a new task."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Human-readable task name",
        examples=["Sync Integration Data"],
    )
    task_type: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Task type identifier (snake_case)",
        examples=["sync_data", "run_diagnostic"],
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Task-specific input data",
    )
    priority: TaskPriorityRequest = Field(
        default=TaskPriorityRequest.NORMAL,
        description="Task priority level",
    )
    scheduled_at: datetime | None = Field(
        default=None,
        description="When to execute the task (UTC)",
    )
    timeout_seconds: int = Field(
        default=300,
        ge=1,
        le=86400,
        description="Task timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts on failure",
    )
    tags: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Tags for categorization",
    )
    idempotency_key: str | None = Field(
        default=None,
        max_length=64,
        description="Key for deduplication",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Ensure tags are lowercase and valid."""
        validated = []
        for tag in v:
            tag = tag.lower().strip()
            if tag and len(tag) <= 32:
                validated.append(tag)
        return list(set(validated))[:10]  # Max 10 unique tags


class TaskUpdateRequest(BaseRequest):
    """Request to update a task."""

    priority: TaskPriorityRequest | None = Field(
        default=None,
        description="Updated priority",
    )
    timeout_seconds: int | None = Field(
        default=None,
        ge=1,
        le=86400,
        description="Updated timeout",
    )
    max_retries: int | None = Field(
        default=None,
        ge=0,
        le=10,
        description="Updated max retries",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Updated tags",
    )


class TaskProgressRequest(BaseRequest):
    """Request to update task progress."""

    progress: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Progress percentage (0-100)",
    )
    message: str = Field(
        default="",
        max_length=256,
        description="Progress status message",
    )


class TaskActionRequest(BaseRequest):
    """Request to perform an action on a task."""

    action: str = Field(
        ...,
        pattern=r"^(cancel|pause|resume|retry)$",
        description="Action to perform",
    )
    reason: str | None = Field(
        default=None,
        max_length=256,
        description="Reason for the action",
    )


class TaskBulkActionRequest(BaseRequest):
    """Request to perform bulk action on multiple tasks."""

    task_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of task IDs",
    )
    action: str = Field(
        ...,
        pattern=r"^(cancel|pause|resume|retry)$",
        description="Action to perform",
    )


# =============================================================================
# Component Requests
# =============================================================================


class ComponentRegisterRequest(BaseRequest):
    """Request to register a new component."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Component name",
        examples=["api-gateway"],
    )
    component_type: ComponentTypeRequest = Field(
        ...,
        description="Type of component",
    )
    host: str = Field(
        default="localhost",
        max_length=256,
        description="Component hostname or IP",
    )
    port: int = Field(
        default=0,
        ge=0,
        le=65535,
        description="Component port (0 = default)",
    )
    version: str = Field(
        default="1.0.0",
        max_length=32,
        pattern=r"^[0-9]+\.[0-9]+\.[0-9]+",
        description="Component version (semver)",
    )
    health_check_url: str | None = Field(
        default=None,
        max_length=512,
        description="Health check endpoint URL",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="List of component IDs this depends on",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional component metadata",
    )


class ComponentUpdateRequest(BaseRequest):
    """Request to update a component."""

    enabled: bool | None = Field(
        default=None,
        description="Enable or disable the component",
    )
    host: str | None = Field(
        default=None,
        max_length=256,
        description="Updated hostname",
    )
    port: int | None = Field(
        default=None,
        ge=0,
        le=65535,
        description="Updated port",
    )
    version: str | None = Field(
        default=None,
        max_length=32,
        description="Updated version",
    )
    health_check_url: str | None = Field(
        default=None,
        max_length=512,
        description="Updated health check URL",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Updated metadata (merged)",
    )


class ComponentHealthReportRequest(BaseRequest):
    """Request to report component health status."""

    component_id: str = Field(
        ...,
        min_length=1,
        description="Component identifier",
    )
    healthy: bool = Field(
        ...,
        description="Whether component is healthy",
    )
    message: str = Field(
        default="",
        max_length=512,
        description="Health status message",
    )
    metrics: dict[str, float] | None = Field(
        default=None,
        description="Optional metrics snapshot",
    )


# =============================================================================
# Alert Requests
# =============================================================================


class AlertCreateRequest(BaseRequest):
    """Request to create a new alert."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Alert title",
        examples=["High CPU Usage"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="Detailed alert message",
    )
    severity: AlertSeverityRequest = Field(
        default=AlertSeverityRequest.INFO,
        description="Alert severity level",
    )
    source: str = Field(
        default="system",
        max_length=64,
        description="Source of the alert",
    )
    component_id: str | None = Field(
        default=None,
        description="Associated component ID",
    )
    metric_name: str | None = Field(
        default=None,
        max_length=64,
        description="Associated metric name",
    )
    metric_value: float | None = Field(
        default=None,
        description="Current metric value",
    )
    threshold: float | None = Field(
        default=None,
        description="Threshold that was exceeded",
    )
    tags: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Alert tags",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional alert context",
    )

    @model_validator(mode="after")
    def validate_metric_fields(self) -> AlertCreateRequest:
        """Ensure metric fields are consistent."""
        if self.metric_value is not None and self.metric_name is None:
            raise ValueError("metric_name is required when metric_value is provided")
        return self


class AlertAcknowledgeRequest(BaseRequest):
    """Request to acknowledge an alert."""

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="ID of user acknowledging the alert",
    )
    note: str | None = Field(
        default=None,
        max_length=512,
        description="Optional acknowledgment note",
    )


class AlertResolveRequest(BaseRequest):
    """Request to resolve an alert."""

    resolution_note: str | None = Field(
        default=None,
        max_length=1024,
        description="Note about how the alert was resolved",
    )
    auto_resolved: bool = Field(
        default=False,
        description="Whether this was auto-resolved",
    )


class AlertBulkActionRequest(BaseRequest):
    """Request for bulk alert actions."""

    alert_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of alert IDs",
    )
    action: str = Field(
        ...,
        pattern=r"^(acknowledge|resolve|delete)$",
        description="Action to perform",
    )
    user_id: str | None = Field(
        default=None,
        description="User performing the action",
    )


# =============================================================================
# Integration Requests
# =============================================================================


class IntegrationSyncRequest(BaseRequest):
    """Request to sync with an external integration."""

    integration_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Integration identifier",
        examples=["gemini_studio"],
    )
    sync_type: str = Field(
        default="full",
        pattern=r"^(full|incremental|delta)$",
        description="Type of synchronization",
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Sync-specific options",
    )
    force: bool = Field(
        default=False,
        description="Force sync even if recently synced",
    )


class IntegrationConfigRequest(BaseRequest):
    """Request to update integration configuration."""

    enabled: bool | None = Field(
        default=None,
        description="Enable or disable integration",
    )
    api_url: str | None = Field(
        default=None,
        max_length=512,
        description="API endpoint URL",
    )
    api_key: str | None = Field(
        default=None,
        max_length=256,
        description="API key (will be encrypted)",
    )
    timeout_seconds: int | None = Field(
        default=None,
        ge=1,
        le=300,
        description="Request timeout",
    )
    rate_limit_rpm: int | None = Field(
        default=None,
        ge=1,
        le=10000,
        description="Rate limit (requests per minute)",
    )
    custom_config: dict[str, Any] | None = Field(
        default=None,
        description="Integration-specific configuration",
    )


class GeminiPromptRequest(BaseRequest):
    """Request to send a prompt to Gemini integration."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=32000,
        description="Prompt text",
    )
    model: str | None = Field(
        default=None,
        max_length=64,
        description="Model to use",
        examples=["gemini-1.5-pro", "gemini-1.5-flash"],
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    max_tokens: int = Field(
        default=2048,
        ge=1,
        le=32000,
        description="Maximum output tokens",
    )
    system_instruction: str | None = Field(
        default=None,
        max_length=8000,
        description="System instruction",
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response",
    )


# =============================================================================
# System Requests
# =============================================================================


class SystemModeRequest(BaseRequest):
    """Request to change system operation mode."""

    mode: OperationModeRequest = Field(
        ...,
        description="Target operation mode",
    )
    reason: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Reason for mode change",
    )
    scheduled_end: datetime | None = Field(
        default=None,
        description="When to automatically exit this mode",
    )
    notify_users: bool = Field(
        default=True,
        description="Notify connected users of mode change",
    )


class SystemConfigRequest(BaseRequest):
    """Request to update system configuration."""

    config_key: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-z][a-z0-9_.]*$",
        description="Configuration key (dot notation)",
    )
    config_value: Any = Field(
        ...,
        description="Configuration value",
    )
    persist: bool = Field(
        default=True,
        description="Persist to configuration store",
    )


class DiagnosticRequest(BaseRequest):
    """Request to run system diagnostics."""

    check_types: list[str] = Field(
        default_factory=lambda: ["all"],
        description="Types of checks to run",
        examples=[["connectivity", "database", "integrations"]],
    )
    include_details: bool = Field(
        default=True,
        description="Include detailed results",
    )
    timeout_seconds: int = Field(
        default=60,
        ge=5,
        le=300,
        description="Diagnostic timeout",
    )


# =============================================================================
# Query/Filter Requests
# =============================================================================


class PaginationRequest(BaseRequest):
    """Common pagination parameters."""

    page: int = Field(
        default=1,
        ge=1,
        le=10000,
        description="Page number",
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page",
    )
    sort_by: str | None = Field(
        default=None,
        max_length=64,
        description="Field to sort by",
    )
    sort_order: str = Field(
        default="desc",
        pattern=r"^(asc|desc)$",
        description="Sort order",
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class TaskFilterRequest(PaginationRequest):
    """Request to filter tasks."""

    status: list[str] | None = Field(
        default=None,
        description="Filter by status(es)",
    )
    priority: list[str] | None = Field(
        default=None,
        description="Filter by priority(ies)",
    )
    task_type: str | None = Field(
        default=None,
        description="Filter by task type",
    )
    created_after: datetime | None = Field(
        default=None,
        description="Filter tasks created after this time",
    )
    created_before: datetime | None = Field(
        default=None,
        description="Filter tasks created before this time",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Filter by tags (any match)",
    )
    search: str | None = Field(
        default=None,
        max_length=256,
        description="Search in task name",
    )


class AlertFilterRequest(PaginationRequest):
    """Request to filter alerts."""

    severity: list[str] | None = Field(
        default=None,
        description="Filter by severity(ies)",
    )
    acknowledged: bool | None = Field(
        default=None,
        description="Filter by acknowledgment status",
    )
    resolved: bool | None = Field(
        default=None,
        description="Filter by resolution status",
    )
    component_id: str | None = Field(
        default=None,
        description="Filter by component",
    )
    created_after: datetime | None = Field(
        default=None,
        description="Filter alerts created after this time",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Filter by tags",
    )


__all__ = [
    # Base
    "BaseRequest",
    # Enums
    "TaskPriorityRequest",
    "AlertSeverityRequest",
    "ComponentTypeRequest",
    "OperationModeRequest",
    # Session
    "SessionCreateRequest",
    "SessionUpdateRequest",
    "SessionTerminateRequest",
    # Task
    "TaskCreateRequest",
    "TaskUpdateRequest",
    "TaskProgressRequest",
    "TaskActionRequest",
    "TaskBulkActionRequest",
    # Component
    "ComponentRegisterRequest",
    "ComponentUpdateRequest",
    "ComponentHealthReportRequest",
    # Alert
    "AlertCreateRequest",
    "AlertAcknowledgeRequest",
    "AlertResolveRequest",
    "AlertBulkActionRequest",
    # Integration
    "IntegrationSyncRequest",
    "IntegrationConfigRequest",
    "GeminiPromptRequest",
    # System
    "SystemModeRequest",
    "SystemConfigRequest",
    "DiagnosticRequest",
    # Query/Filter
    "PaginationRequest",
    "TaskFilterRequest",
    "AlertFilterRequest",
]
