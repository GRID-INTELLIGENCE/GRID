import pytest

# Try to import legacy module, skip if not available
try:
    from grid.pattern.engine import PatternEngine

    HAS_LEGACY_SRC = True
except (ImportError, ModuleNotFoundError):
    HAS_LEGACY_SRC = False
    pytestmark = pytest.mark.skip(reason="legacy_src module not available")


class TestPatternEngineMIST:
    def test_mist_detected_when_no_patterns(self):
        engine = PatternEngine()
        matches = []
        result = engine.detect_mist_pattern(matches)

        assert result is not None
        assert result["pattern_code"] == "MIST_UNKNOWABLE"
        assert result["confidence"] == 0.5

    def test_mist_returns_none_when_patterns_exist(self):
        engine = PatternEngine()
        matches = [{"pattern_code": "P1"}]
        result = engine.detect_mist_pattern(matches)

        assert result is None
