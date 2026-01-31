"""
Unified Fabric - Event Schemas
===============================
Defines event schema metadata for cross-project validation.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EventSchema:
    """Schema metadata for event payload validation."""

    event_type: str
    domain: str
    required_keys: tuple[str, ...] = ()
    optional_keys: tuple[str, ...] = ()
    description: str = ""


@dataclass
class ValidationResult:
    """Result of event schema validation."""

    is_valid: bool
    missing_keys: list[str] = field(default_factory=list)
    message: str = ""
    schema: EventSchema | None = None


_SCHEMA_REGISTRY: dict[str, EventSchema] = {}


def register_schema(schema: EventSchema) -> None:
    """Register a schema for a specific event type or wildcard pattern."""
    _SCHEMA_REGISTRY[schema.event_type] = schema


def register_schemas(schemas: Iterable[EventSchema]) -> None:
    """Register multiple schemas."""
    for schema in schemas:
        register_schema(schema)


def get_schema(event_type: str) -> EventSchema | None:
    """Find a schema by exact type or wildcard prefix (e.g. safety.*)."""
    if event_type in _SCHEMA_REGISTRY:
        return _SCHEMA_REGISTRY[event_type]

    for pattern, schema in _SCHEMA_REGISTRY.items():
        if pattern.endswith(".*") and event_type.startswith(pattern[:-2]):
            return schema

    return None


def validate_event(event_type: str, payload: dict) -> ValidationResult:
    """Validate an event payload against a registered schema."""
    schema = get_schema(event_type)
    if schema is None:
        return ValidationResult(is_valid=True, schema=None)

    missing = [key for key in schema.required_keys if key not in payload]
    if missing:
        return ValidationResult(
            is_valid=False,
            missing_keys=missing,
            message=f"Missing required keys: {', '.join(missing)}",
            schema=schema,
        )

    return ValidationResult(is_valid=True, schema=schema)


def bootstrap_default_schemas() -> None:
    """Register baseline event schemas for cross-project integration."""
    register_schemas(
        [
            EventSchema(
                event_type="safety.validation_required",
                domain="safety",
                required_keys=("context", "request_id"),
                optional_keys=("content", "pii_types", "severity", "metadata"),
                description="Safety validation request",
            ),
            EventSchema(
                event_type="safety.violation_detected",
                domain="safety",
                required_keys=("violation_type", "severity"),
                optional_keys=("details", "request_id", "correlation_id"),
                description="Security or safety violation event",
            ),
            EventSchema(
                event_type="safety.audit_replication",
                domain="safety",
                required_keys=("audit_entry_id", "project_id"),
                optional_keys=("details", "severity"),
                description="Audit replication payload",
            ),
            EventSchema(
                event_type="safety.*",
                domain="safety",
                description="Safety domain wildcard",
            ),
            EventSchema(
                event_type="grid.case.*",
                domain="grid",
                required_keys=("case_id",),
                optional_keys=("status", "metadata"),
                description="GRID case lifecycle events",
            ),
            EventSchema(
                event_type="grid.knowledge.shared",
                domain="grid",
                required_keys=("skill_name",),
                optional_keys=("capability", "patterns"),
                description="Knowledge sharing payload",
            ),
            EventSchema(
                event_type="coinbase.action.*",
                domain="coinbase",
                required_keys=("action_id", "action_type"),
                optional_keys=("asset", "amount", "metadata"),
                description="Coinbase portfolio action events",
            ),
            EventSchema(
                event_type="coinbase.signal.*",
                domain="coinbase",
                required_keys=("signal_id", "signal_type"),
                optional_keys=("asset", "confidence", "metadata"),
                description="Coinbase trading signal events",
            ),
        ]
    )


bootstrap_default_schemas()

__all__ = [
    "EventSchema",
    "ValidationResult",
    "register_schema",
    "register_schemas",
    "get_schema",
    "validate_event",
]
