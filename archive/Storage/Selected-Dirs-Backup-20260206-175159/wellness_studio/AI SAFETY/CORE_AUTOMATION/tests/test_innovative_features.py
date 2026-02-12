"""
Lightweight tests for innovative features modules.
"""
import os
import sys
import unittest

MODULES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modules"))
sys.path.insert(0, MODULES_DIR)

from gap_detection import SafetyGapDetector  # type: ignore
from trend_analytics import SafetyTrendAnalyzer  # type: ignore
from protocol_generator import SafetyProtocolGenerator  # type: ignore


class TestSafetyGapDetector(unittest.TestCase):
    """Basic tests for gap detection"""

    def test_detect_new_gaps_tracks_state(self):
        detector = SafetyGapDetector()
        current_results = {
            "providers": {
                "OpenAI": [
                    {
                        "fetch": {"url": "https://example.com/a"},
                        "safety_analysis": {"gaps": ["gap-1", "gap-2"]}
                    }
                ]
            }
        }

        first_run = detector.detect_new_gaps(current_results)
        self.assertEqual(len(first_run), 2)

        second_run = detector.detect_new_gaps(current_results)
        self.assertEqual(len(second_run), 0)


class TestSafetyTrendAnalyzer(unittest.TestCase):
    """Basic tests for trend analysis"""

    def test_analyze_trends_requires_history(self):
        analyzer = SafetyTrendAnalyzer()
        analyzer.record_snapshot({"summary": {"average_safety_score": 75}, "providers": {}})

        trends = analyzer.analyze_trends(window_size=2)
        self.assertIn("error", trends)


class TestSafetyProtocolGenerator(unittest.TestCase):
    """Basic tests for protocol generation"""

    def test_generate_protocol_sets_severity(self):
        generator = SafetyProtocolGenerator()
        gaps = ["gap-a", "gap-b", "gap-c", "gap-d", "gap-e"]

        protocol = generator.generate_protocol("OpenAI", gaps, safety_score=70)
        self.assertEqual(protocol["gap_count"], 5)
        self.assertEqual(protocol["severity"], "high")
        self.assertGreater(len(protocol["recommendations"]), 0)


class TestMonitoringPipelineIntegration(unittest.TestCase):
    """Integration tests for full monitoring pipeline"""

    def test_full_pipeline_with_mock_data(self):
        """Test complete pipeline: gap detection -> trend analysis -> protocol generation"""
        gap_detector = SafetyGapDetector()
        trend_analyzer = SafetyTrendAnalyzer()
        protocol_generator = SafetyProtocolGenerator()

        mock_results = {
            "providers": {
                "OpenAI": [
                    {"fetch": {"url": "https://openai.com/safety/"}, "safety_analysis": {"gaps": ["gap-1", "gap-2"], "safety_score": 84}},
                    {"fetch": {"url": "https://openai.com/safety/evaluations/"}, "safety_analysis": {"gaps": ["gap-3"], "safety_score": 92}}
                ],
                "Anthropic": [
                    {"fetch": {"url": "https://anthropic.com/safety/"}, "safety_analysis": {"gaps": ["gap-1", "gap-2", "gap-3"], "safety_score": 76}}
                ]
            },
            "summary": {
                "total_providers": 2,
                "total_sources": 3,
                "successful_fetches": 3,
                "failed_fetches": 0,
                "total_gaps": 5,
                "average_safety_score": 84.0,
                "methods_used": ["http_fetch"]
            }
        }

        new_gaps = gap_detector.detect_new_gaps(mock_results)
        self.assertEqual(len(new_gaps), 6)

        trend_analyzer.record_snapshot(mock_results)
        trends = trend_analyzer.analyze_trends(window_size=1)
        self.assertNotIn("error", trends)

        provider_gaps = ["gap-1", "gap-2", "gap-3", "gap-4", "gap-5"]
        protocol = protocol_generator.generate_protocol("OpenAI", provider_gaps, safety_score=68)
        self.assertEqual(protocol["provider"], "OpenAI")
        self.assertEqual(protocol["gap_count"], 5)
        self.assertEqual(protocol["severity"], "high")

    def test_provider_specific_score_calculation(self):
        """Test that provider-specific scores are computed correctly"""
        protocol_generator = SafetyProtocolGenerator()

        gaps = ["gap-a", "gap-b", "gap-c"]
        provider_avg = 72

        protocol = protocol_generator.generate_protocol("Google", gaps, safety_score=provider_avg)
        self.assertEqual(protocol["safety_score"], provider_avg)
        self.assertEqual(protocol["severity"], "medium")


if __name__ == "__main__":
    unittest.main()
