"""
Integration tests for Parasite Guard components.

Tests ACK tracking, EventBus subscriptions, and Alerter functionality
in realistic scenarios.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# =============================================================================
# ACK Tracker Integration Tests
# =============================================================================


class TestAckTrackerIntegration:
    """Integration tests for WebSocket ACK tracking."""

    @pytest.fixture
    def ack_tracker(self):
        """Create an AckTracker instance."""
        from application.resonance.api.websocket import AckTracker

        return AckTracker(timeout_seconds=1.0, max_retries=2)

    @pytest.fixture
    def message_envelope(self):
        """Create a test MessageEnvelope."""
        from application.resonance.api.websocket import MessageEnvelope

        return MessageEnvelope(
            id=str(uuid.uuid4()),
            type="test",
            payload={"data": "test_value"},
            requires_ack=True,
        )

    @pytest.mark.asyncio
    async def test_send_with_ack_success(self, ack_tracker, message_envelope):
        """Test successful ACK receipt."""
        # Mock WebSocket
        mock_ws = AsyncMock()

        # Simulate ACK response
        ack_response = json.dumps(
            {
                "type": "ack",
                "ack_id": message_envelope.id,
                "status": "ok",
            }
        )
        mock_ws.receive_text = AsyncMock(return_value=ack_response)

        result = await ack_tracker.send_with_ack(mock_ws, message_envelope)

        assert result is True
        assert ack_tracker.pending_count == 0
        assert ack_tracker.stats["acks_received"] == 1

    @pytest.mark.asyncio
    async def test_send_with_ack_timeout(self, ack_tracker, message_envelope):
        """Test ACK timeout handling."""
        mock_ws = AsyncMock()

        # Simulate timeout
        mock_ws.receive_text = AsyncMock(side_effect=TimeoutError())

        result = await ack_tracker.send_with_ack(mock_ws, message_envelope)

        assert result is False
        assert ack_tracker.stats["timeouts"] > 0

    @pytest.mark.asyncio
    async def test_send_with_ack_nack(self, ack_tracker, message_envelope):
        """Test NACK handling."""
        mock_ws = AsyncMock()

        # Simulate NACK response
        nack_response = json.dumps(
            {
                "type": "ack",
                "ack_id": message_envelope.id,
                "status": "error",
                "error_code": "invalid_data",
            }
        )
        mock_ws.receive_text = AsyncMock(return_value=nack_response)

        result = await ack_tracker.send_with_ack(mock_ws, message_envelope)

        assert result is False

    @pytest.mark.asyncio
    async def test_message_envelope_serialization(self, message_envelope):
        """Test MessageEnvelope JSON serialization."""
        json_str = message_envelope.to_json()
        data = json.loads(json_str)

        assert data["id"] == message_envelope.id
        assert data["type"] == message_envelope.type
        assert data["payload"] == message_envelope.payload
        assert data["requires_ack"] == message_envelope.requires_ack

    @pytest.mark.asyncio
    async def test_pending_messages_tracking(self, ack_tracker, message_envelope):
        """Test tracking of pending messages."""
        mock_ws = AsyncMock()
        mock_ws.receive_text = AsyncMock(side_effect=TimeoutError())

        # Start send but don't wait for completion
        await ack_tracker.send_with_ack(mock_ws, message_envelope)

        # After timeout, pending should be cleared
        assert ack_tracker.pending_count == 0


# =============================================================================
# EventBus Subscription Integration Tests
# =============================================================================


class TestEventBusSubscriptionIntegration:
    """Integration tests for EventBus subscription handling."""

    @pytest.fixture
    async def event_bus(self):
        """Create an EventBus instance."""
        from infrastructure.event_bus.event_system import EventBus

        # Bypass singleton for testing
        bus = object.__new__(EventBus)
        bus.__init__()
        return bus

    @pytest.mark.asyncio
    async def test_subscribe_returns_handle(self, event_bus):
        """Test that subscribe returns a Subscription handle."""
        handler = AsyncMock()

        sub = await event_bus.subscribe("test.event", handler)

        assert sub is not None
        assert sub.event_type == "test.event"
        assert sub.id is not None
        assert sub.created_at > 0

    @pytest.mark.asyncio
    async def test_unsubscribe_by_handle(self, event_bus):
        """Test unsubscribing using the Subscription handle."""
        handler = AsyncMock()

        sub = await event_bus.subscribe("test.event", handler)
        initial_count = await event_bus.get_subscription_count()

        result = await event_bus.unsubscribe(sub)

        assert result is True
        assert await event_bus.get_subscription_count() == initial_count - 1

    @pytest.mark.asyncio
    async def test_unsubscribe_by_id(self, event_bus):
        """Test unsubscribing using just the subscription ID."""
        handler = AsyncMock()

        sub = await event_bus.subscribe("test.event", handler)
        initial_count = await event_bus.get_subscription_count()

        result = await event_bus.unsubscribe(sub.id)

        assert result is True
        assert await event_bus.get_subscription_count() == initial_count - 1

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, event_bus):
        """Test unsubscribing a non-existent subscription."""
        result = await event_bus.unsubscribe(uuid.uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_subscription_count_by_type(self, event_bus):
        """Test getting subscription count by event type."""
        handler = AsyncMock()

        await event_bus.subscribe("type.a", handler)
        await event_bus.subscribe("type.a", handler)
        await event_bus.subscribe("type.b", handler)

        count_a = await event_bus.get_subscription_count("type.a")
        count_b = await event_bus.get_subscription_count("type.b")
        total = await event_bus.get_subscription_count()

        assert count_a == 2
        assert count_b == 1
        assert total == 3

    @pytest.mark.asyncio
    async def test_clear_all_subscriptions(self, event_bus):
        """Test clearing all subscriptions."""
        handler = AsyncMock()

        await event_bus.subscribe("type.a", handler)
        await event_bus.subscribe("type.b", handler)
        await event_bus.subscribe("type.c", handler)

        cleared = await event_bus.clear_all()

        assert cleared == 3
        assert await event_bus.get_subscription_count() == 0

    @pytest.mark.asyncio
    async def test_subscription_serialization(self, event_bus):
        """Test Subscription.to_dict() serialization."""
        handler = AsyncMock()

        sub = await event_bus.subscribe("test.event", handler)
        data = sub.to_dict()

        assert "id" in data
        assert data["event_type"] == "test.event"
        assert "created_at" in data
        assert "handler_name" in data


# =============================================================================
# Alerter Integration Tests
# =============================================================================


class TestAlerterIntegration:
    """Integration tests for ParasiteAlerter."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        from infrastructure.parasite_guard.config import ParasiteGuardConfig

        return ParasiteGuardConfig()

    @pytest.fixture
    def state_machine(self):
        """Create a state machine instance."""
        from infrastructure.parasite_guard.state_machine import (
            GuardState,
            ParasiteGuardStateMachine,
        )

        sm = ParasiteGuardStateMachine()
        # Transition to MONITORING for testing
        sm.transition(GuardState.MONITORING)
        return sm

    @pytest.fixture
    def alerter(self, config, state_machine):
        """Create an alerter instance."""
        from infrastructure.parasite_guard.alerter import (
            InMemoryAlertChannel,
            ParasiteAlerter,
        )

        alerter = ParasiteAlerter(config, state_machine)
        # Add in-memory channel for testing
        alerter._in_memory = InMemoryAlertChannel()
        alerter.add_channel(alerter._in_memory)
        return alerter

    @pytest.fixture
    def parasite_context(self):
        """Create a test ParasiteContext."""
        from infrastructure.parasite_guard.models import (
            ParasiteContext,
            ParasiteSeverity,
        )

        return ParasiteContext(
            id=uuid.uuid4(),
            component="websocket",
            pattern="no_ack",
            rule="WebSocketNoAckDetector",
            severity=ParasiteSeverity.HIGH,
        )

    @pytest.mark.asyncio
    async def test_alert_sends_to_all_channels(self, alerter, parasite_context):
        """Test that alerts are sent to all configured channels."""
        from infrastructure.parasite_guard.contracts import Severity

        await alerter.alert(parasite_context, Severity.HIGH)

        # Check in-memory channel received the alert
        alerts = alerter._in_memory.alerts
        assert len(alerts) >= 1
        assert alerts[-1].component == "websocket"
        assert alerts[-1].pattern == "no_ack"

    @pytest.mark.asyncio
    async def test_alert_tracking(self, alerter, parasite_context):
        """Test that alerts are tracked."""
        from infrastructure.parasite_guard.contracts import Severity

        await alerter.alert(parasite_context, Severity.MEDIUM)

        stats = alerter.get_stats()
        assert stats["alerts_sent"] >= 1

        counts = alerter.get_alert_counts()
        assert counts.get("no_ack", 0) >= 1

    @pytest.mark.asyncio
    async def test_escalation_for_critical(self, alerter, parasite_context):
        """Test escalation for critical severity."""
        from infrastructure.parasite_guard.contracts import Severity
        from infrastructure.parasite_guard.models import ParasiteSeverity

        parasite_context.severity = ParasiteSeverity.CRITICAL

        await alerter.alert(parasite_context, Severity.CRITICAL)

        stats = alerter.get_stats()
        assert stats["escalations"] >= 1

    @pytest.mark.asyncio
    async def test_escalation_frequency_threshold(self, alerter, parasite_context):
        """Test escalation after multiple alerts."""
        from infrastructure.parasite_guard.contracts import Severity

        # Send multiple alerts for the same pattern
        for _ in range(5):
            await alerter.alert(parasite_context, Severity.HIGH)

        stats = alerter.get_stats()
        # Should have escalated due to frequency
        assert stats["escalations"] >= 1

    @pytest.mark.asyncio
    async def test_state_machine_transition_on_escalation(self, config, state_machine, parasite_context):
        """Test that escalation triggers state machine transition."""
        from infrastructure.parasite_guard.alerter import ParasiteAlerter
        from infrastructure.parasite_guard.contracts import Severity
        from infrastructure.parasite_guard.models import ParasiteSeverity
        from infrastructure.parasite_guard.state_machine import GuardState

        # Set up state machine in MITIGATING state
        state_machine.transition(GuardState.DETECTING)
        state_machine.transition(GuardState.MITIGATING)

        alerter = ParasiteAlerter(config, state_machine)
        parasite_context.severity = ParasiteSeverity.CRITICAL

        await alerter.escalate(parasite_context)

        assert state_machine.state == GuardState.ALERTING

    @pytest.mark.asyncio
    async def test_reset_escalations(self, alerter, parasite_context):
        """Test resetting escalation tracking."""
        from infrastructure.parasite_guard.contracts import Severity
        from infrastructure.parasite_guard.models import ParasiteSeverity

        parasite_context.severity = ParasiteSeverity.CRITICAL
        await alerter.alert(parasite_context, Severity.CRITICAL)

        initial_escalated = len(alerter._escalated_patterns)
        alerter.reset_escalations()

        assert len(alerter._escalated_patterns) == 0
        assert initial_escalated > 0  # Had escalations before reset


