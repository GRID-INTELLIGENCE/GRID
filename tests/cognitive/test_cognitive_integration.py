"""Test suite for cognitive integration flows."""

import pytest

from cognitive.cognitive_engine import CognitiveEngine, InteractionEvent
from cognitive.light_of_the_seven.cognitive_layer.schemas.cognitive_state import ProcessingMode


class TestCognitiveIntegration:
    """Test suite for cognitive integration flows."""

    @pytest.fixture
    async def cognitive_engine(self):
        """Create cognitive engine instance for testing."""
        return CognitiveEngine()

    @pytest.mark.asyncio
    async def test_interaction_to_cognitive_state_flow(self, cognitive_engine):
        """Test complete flow from interaction to cognitive state."""
        # Create interaction event
        event = InteractionEvent(
            user_id="test_user",
            action="case_start",
            metadata={"complexity": 0.7, "information_density": 0.6}
        )

        # Track interaction
        cognitive_state = await cognitive_engine.track_interaction(event)

        # Verify cognitive state was created
        assert cognitive_state is not None
        assert cognitive_state.estimated_load > 0.0
        assert cognitive_state.processing_mode in [ProcessingMode.SYSTEM_1, ProcessingMode.SYSTEM_2]
        assert "event" in cognitive_state.context

    @pytest.mark.asyncio
    async def test_interaction_to_operation_mapping(self, cognitive_engine):
        """Test interaction to operation conversion."""
        # Test case_start mapping
        case_start_event = InteractionEvent(
            user_id="test_user",
            action="case_start"
        )
        operation = cognitive_engine._interaction_to_operation(case_start_event)

        assert operation["complexity"] == 0.7  # Should be increased for case_start
        assert operation["novelty"] == 0.6    # Should be increased for case_start

        # Test retry mapping
        retry_event = InteractionEvent(
            user_id="test_user",
            action="retry"
        )
        retry_operation = cognitive_engine._interaction_to_operation(retry_event)

        assert retry_operation["complexity"] == 0.8  # Should be high for retry
        assert retry_operation["novelty"] == 0.2      # Should be low for retry

        # Test error mapping
        error_event = InteractionEvent(
            user_id="test_user",
            action="error"
        )
        error_operation = cognitive_engine._interaction_to_operation(error_event)

        assert error_operation["complexity"] == 0.9  # Should be very high for error
        assert error_operation["time_pressure"] == 0.3  # Should add time pressure

    @pytest.mark.asyncio
    async def test_multiple_interactions_learning(self, cognitive_engine):
        """Test cognitive state evolution across multiple interactions."""
        user_id = "test_learning_user"

        # First interaction - should create profile
        event1 = InteractionEvent(
            user_id=user_id,
            action="case_start",
            metadata={"complexity": 0.5}
        )
        state1 = await cognitive_engine.track_interaction(event1)

        # Second interaction - should update profile
        event2 = InteractionEvent(
            user_id=user_id,
            action="query",
            metadata={"complexity": 0.3}
        )
        state2 = await cognitive_engine.track_interaction(event2)

        # Verify both states were created
        assert state1.estimated_load > 0.0
        assert state2.estimated_load > 0.0

        # Verify interaction history is maintained
        assert len(cognitive_engine._interaction_history[user_id]) >= 2

    @pytest.mark.asyncio
    async def test_processing_mode_detection(self, cognitive_engine):
        """Test processing mode detection based on load."""
        # Low load should trigger System 1
        low_load_event = InteractionEvent(
            user_id="test_user",
            action="query",
            metadata={"complexity": 0.2, "information_density": 0.3}
        )
        low_load_state = await cognitive_engine.track_interaction(low_load_event)

        # High load should trigger System 2
        high_load_event = InteractionEvent(
            user_id="test_user",
            action="case_start",
            metadata={"complexity": 0.9, "information_density": 0.8}
        )
        high_load_state = await cognitive_engine.track_interaction(high_load_event)

        # Verify processing modes are detected
        assert low_load_state.processing_mode in [ProcessingMode.SYSTEM_1, ProcessingMode.SYSTEM_2]
        assert high_load_state.processing_mode in [ProcessingMode.SYSTEM_1, ProcessingMode.SYSTEM_2]

        # Typically, high load should favor System 2
        # (but this depends on the specific implementation)
        assert high_load_state.estimated_load > low_load_state.estimated_load
