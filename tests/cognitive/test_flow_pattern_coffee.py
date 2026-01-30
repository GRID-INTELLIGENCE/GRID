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

    def test_recognize_with_coffee_mode(self, flow_pattern):
        data = {
            "cognitive_load": 2.0,
            "engagement": 0.9,
            "focus": 0.9,
            "time_distortion": 0.5
        }
        detection = flow_pattern.recognize_with_coffee_mode(data)
        assert detection.detected is True
        assert detection.features["coffee_mode"] == "Espresso"
        assert detection.features["recommended_chunk_size"] == 32
        assert "Espresso" in detection.explanation

    def test_calculate_momentum(self, flow_pattern):
        data = {
            "cognitive_load": 2.0,
            "engagement": 0.8,
            "focus": 0.8
        }
        momentum = flow_pattern.calculate_momentum(data)
        assert momentum["momentum_type"] == "high"
        assert momentum["momentum_score"] > 0.8
        assert momentum["recommended_pace"] == "fast"

        data_low = {
            "cognitive_load": 8.0,
            "engagement": 0.5,
            "focus": 0.5
        }
        momentum_low = flow_pattern.calculate_momentum(data_low)
        assert momentum_low["momentum_type"] == "low"
        assert momentum_low["momentum_score"] < 0.5
        assert momentum_low["recommended_pace"] == "deliberate"
        assert momentum_low["momentum_score"] < 0.5
        assert momentum_low["recommended_pace"] == "deliberate"
