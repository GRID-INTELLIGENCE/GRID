"""
Google Safety Engine Tests
Tests for AI Principles, Frontier Safety Framework, and Hard Constraints
"""
import unittest
import json
from pathlib import Path
from typing import Dict, Any


class TestGoogleSafetyEngine(unittest.TestCase):
    """Test Google DeepMind's AI Principles and Frontier Safety Framework implementation."""

    def setUp(self):
        """Load Google safety configuration."""
        self.config_dir = Path(__file__).parent.parent.parent / "PROVIDERS" / "GOOGLE"
        self.schema = self._load_json("GOOGLE_AI_SAFETY_SCHEMA.json")
        self.actions_matrix = self._load_json("ACTIONS_MATRIX.json")
        self.thresholds = self._load_json("THRESHOLDS.json")
        self._setup_test_methods()

    def _setup_test_methods(self):
        """Set up test methods based on available configuration."""
        self.has_schema = bool(self.schema)
        self.has_actions = bool(self.actions_matrix)
        self.has_thresholds = bool(self.thresholds)

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Helper to load JSON configuration files."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def test_schema_structure(self):
        """Test that Google schema has required fields."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        self.assertIn("provider", self.schema)
        self.assertIn("safety_frameworks", self.schema)
        self.assertIn("hard_constraints", self.schema)
        provider = self.schema["provider"]
        provider_name = provider.get("name") if isinstance(provider, dict) else provider
        self.assertEqual(provider_name, "Google DeepMind")

    def test_ai_principles_framework(self):
        """Test AI Principles framework is defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        frameworks = self.schema.get("safety_frameworks", {})
        self.assertIn("ai_principles", frameworks)
        principles = frameworks["ai_principles"]
        self.assertGreater(len(principles), 0)

    def test_frontier_safety_framework(self):
        """Test Frontier Safety Framework is defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        frameworks = self.schema.get("safety_frameworks", {})
        self.assertIn("frontier_safety_framework", frameworks)
        frontier = frameworks["frontier_safety_framework"]
        self.assertIn("levels", frontier)
        self.assertIn("risk_domains", frontier)

    def test_frontier_safety_levels(self):
        """Test Frontier Safety levels are defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        frameworks = self.schema.get("safety_frameworks", {})
        frontier = frameworks.get("frontier_safety_framework", {})
        levels = frontier.get("levels", [])
        expected_levels = ["Standard Safety Precautions", "Enhanced Security & Monitoring", 
                          "Critical Risk Mitigation", "Threshold Breach Protocol"]
        for level in expected_levels:
            self.assertIn(level, levels)

    def test_frontier_risk_domains(self):
        """Test Frontier Safety risk domains are defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        frameworks = self.schema.get("safety_frameworks", {})
        frontier = frameworks.get("frontier_safety_framework", {})
        risk_domains = frontier.get("risk_domains", [])
        expected_domains = ["CBRN (Chemical, Biological, Radiological, Nuclear)", 
                           "Cybersecurity", "Autonomous Agency", "Persuasion & Manipulation"]
        for domain in expected_domains:
            self.assertIn(domain, risk_domains)

    def test_hard_constraints(self):
        """Test that hard constraints are properly defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        constraints = self.schema.get("hard_constraints", {})
        self.assertIn("prohibited_applications", constraints)
        prohibited = constraints["prohibited_applications"]
        self.assertGreater(len(prohibited), 0)

    def test_research_areas_defined(self):
        """Test that research areas are defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        self.assertIn("research_areas", self.schema)
        research_areas = self.schema["research_areas"]
        self.assertGreater(len(research_areas), 0)
        expected_areas = ["Technical Safety", "Ethics & Society", "Governance & Security", "Interpretability"]
        area_names = [area["name"] for area in research_areas]
        for area in expected_areas:
            self.assertIn(area, area_names)

    def test_monitoring_parameters(self):
        """Test that monitoring parameters are defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        self.assertIn("monitoring_parameters", self.schema)
        monitoring = self.schema["monitoring_parameters"]
        self.assertIn("gemini_safety_filters", monitoring)
        self.assertIn("evaluations", monitoring)

    def test_gemini_safety_filters(self):
        """Test Gemini safety filters are defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        monitoring = self.schema.get("monitoring_parameters", {})
        filters = monitoring.get("gemini_safety_filters", [])
        expected_filters = ["Hate Speech", "Harassment", "Sexually Explicit", "Dangerous Content"]
        for filter_name in expected_filters:
            self.assertIn(filter_name, filters)

    def test_privacy_protocols(self):
        """Test privacy protocols are defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        self.assertIn("privacy_protocols", self.schema)
        privacy = self.schema["privacy_protocols"]
        self.assertIn("approaches", privacy)
        approaches = privacy["approaches"]
        expected_approaches = ["Data Minimization", "Differential Privacy", "Federated Learning"]
        for approach in expected_approaches:
            self.assertIn(approach, approaches)

    def test_governance_bodies(self):
        """Test governance oversight bodies are defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        metadata = self.schema.get("metadata", {})
        self.assertIn("governance", metadata)
        governance = metadata["governance"]
        self.assertIn("oversight_bodies", governance)
        oversight_bodies = governance["oversight_bodies"]
        self.assertGreater(len(oversight_bodies), 0)

    def test_actions_matrix_structure(self):
        """Test actions matrix has proper structure."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        self.assertTrue(
            "trigger_definitions" in self.actions_matrix,
            "Actions matrix should have trigger_definitions"
        )
        # Google uses singular 'action_catalog', others use plural
        self.assertTrue(
            "action_catalog" in self.actions_matrix or "actions_catalog" in self.actions_matrix,
            "Actions matrix should have action_catalog or actions_catalog"
        )

    def test_action_catalog_completeness(self):
        """Test that action catalog has expected action types."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        # Google uses singular 'action_catalog', others use plural
        catalog = self.actions_matrix.get("action_catalog") or self.actions_matrix.get("actions_catalog", {})
        expected_actions = ["BLOCK_CONTENT", "ESCALATE_RSC", "USER_THROTTLE", "MODEL_PAUSE"]
        for action_type in expected_actions:
            actions = [a for a in catalog.values() if action_type in a.get("type", "")]
            self.assertGreater(len(actions), 0, f"Expected action {action_type} not found")

    def test_trigger_action_mapping(self):
        """Test that triggers map to actions correctly."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        mappings = self.actions_matrix.get("mapping", [])
        self.assertGreater(len(mappings), 0)
        for mapping in mappings:
            self.assertIn("trigger_id", mapping)
            self.assertIn("actions", mapping)
            self.assertGreater(len(mapping["actions"]), 0)

    def test_gemini_filter_triggers(self):
        """Test Gemini safety filter triggers exist."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        triggers = self.actions_matrix.get("trigger_definitions", [])
        # Look for triggers related to Gemini safety filters
        gemini_triggers = [t for t in triggers if "gemini_safety_filters" in t.get("condition", "")]
        self.assertGreater(len(gemini_triggers), 0, "No Gemini filter triggers found")

    def test_frontier_redline_triggers(self):
        """Test Frontier Safety redline triggers exist."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        triggers = self.actions_matrix.get("trigger_definitions", [])
        # Look for triggers related to frontier safety
        frontier_triggers = [t for t in triggers if "frontier_safety" in t.get("condition", "")]
        self.assertGreater(len(frontier_triggers), 0, "No Frontier redline triggers found")

    def test_thresholds_defined(self):
        """Test that thresholds are defined for key signals."""
        if not self.has_thresholds:
            self.skipTest("Thresholds file not found")
        self.assertIn("signal_thresholds", self.thresholds)
        self.assertIn("escalation_triggers", self.thresholds)

    def test_threshold_signal_coverage(self):
        """Test that key safety signals have thresholds."""
        if not self.has_thresholds:
            self.skipTest("Thresholds file not found")
        signals = self.thresholds.get("signal_thresholds", {})
        # Google uses nested categories for signals
        expected_nested_signals = {
            "gemini_safety_filters": ["hate_speech", "harassment"],
            "frontier_safety": ["cbrn_uplift_score"],
            "privacy_and_security": ["pii_leakage_probability"]
        }
        for category, signal_names in expected_nested_signals.items():
            self.assertIn(category, signals, f"Category {category} not found")
            category_signals = signals[category]
            for signal in signal_names:
                self.assertIn(signal, category_signals, f"Signal {signal} not found in {category}")

    def test_escalation_triggers_defined(self):
        """Test that escalation triggers are defined."""
        if not self.has_thresholds:
            self.skipTest("Thresholds file not found")
        escalations = self.thresholds.get("escalation_triggers", {})
        self.assertGreater(len(escalations), 0)


if __name__ == "__main__":
    unittest.main()
