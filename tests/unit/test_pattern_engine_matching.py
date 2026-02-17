import pytest

from grid.exceptions import DataSaveError

# Try to import legacy module, skip if not available
try:
    from grid.pattern.engine import PatternEngine

    HAS_LEGACY_SRC = True
except (ImportError, ModuleNotFoundError):
    HAS_LEGACY_SRC = False
    pytestmark = pytest.mark.skip(reason="legacy_src module not available")


class TestPatternEngineMatching:
    @pytest.fixture
    def engine(self):
        return PatternEngine()

    def test_save_pattern_matches_success(self, engine):
        matches = [{"pattern_code": "P1", "confidence": 0.9}]
        saved = engine.save_pattern_matches("entity1", matches)
        assert len(saved) == 1
        assert saved[0].entity_id == "entity1"
        assert saved[0].pattern_code == "P1"

    def test_save_pattern_matches_invalid_format_raises(self, engine):
        matches = [{"pattern_code": "P1"}]  # missing confidence
        with pytest.raises(DataSaveError, match="Missing 'confidence'"):
            engine.save_pattern_matches("entity1", matches)

    def test_save_pattern_matches_missing_code_raises(self, engine):
        matches = [{"confidence": 0.9}]  # missing pattern_code
        with pytest.raises(DataSaveError, match="Missing 'pattern_code'"):
            engine.save_pattern_matches("entity1", matches)
