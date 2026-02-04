import pytest

from cognitive.patterns.recognition import FlowPattern


class TestFlowPatternCoffee:
    @pytest.fixture
    def flow_pattern(self):
        return FlowPattern()

    def test_detect_coffee_mode_espresso(self, flow_pattern):
        mode = flow_pattern.detect_coffee_mode(2.0)
        assert mode.name == "Espresso"
        assert mode.chunk_size == 32
        assert mode.momentum == "high"

    def test_detect_coffee_mode_americano(self, flow_pattern):
        mode = flow_pattern.detect_coffee_mode(5.0)
        assert mode.name == "Americano"
        assert mode.chunk_size == 64
        assert mode.momentum == "balanced"

    def test_detect_coffee_mode_cold_brew(self, flow_pattern):
        mode = flow_pattern.detect_coffee_mode(8.0)
        assert mode.name == "Cold Brew"
        assert mode.chunk_size == 128
        assert mode.momentum == "low"

    @pytest.mark.asyncio
    async def test_recognize_with_coffee_mode(self, flow_pattern):
        data = {"cognitive_load": 2.0, "engagement": 0.9, "focus": 0.9, "time_distortion": 0.5}
        detection = await flow_pattern.recognize(data)
        assert detection.detected is True
        # Verify coffee mode detection works via calculate_momentum
        coffee_mode = flow_pattern.detect_coffee_mode(2.0)
        assert coffee_mode.name == "Espresso"

    def test_calculate_momentum(self, flow_pattern):
        data = {"cognitive_load": 2.0, "engagement": 0.8, "focus": 0.8}
        momentum = flow_pattern.calculate_momentum(data)
        assert momentum["momentum_type"] == "high"
        assert momentum["momentum_score"] > 0.8
        assert momentum["recommended_pace"] == "fast"

        data_low = {"cognitive_load": 8.0, "engagement": 0.5, "focus": 0.5}
        momentum_low = flow_pattern.calculate_momentum(data_low)
        assert momentum_low["momentum_type"] == "low"
        assert momentum_low["momentum_score"] < 0.5
        assert momentum_low["recommended_pace"] == "deliberate"
        assert momentum_low["momentum_score"] < 0.5
        assert momentum_low["recommended_pace"] == "deliberate"

    def test_detect_coffee_mode_boundary_espresso_americano(self, flow_pattern):
        """Test boundary between Espresso and Americano at 3.0 cognitive load."""
        mode = flow_pattern.detect_coffee_mode(3.0)
        assert mode.name == "Americano"
        assert mode.chunk_size == 64

    def test_detect_coffee_mode_boundary_americano_cold_brew(self, flow_pattern):
        """Test boundary between Americano and Cold Brew at 7.0 cognitive load."""
        mode = flow_pattern.detect_coffee_mode(7.0)
        assert mode.name == "Cold Brew"
        assert mode.chunk_size == 128

    def test_detect_coffee_mode_low_load_edge_case(self, flow_pattern):
        """Test with very low cognitive load."""
        mode = flow_pattern.detect_coffee_mode(0.1)
        assert mode.name == "Espresso"
        assert mode.processing_mode == "system_1"

    def test_detect_coffee_mode_high_load_edge_case(self, flow_pattern):
        """Test with very high cognitive load."""
        mode = flow_pattern.detect_coffee_mode(9.9)
        assert mode.name == "Cold Brew"
        assert mode.processing_mode == "system_2"

    def test_calculate_momentum_americano_mode(self, flow_pattern):
        """Test momentum calculation in Americano mode."""
        data = {"cognitive_load": 5.0, "engagement": 0.6, "focus": 0.7}
        momentum = flow_pattern.calculate_momentum(data)
        assert momentum["momentum_type"] == "balanced"
        assert momentum["coffee_mode"] == "Americano"
        assert momentum["recommended_pace"] == "steady"

    def test_calculate_momentum_cold_brew_high_engagement(self, flow_pattern):
        """Test momentum in Cold Brew mode with high engagement."""
        data = {"cognitive_load": 8.5, "engagement": 0.9, "focus": 0.8}
        momentum = flow_pattern.calculate_momentum(data)
        assert momentum["momentum_type"] == "low"
        assert momentum["coffee_mode"] == "Cold Brew"
        # Even in cold brew with high engagement, should be deliberate
        assert momentum["recommended_pace"] in ["steady", "deliberate"]

    @pytest.mark.asyncio
    async def test_recognize_with_coffee_mode_americano(self, flow_pattern):
        """Test flow recognition in Americano mode."""
        data = {
            "cognitive_load": 5.0,
            "engagement": 0.7,
            "focus": 0.6,
            "time_distortion": 0.4,
        }
        detection = await flow_pattern.recognize_with_coffee_mode(data)
        assert detection.features["coffee_mode"] == "Americano"
        assert detection.features["recommended_chunk_size"] == 64
        assert "Americano" in detection.explanation

    @pytest.mark.asyncio
    async def test_recognize_with_coffee_mode_cold_brew(self, flow_pattern):
        """Test flow recognition in Cold Brew mode."""
        data = {
            "cognitive_load": 8.0,
            "engagement": 0.5,
            "focus": 0.4,
            "time_distortion": 0.2,
        }
        detection = await flow_pattern.recognize_with_coffee_mode(data)
        assert detection.features["coffee_mode"] == "Cold Brew"
        assert detection.features["recommended_chunk_size"] == 128
        assert "Cold Brew" in detection.explanation
