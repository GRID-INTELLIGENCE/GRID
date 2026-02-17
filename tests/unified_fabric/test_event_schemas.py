"""
Tests for Unified Fabric - Event Schemas
"""

from unified_fabric.event_schemas import (
    EventSchema,
    get_schema,
    register_schema,
    validate_event,
)


def test_schema_registration_and_retrieval():
    test_schema = EventSchema(
        event_type="test.event",
        domain="test",
        required_keys=("a", "b"),
    )
    register_schema(test_schema)

    retrieved = get_schema("test.event")
    assert retrieved == test_schema
    assert retrieved.domain == "test"
    assert "a" in retrieved.required_keys


def test_wildcard_matching():
    # safety.* should already be registered by bootstrap
    retrieved = get_schema("safety.custom_event")
    assert retrieved is not None
    assert retrieved.domain == "safety"
    assert retrieved.event_type == "safety.*"


def test_validate_event_success():
    # Using bootstrapped schema: safety.validation_required
    payload = {"context": {"proj": "grid"}, "request_id": "123"}
    result = validate_event("safety.validation_required", payload)
    assert result.is_valid is True
    assert result.schema is not None


def test_validate_event_missing_keys():
    payload = {"context": {"proj": "grid"}}  # missing request_id
    result = validate_event("safety.validation_required", payload)
    assert result.is_valid is False
    assert "request_id" in result.missing_keys
    assert "Missing required keys" in result.message


def test_validate_no_schema():
    # Should be valid if no schema is found
    result = validate_event("unregistered.type", {"any": "thing"})
    assert result.is_valid is True
    assert result.schema is None