# =============================================================================
# State Machine Integration Tests
# =============================================================================


class TestStateMachineIntegration:
    """Integration tests for ParasiteGuardStateMachine."""

    @pytest.fixture
    def state_machine(self):
        """Create a state machine instance."""
        from infrastructure.parasite_guard.state_machine import ParasiteGuardStateMachine

        return ParasiteGuardStateMachine()

    def test_initial_state(self, state_machine):
        """Test initial state is INITIALIZING."""
        from infrastructure.parasite_guard.state_machine import GuardState

        assert state_machine.state == GuardState.INITIALIZING

    def test_valid_transition_sequence(self, state_machine):
        """Test a valid sequence of transitions."""
        from infrastructure.parasite_guard.state_machine import GuardState

        # INITIALIZING -> MONITORING
        state_machine.transition(GuardState.MONITORING)
        assert state_machine.state == GuardState.MONITORING

        # MONITORING -> DETECTING
        state_machine.transition(GuardState.DETECTING)
        assert state_machine.state == GuardState.DETECTING

        # DETECTING -> MITIGATING
        state_machine.transition(GuardState.MITIGATING)
        assert state_machine.state == GuardState.MITIGATING

        # MITIGATING -> MONITORING (resolved)
        state_machine.transition(GuardState.MONITORING)
        assert state_machine.state == GuardState.MONITORING

    def test_invalid_transition_raises(self, state_machine):
        """Test that invalid transitions raise InvalidTransitionError."""
        from infrastructure.parasite_guard.state_machine import (
            GuardState,
            InvalidTransitionError,
        )

        # INITIALIZING -> ALERTING is invalid
        with pytest.raises(InvalidTransitionError):
            state_machine.transition(GuardState.ALERTING)

    def test_transition_history(self, state_machine):
        """Test that transition history is recorded."""
        from infrastructure.parasite_guard.state_machine import GuardState

        state_machine.transition(GuardState.MONITORING)
        state_machine.transition(GuardState.DETECTING)

        history = state_machine._transition_history
        assert len(history) == 2
        assert history[0][1] == GuardState.MONITORING
        assert history[1][1] == GuardState.DETECTING

    def test_transition_stats(self, state_machine):
        """Test transition statistics calculation."""
        from infrastructure.parasite_guard.state_machine import GuardState

        state_machine.transition(GuardState.MONITORING)
        state_machine.transition(GuardState.DETECTING)
        state_machine.transition(GuardState.MITIGATING)
        state_machine.transition(GuardState.MONITORING)

        stats = state_machine.get_transition_stats()
        assert stats["total_transitions"] == 4
        assert stats["resolution_rate"] == 1.0  # 100% resolved


