
import pytest

from cognitive.patterns.recognition import TemporalIntent, TimePattern


class TestTimePatternTemporal:
    @pytest.fixture
    def time_pattern(self):
        return TimePattern()

    def test_parse_temporal_intent_specific_year(self, time_pattern):
        intent = time_pattern.parse_temporal_intent("What year happened in 1995?")
        assert intent.era_type == "specific_year"
        assert intent.start_year == 1995
        assert intent.end_year == 1995
        assert intent.confidence >= 0.7

    def test_parse_temporal_intent_range(self, time_pattern):
        intent = time_pattern.parse_temporal_intent("Data from year 1950-1960")
        assert intent.era_type == "range"
        assert intent.start_year == 1950
        assert intent.end_year == 1960
        assert intent.confidence >= 0.8

    def test_parse_temporal_intent_decade(self, time_pattern):
        intent = time_pattern.parse_temporal_intent("The 80s era was great")
        assert intent.era_type == "range"
        assert intent.start_year == 1980
        assert intent.end_year == 1989
        assert intent.confidence >= 0.8

    def test_parse_temporal_intent_modern(self, time_pattern):
        intent = time_pattern.parse_temporal_intent("Modern trends in AI")
        assert intent.era_type == "modern"
        assert intent.confidence >= 0.7

    def test_calculate_era_relevance_specific_year(self, time_pattern):
        intent = TemporalIntent(query="1995", era_type="specific_year", start_year=1995, end_year=1995, confidence=0.9)
        metadata = {"year": 1995}
        relevance = time_pattern.calculate_era_relevance(intent, metadata)
        assert relevance == time_pattern.ERA_RELEVANCE_SCORES["specific_year"]

        metadata_wrong = {"year": 2000}
        relevance_wrong = time_pattern.calculate_era_relevance(intent, metadata_wrong)
        assert relevance_wrong < relevance

    def test_calculate_temporal_resonance(self, time_pattern):
        intent = TemporalIntent(query="2020", era_type="specific_year", start_year=2020, end_year=2020, confidence=0.9)
        metadata = {"year": 2020}
        resonance = time_pattern.calculate_temporal_resonance(intent, metadata)
        assert resonance.score > 0.9
        assert resonance.distance == 0.0

        metadata_far = {"year": 1920}
        resonance_far = time_pattern.calculate_temporal_resonance(intent, metadata_far)
        assert resonance_far.score < 0.5

    def test_filter_by_temporal_relevance(self, time_pattern):
        intent = TemporalIntent(query="2020", era_type="specific_year", start_year=2020, end_year=2020, confidence=0.9)
        docs = [
            {"id": 1, "metadata": {"year": 2020}},
            {"id": 2, "metadata": {"year": 1990}},
        ]
        filtered = time_pattern.filter_by_temporal_relevance(docs, intent, threshold=0.8)
        assert len(filtered) == 1
        assert filtered[0]["id"] == 1

    def test_detect_temporal_theme(self, time_pattern):
        result = time_pattern.detect_temporal_theme("A history of evolution over the century")
        assert result["has_temporal_theme"] is True
        assert "history" in result["keywords_found"]
        assert "evolution" in result["keywords_found"]
        assert result["has_temporal_theme"] is True
        assert "history" in result["keywords_found"]
        assert "evolution" in result["keywords_found"]
