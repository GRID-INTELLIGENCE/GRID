"""
NVIDIA Safety Engine Tests
Tests for NeMo Guardrails, Trustworthy AI, and Secure Infrastructure
"""
import unittest
import json
from pathlib import Path
from typing import Dict, Any


class TestNvidiaSafetyEngine(unittest.TestCase):
    """Test NVIDIA's safety frameworks."""

    def setUp(self):
        """Load NVIDIA safety configuration."""
        self.config_dir = Path(__file__).parent.parent.parent / "PROVIDERS" / "NVIDIA"
        self.schema = self._load_json("NVIDIA_AI_SAFETY_SCHEMA.json")
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
        """Test that NVIDIA schema has required fields."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        self.assertIn("provider", self.schema)
        self.assertIn("safety_frameworks", self.schema)
        self.assertIn("hard_constraints", self.schema)
        self.assertEqual(self.schema["provider"], "NVIDIA")

    def test_nemo_guardrails(self):
        """Test NeMo Guardrails framework is defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        frameworks = self.schema.get("safety_frameworks", {})
        self.assertIn("nemo_guardrails", frameworks)

    def test_trustworthy_ai(self):
        """Test Trustworthy AI initiative is defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        frameworks = self.schema.get("safety_frameworks", {})
        self.assertIn("trustworthy_ai", frameworks)

    def test_confidential_computing(self):
        """Test confidential computing is defined in research areas."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        research_areas = self.schema.get("research_areas", [])
        confidential = [r for r in research_areas if "confidential" in r.get("name", "").lower()]
        self.assertGreater(len(confidential), 0)

    def test_hard_constraints(self):
        """Test that hard constraints are properly defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        constraints = self.schema.get("hard_constraints", {})
        self.assertIn("prohibited_applications", constraints)
        self.assertGreater(len(constraints["prohibited_applications"]), 0)

    def test_actions_matrix_structure(self):
        """Test actions matrix has proper structure."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        self.assertIn("trigger_definitions", self.actions_matrix)
        self.assertIn("action_catalog", self.actions_matrix)
        self.assertIn("mapping", self.actions_matrix)

    def test_thresholds_defined(self):
        """Test that thresholds are defined for key signals."""
        if not self.has_thresholds:
            self.skipTest("Thresholds file not found")
        self.assertIn("signal_thresholds", self.thresholds)
        self.assertIn("escalation_triggers", self.thresholds)

    def test_guardrails_triggers(self):
        """Test guardrails triggers are defined."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        triggers = self.actions_matrix.get("trigger_definitions", [])
        guardrails_triggers = [t for t in triggers if "guardrails" in t.get("name", "").lower()]
        self.assertGreater(len(guardrails_triggers), 0)

    def test_action_catalog_completeness(self):
        """Test that action catalog has expected action types."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        catalog = self.actions_matrix.get("action_catalog", {})
        expected_actions = ["BLOCK_CONTENT", "ESCALATE"]
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


if __name__ == "__main__":
    unittest.main()