# =============================================================================
# Contract Validation Integration Tests
# =============================================================================


class TestContractValidation:
    """Integration tests for contract validation."""

    def test_detector_contract_validation(self):
        """Test detector contract validation."""
        from infrastructure.parasite_guard.contracts import validate_detector_contract

        # Create a mock detector that doesn't implement the contract
        class BadDetector:
            pass

        is_valid, errors = validate_detector_contract(BadDetector())
        assert is_valid is False
        assert len(errors) > 0

    def test_sanitizer_contract_validation(self):
        """Test sanitizer contract validation."""
        from infrastructure.parasite_guard.contracts import validate_sanitizer_contract

        # Create a mock sanitizer that doesn't implement the contract
        class BadSanitizer:
            pass

        is_valid, errors = validate_sanitizer_contract(BadSanitizer())
        assert is_valid is False
        assert len(errors) > 0

    def test_alerter_contract_validation(self):
        """Test alerter contract validation."""
        from infrastructure.parasite_guard.contracts import validate_alerter_contract

        # Create a mock alerter that doesn't implement the contract
        class BadAlerter:
            pass

        is_valid, errors = validate_alerter_contract(BadAlerter())
        assert is_valid is False
        assert len(errors) > 0

    def test_precision_metrics_calculation(self):
        """Test PrecisionMetrics calculations."""
        from infrastructure.parasite_guard.contracts import PrecisionMetrics

        metrics = PrecisionMetrics(
            true_positives=90,
            false_positives=5,
            true_negatives=100,
            false_negatives=5,
        )

        assert 0.94 <= metrics.precision <= 0.95  # 90 / 95
        assert 0.94 <= metrics.recall <= 0.95  # 90 / 95
        assert metrics.f1_score > 0.9
        assert metrics.accuracy == 0.95  # 190 / 200
