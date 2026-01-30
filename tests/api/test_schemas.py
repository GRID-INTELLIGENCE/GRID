"""
Unit tests for Activity Resonance API schemas.

Tests Pydantic validation, field constraints, and schema serialization.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from application.resonance.api.schemas import (
    ActivityCompleteResponse,
    ActivityEventResponse,
    ActivityEventsResponse,
    ActivityProcessRequest,
    ActivityType,
    ContextMetricsResponse,
    ContextQueryRequest,
    ContextResponse,
    EnvelopeMetricsResponse,
    ErrorResponse,
    PathTriageRequest,
    ResonanceResponse,
    WebSocketFeedbackMessage,
)


class TestActivityProcessRequest:
    """Test ActivityProcessRequest schema."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = ActivityProcessRequest(
            query="create a new service",
            activity_type=ActivityType.CODE,
            context={"urgency": True},
        )
        assert request.query == "create a new service"
        assert request.activity_type == ActivityType.CODE
        assert request.context == {"urgency": True}

    def test_minimal_request(self):
        """Test request with minimal fields."""
        request = ActivityProcessRequest(query="test query")
        assert request.query == "test query"
        assert request.activity_type == ActivityType.GENERAL
        assert request.context == {}

    def test_query_too_short(self):
        """Test validation error for query too short."""
        with pytest.raises(ValidationError):
            ActivityProcessRequest(query="")

    def test_query_too_long(self):
        """Test validation error for query too long."""
        with pytest.raises(ValidationError):
            ActivityProcessRequest(query="x" * 1001)


class TestContextQueryRequest:
    """Test ContextQueryRequest schema."""

    def test_valid_request(self):
        """Test valid context query request."""
        request = ContextQueryRequest(
            query="test query",
            context_type="code",
            max_length=500,
        )
        assert request.query == "test query"
        assert request.context_type == "code"
        assert request.max_length == 500

    def test_max_length_constraints(self):
        """Test max_length validation."""
        with pytest.raises(ValidationError):
            ContextQueryRequest(query="test", max_length=49)  # Too small

        with pytest.raises(ValidationError):
            ContextQueryRequest(query="test", max_length=2001)  # Too large


class TestContextResponse:
    """Test ContextResponse schema."""

    def test_valid_response(self):
        """Test valid context response."""
        metrics = ContextMetricsResponse(
            sparsity=0.5,
            attention_tension=0.3,
            decision_pressure=0.4,
            clarity=0.9,
            confidence=0.8,
        )
        response = ContextResponse(
            content="Test context",
            source="application/code",
            metrics=metrics,
            timestamp=1234567890.0,
            relevance_score=0.7,
        )
        assert response.content == "Test context"
        assert response.metrics.sparsity == 0.5
        assert response.relevance_score == 0.7

    def test_metrics_validation(self):
        """Test metrics value constraints."""
        with pytest.raises(ValidationError):
            ContextMetricsResponse(
                sparsity=1.5,  # > 1.0
                attention_tension=0.5,
                decision_pressure=0.5,
                clarity=0.5,
                confidence=0.5,
            )


class TestPathTriageRequest:
    """Test PathTriageRequest schema."""

    def test_valid_request(self):
        """Test valid path triage request."""
        request = PathTriageRequest(
            goal="implement feature",
            max_options=5,
        )
        assert request.goal == "implement feature"
        assert request.max_options == 5

    def test_max_options_constraints(self):
        """Test max_options validation."""
        with pytest.raises(ValidationError):
            PathTriageRequest(goal="test", max_options=0)  # Too small

        with pytest.raises(ValidationError):
            PathTriageRequest(goal="test", max_options=11)  # Too large


class TestResonanceResponse:
    """Test ResonanceResponse schema."""

    def test_valid_response(self):
        """Test valid resonance response."""
        response = ResonanceResponse(
            activity_id="test-id",
            state="active",
            urgency=0.5,
            message="Test message",
            timestamp=datetime.now(UTC),
        )
        assert response.activity_id == "test-id"
        assert response.state == "active"
        assert response.urgency == 0.5

    def test_urgency_constraints(self):
        """Test urgency value constraints."""
        with pytest.raises(ValidationError):
            ResonanceResponse(
                activity_id="test",
                state="active",
                urgency=1.5,  # > 1.0
                message="test",
            )


class TestEnvelopeMetricsResponse:
    """Test EnvelopeMetricsResponse schema."""

    def test_valid_response(self):
        """Test valid envelope metrics response."""
        response = EnvelopeMetricsResponse(
            phase="sustain",
            amplitude=0.7,
            velocity=0.0,
            time_in_phase=1.0,
            total_time=1.5,
            peak_amplitude=1.0,
        )
        assert response.phase == "sustain"
        assert response.amplitude == 0.7
        assert response.peak_amplitude == 1.0

    def test_amplitude_constraints(self):
        """Test amplitude value constraints."""
        with pytest.raises(ValidationError):
            EnvelopeMetricsResponse(
                phase="attack",
                amplitude=1.5,  # > 1.0
                velocity=0.0,
                time_in_phase=0.0,
                total_time=0.0,
                peak_amplitude=1.0,
            )


class TestActivityCompleteResponse:
    """Test ActivityCompleteResponse schema."""

    def test_valid_response(self):
        """Test valid activity complete response."""
        response = ActivityCompleteResponse(
            activity_id="test-id",
            completed=True,
            message="Completed",
            timestamp=datetime.now(UTC),
        )
        assert response.activity_id == "test-id"
        assert response.completed is True


class TestActivityEventResponse:
    """Test ActivityEventResponse schema."""

    def test_valid_response(self):
        """Test valid activity event response."""
        response = ActivityEventResponse(
            event_id="event-1",
            timestamp=1234567890.0,
            activity_type="general",
            payload={"key": "value"},
        )
        assert response.event_id == "event-1"
        assert response.activity_type == "general"


class TestActivityEventsResponse:
    """Test ActivityEventsResponse schema."""

    def test_valid_response(self):
        """Test valid activity events response."""
        events = [
            ActivityEventResponse(
                event_id="event-1",
                timestamp=1234567890.0,
                activity_type="general",
                payload={},
            )
        ]
        response = ActivityEventsResponse(
            activity_id="test-id",
            events=events,
            total=1,
        )
        assert response.activity_id == "test-id"
        assert len(response.events) == 1
        assert response.total == 1


class TestWebSocketFeedbackMessage:
    """Test WebSocketFeedbackMessage schema."""

    def test_valid_message(self):
        """Test valid WebSocket feedback message."""
        message = WebSocketFeedbackMessage(
            activity_id="test-id",
            state="active",
            urgency=0.5,
            message="Test feedback",
            timestamp=datetime.now(UTC),
        )
        assert message.activity_id == "test-id"
        assert message.state == "active"
        assert message.urgency == 0.5


class TestErrorResponse:
    """Test ErrorResponse schema."""

    def test_valid_error_response(self):
        """Test valid error response."""
        response = ErrorResponse(
            error="Test error",
            detail="Error detail",
            activity_id="test-id",
        )
        assert response.error == "Test error"
        assert response.detail == "Error detail"
        assert response.activity_id == "test-id"
