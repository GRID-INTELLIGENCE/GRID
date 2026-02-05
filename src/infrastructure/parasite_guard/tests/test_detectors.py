"""
Tests for Parasite Guard detectors.

Focus on C1 (WebSocket No-Ack Detector) for Phase 1 validation.
"""

from __future__ import annotations

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.parasite_guard.config import ParasiteGuardConfig, GuardMode
from infrastructure.parasite_guard.models import (
    ParasiteContext,
    DetectionResult,
    ParasiteSeverity,
)
from infrastructure.parasite_guard.detectors import (
    Detector,
    WebSocketNoAckDetector,
    EventSubscriptionLeakDetector,
    DBConnectionOrphanDetector,
    DetectorChain,
)


@pytest.fixture
def config():
    """Create test configuration."""
    return ParasiteGuardConfig()


@pytest.fixture
def websocket_detector(config):
    """Create WebSocket detector instance."""
    return WebSocketNoAckDetector(config)


@pytest.fixture
def eventbus_detector(config):
    """Create Event Bus detector instance."""
    detector = EventSubscriptionLeakDetector(config)
    return detector


@pytest.fixture
def db_detector(config):
    """Create DB detector instance."""
    return DBConnectionOrphanDetector(config)


# =============================================================================
# WebSocket No-Ack Detector Tests (C1)
# =============================================================================


class TestWebSocketNoAckDetector:
    """Tests for WebSocket No-Ack Detection."""

    @pytest.mark.asyncio
    async def test_no_detection_without_message(self, websocket_detector):
        """Test that no detection occurs when no message is pending."""
        # Create mock request
        request = MagicMock()
        request.state = MagicMock()
        request.state.websocket = MagicMock()
        request.state.last_send_id = None

        # Run detector
        result = await websocket_detector(request)

        # Assert no detection
        assert not result.detected
        assert result.context is None

    @pytest.mark.asyncio
    async def test_detection_on_ack_timeout(self, websocket_detector):
        """Test detection when ACK timeout exceeds threshold."""
        # Create mock request with pending message
        request = MagicMock()
        request.state = MagicMock()
        request.state.websocket = MagicMock()

        # Message sent 5 seconds ago (timeout is 3s)
        send_time = datetime.now(timezone.utc)
        send_time_minus_5 = datetime.fromtimestamp(send_time.timestamp() - 5, tz=timezone.utc)

        result = await websocket_detector(
            request,
            last_send_id="msg_123",
            last_ack_id=None,
            send_time=send_time_minus_5,
            connection_id="conn_456",
        )

        # Assert detection
        assert result.detected
        assert result.context is not None
        assert result.context.component == "websocket"
        assert result.context.pattern == "no_ack"
        assert result.context.severity == ParasiteSeverity.CRITICAL
        assert "msg_123" in result.reason
        assert result.confidence >= 0.9

    @pytest.mark.asyncio
    async def test_no_detection_within_timeout(self, websocket_detector):
        """Test no detection when ACK is within timeout."""
        # Create mock request with recent message
        request = MagicMock()
        request.state = MagicMock()
        request.state.websocket = MagicMock()

        # Message sent 1 second ago (timeout is 3s)
        send_time = datetime.now(timezone.utc)
        send_time_minus_1 = datetime.fromtimestamp(send_time.timestamp() - 1, tz=timezone.utc)

        result = await websocket_detector(
            request,
            last_send_id="msg_123",
            last_ack_id=None,
            send_time=send_time_minus_1,
            connection_id="conn_456",
        )

        # Assert no detection (within timeout)
        assert not result.detected

    @pytest.mark.asyncio
    async def test_detection_with_ack_received(self, websocket_detector):
        """Test no detection when ACK is received."""
        # Create mock request with ACK
        request = MagicMock()
        request.state = MagicMock()
        request.state.websocket = MagicMock()

        send_time = datetime.now(timezone.utc)

        result = await websocket_detector(
            request,
            last_send_id="msg_123",
            last_ack_id="msg_123",  # ACK received
            send_time=send_time,
            connection_id="conn_456",
        )

        # Assert no detection (ACK received)
        assert not result.detected


# =============================================================================
# Event Bus Subscription Leak Detector Tests (C2)
# =============================================================================


class TestEventSubscriptionLeakDetector:
    """Tests for Event Bus Subscription Leak Detection."""

    @pytest.mark.asyncio
    async def test_no_detection_below_threshold(self, eventbus_detector):
        """Test no detection when subscription count is below threshold."""
        # Create mock request
        request = MagicMock()

        # Set up event bus with low subscription count
        mock_event_bus = MagicMock()
        mock_event_bus._subscribers = {
            "event1": [MagicMock(), MagicMock()],  # 2 subscriptions
            "event2": [MagicMock()],  # 1 subscription
        }
        eventbus_detector.set_event_bus(mock_event_bus)

        result = await eventbus_detector(request)

        # Assert no detection
        assert not result.detected

    @pytest.mark.asyncio
    async def test_detection_above_threshold(self, eventbus_detector):
        """Test detection when subscription count exceeds threshold."""
        # Create mock request
        request = MagicMock()

        # Create many subscriptions (threshold is 1000)
        subscriptions = [MagicMock() for _ in range(1500)]
        mock_event_bus = MagicMock()
        mock_event_bus._subscribers = {
            "event1": subscriptions[:1000],
            "event2": subscriptions[1000:1500],
        }
        eventbus_detector.set_event_bus(mock_event_bus)

        result = await eventbus_detector(request)

        # Assert detection
        assert result.detected
        assert result.context is not None
        assert result.context.component == "eventbus"
        assert result.context.pattern == "subscription_leak"
        assert result.context.severity == ParasiteSeverity.CRITICAL
        assert "1500" in result.reason  # Total count
        assert "1000" in result.reason  # Threshold


