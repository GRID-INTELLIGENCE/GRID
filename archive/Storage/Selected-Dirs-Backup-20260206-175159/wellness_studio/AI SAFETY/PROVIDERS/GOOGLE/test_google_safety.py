import unittest
from pathlib import Path

from google_safety_engine import GoogleSafetyEngine


class TestGoogleSafetyEngine(unittest.TestCase):
    def setUp(self):
        # Initialize engine with the current directory containing the JSON configs
        self.engine = GoogleSafetyEngine(config_dir=Path(__file__).parent)

    def test_safe_content(self):
        """Test content that should pass all safety checks."""
        test_scores = {
            "hate_speech": 0.1,
            "harassment": 0.05,
            "sexually_explicit": 0.02,
            "dangerous_content": 0.1,
            "cbrn_uplift_score": 0.01,
            "pii_leakage_probability": 0.0001,
        }
        result = self.engine.validate_content("How do I stay healthy?", test_scores)
        self.assertTrue(result["is_safe"])
        self.assertEqual(len(result["violations"]), 0)
        self.assertEqual(len(result["recommended_actions"]), 0)

    def test_gemini_filter_breach(self):
        """Test high-confidence breach of Gemini safety filters."""
        test_scores = {
            "hate_speech": 0.95,  # Trigger for TRG-GOOG-001 (> 0.9)
            "harassment": 0.1,
        }
        result = self.engine.validate_content("Some harmful content", test_scores)
        self.assertFalse(result["is_safe"])

        # Check violations
        violation_categories = [v["category"] for v in result["violations"]]
        self.assertIn("GEMINI_HATE_SPEECH", violation_categories)

        # Check actions (TRG-GOOG-001 -> ACT-GOOG-001, ACT-GOOG-003)
        action_types = [a["type"] for a in result["recommended_actions"]]
        self.assertIn("BLOCK_CONTENT", action_types)
        self.assertIn("USER_THROTTLE", action_types)

    def test_frontier_redline_breach(self):
        """Test breach of Frontier Safety Redlines."""
        test_scores = {
            "cbrn_uplift_score": 0.6,  # Trigger for TRG-GOOG-002 (> 0.5)
        }
        result = self.engine.validate_content("CBRN related query", test_scores)
        self.assertFalse(result["is_safe"])

        violation_categories = [v["category"] for v in result["violations"]]
        self.assertIn("FRONTIER_CBRN_UPLIFT_SCORE", violation_categories)

        # Check actions (TRG-GOOG-002 -> ACT-GOOG-001, ACT-GOOG-002, ACT-GOOG-004)
        action_types = [a["type"] for a in result["recommended_actions"]]
        self.assertIn("BLOCK_CONTENT", action_types)
        self.assertIn("ESCALATE_RSC", action_types)
        self.assertIn("MODEL_PAUSE", action_types)

    def test_privacy_violation(self):
        """Test detection of PII leakage."""
        test_scores = {
            "pii_leakage_probability": 0.05,  # Trigger for TRG-GOOG-003 (> 0.01)
        }
        result = self.engine.validate_content("Contains PII", test_scores)
        self.assertFalse(result["is_safe"])

        violation_categories = [v["category"] for v in result["violations"]]
        self.assertIn("PRIVACY_PII_LEAKAGE_PROBABILITY", violation_categories)

        # Check actions (TRG-GOOG-003 -> ACT-GOOG-001, ACT-GOOG-002)
        action_types = [a["type"] for a in result["recommended_actions"]]
        self.assertIn("BLOCK_CONTENT", action_types)
        self.assertIn("ESCALATE_RSC", action_types)

    def test_summary_generation(self):
        """Test the human-readable summary output."""
        test_scores = {"harassment": 0.85}
        result = self.engine.validate_content("Test", test_scores)
        summary = self.engine.generate_safety_summary(result)

        self.assertIn("Safety Check Failed", summary)
        self.assertIn("GEMINI_HARASSMENT", summary)
        self.assertIn("Mitigation Actions Applied", summary)


if __name__ == "__main__":
    unittest.main()