# =============================================================================
# DB Connection Orphan Detector Tests (C3)
# =============================================================================


class TestDBConnectionOrphanDetector:
    """Tests for DB Connection Orphan Detection."""

    @pytest.mark.asyncio
    async def test_no_detection_below_threshold(self, db_detector):
        """Test no detection when pool size is below threshold."""
        # Create mock request
        request = MagicMock()

        # Set up DB engine with normal pool size
        mock_pool = MagicMock()
        mock_pool.size = MagicMock(return_value=10)  # Below threshold of 30

        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        db_detector.set_db_engine(mock_engine)

        result = await db_detector(request)

        # Assert no detection
        assert not result.detected

    @pytest.mark.asyncio
    async def test_detection_above_threshold(self, db_detector):
        """Test detection when pool size exceeds threshold."""
        # Create mock request
        request = MagicMock()

        # Set up DB engine with large pool size
        mock_pool = MagicMock()
        mock_pool.size = MagicMock(return_value=50)  # Above threshold of 30

        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        db_detector.set_db_engine(mock_engine)

        result = await db_detector(request)

        # Assert detection
        assert result.detected
        assert result.context is not None
        assert result.context.component == "db"
        assert result.context.pattern == "connection_orphan"
        assert result.context.severity == ParasiteSeverity.CRITICAL
        assert "50" in result.reason  # Pool size
        assert "30" in result.reason  # Threshold


# =============================================================================
# Detector Chain Tests
# =============================================================================


class TestDetectorChain:
    """Tests for detector chain functionality."""

    @pytest.mark.asyncio
    async def test_chain_returns_first_detection(self, config):
        """Test that chain returns first detection."""
        # Create detectors
        detector1 = MagicMock(spec=Detector)
        detector1.name = "detector1"
        detector1.component = "comp1"
        detector1.__call__ = AsyncMock(return_value=DetectionResult(detected=False))

        detector2 = MagicMock(spec=Detector)
        detector2.name = "detector2"
        detector2.component = "comp2"
        detector2.__call__ = AsyncMock(return_value=DetectionResult(detected=False))

        detector3 = MagicMock(spec=Detector)
        detector3.name = "detector3"
        detector3.component = "comp3"
        detector3.__call__ = AsyncMock(
            return_value=DetectionResult(
                detected=True,
                context=ParasiteContext(
                    id="test-id",
                    component="comp3",
                    pattern="test_pattern",
                    rule="detector3",
                    severity=ParasiteSeverity.HIGH,
                ),
            )
        )

        # Create chain
        chain = DetectorChain([detector1, detector2, detector3], config)

        # Create mock request
        request = MagicMock()

        # Run detection
        result = await chain.detect(request)

        # Assert third detector fired
        assert result.detected
        assert result.context.component == "comp3"
        assert result.context.pattern == "test_pattern"

        # Verify detector1 and detector2 were called
        detector1.__call__.assert_called_once()
        detector2.__call__.assert_called_once()

        # Verify detector3 was called and returned first detection
        detector3.__call__.assert_called_once()

    @pytest.mark.asyncio
    async def test_chain_skips_disabled_components(self, config):
        """Test that chain skips disabled components."""
        # Create detector for disabled component
        detector = MagicMock(spec=Detector)
        detector.name = "test_detector"
        detector.component = "websocket"  # This component will be disabled
        detector.__call__ = AsyncMock(
            return_value=DetectionResult(
                detected=True,
                context=ParasiteContext(
                    id="test-id",
                    component="websocket",
                    pattern="test_pattern",
                    rule="test_detector",
                    severity=ParasiteSeverity.HIGH,
                ),
            )
        )

        # Create chain with websocket disabled
        config.enable_component("websocket", GuardMode.DISABLED)
        chain = DetectorChain([detector], config)

        # Create mock request
        request = MagicMock()

        # Run detection
        result = await chain.detect(request)

        # Assert no detection (component disabled)
        assert result is None

        # Verify detector was NOT called
        detector.__call__.assert_not_called()

    @pytest.mark.asyncio
    async def test_chain_handles_detector_exceptions(self, config):
        """Test that chain continues after detector exception."""
        # Create detector that raises exception
        failing_detector = MagicMock(spec=Detector)
        failing_detector.name = "failing_detector"
        failing_detector.component = "comp1"
        failing_detector.__call__ = AsyncMock(side_effect=Exception("Detector failed"))

        # Create working detector
        working_detector = MagicMock(spec=Detector)
        working_detector.name = "working_detector"
        working_detector.component = "comp2"
        working_detector.__call__ = AsyncMock(return_value=DetectionResult(detected=False))

        # Create chain
        chain = DetectorChain([failing_detector, working_detector], config)

        # Create mock request
        request = MagicMock()

        # Run detection
        result = await chain.detect(request)

        # Assert no detection (working detector ran)
        assert result is None or not result.detected

        # Verify both detectors were called
        failing_detector.__call__.assert_called_once()
        working_detector.__call__.assert_called_once()


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
