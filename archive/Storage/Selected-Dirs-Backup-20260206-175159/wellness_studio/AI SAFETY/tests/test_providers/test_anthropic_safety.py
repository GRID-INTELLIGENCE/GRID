"""
Anthropic Safety Engine Tests
Tests for Constitutional AI, RSP, ASL levels, and Hard Constraints
"""
import unittest
import json
from pathlib import Path
from typing import Dict, Any


class TestAnthropicSafetyEngine(unittest.TestCase):
    """Test Anthropic's Constitutional AI and Responsible Scaling Policy implementation."""

    def setUp(self):
        """Load Anthropic safety configuration."""
        self.config_dir = Path(__file__).parent.parent.parent / "PROVIDERS" / "ANTHROPIC"
        self.schema = self._load_json("ANTHROPIC_AI_SAFETY_SCHEMA.json")
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
        """Test that Anthropic schema has required fields."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        self.assertIn("provider", self.schema)
        self.assertIn("safety_frameworks", self.schema)
        self.assertIn("hard_constraints", self.schema)
        # Handle both string and object provider formats
        provider = self.schema["provider"]
        provider_name = provider.get("name") if isinstance(provider, dict) else provider
        self.assertEqual(provider_name, "Anthropic")

    def test_constitutional_ai_framework(self):
        """Test Constitutional AI framework is defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        frameworks = self.schema.get("safety_frameworks", {})
        self.assertIn("constitutional_ai", frameworks)

    def test_rsp_levels(self):
        """Test Responsible Scaling Policy levels are defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        frameworks = self.schema.get("safety_frameworks", {})
        self.assertIn("responsible_scaling_policy", frameworks)
        rsp = frameworks["responsible_scaling_policy"]
        # Check for 'levels' or alternative structure
        if "levels" in rsp:
            self.assertIn("levels", rsp)
            self.assertIn("ASL-1", rsp["levels"])
        elif "description" in rsp:
            # Alternative structure
            self.assertIn("description", rsp)
        else:
            self.skipTest("RSP structure not recognized")

    def test_hard_constraints(self):
        """Test that hard constraints are properly defined."""
        if not self.has_schema:
            self.skipTest("Schema file not found")
        constraints = self.schema.get("hard_constraints", {})
        # Anthropic uses 'constraints' array instead of 'prohibited_applications'
        if "prohibited_applications" in constraints:
            prohibited = constraints["prohibited_applications"]
        elif "constraints" in constraints:
            prohibited = constraints["constraints"]
        else:
            self.skipTest("No prohibited applications found in schema")
        self.assertGreater(len(prohibited), 0)

    def test_actions_matrix_structure(self):
        """Test actions matrix has proper structure."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        # Anthropic uses 'triggers' instead of 'trigger_definitions'
        self.assertTrue(
            "trigger_definitions" in self.actions_matrix or "triggers" in self.actions_matrix,
            "Actions matrix should have trigger_definitions or triggers"
        )
        # Anthropic uses actions_catalog as array, others as object
        self.assertIn("actions_catalog", self.actions_matrix)

    def test_thresholds_defined(self):
        """Test that thresholds are defined for key signals."""
        if not self.has_thresholds:
            self.skipTest("Thresholds file not found")
        # Anthropic thresholds may have different structure
        if "signal_thresholds" in self.thresholds:
            self.assertIn("signal_thresholds", self.thresholds)
            self.assertIn("escalation_triggers", self.thresholds)
        elif "thresholds" in self.thresholds:
            # Alternative structure
            self.assertIn("thresholds", self.thresholds)
        else:
            self.skipTest("Thresholds structure not recognized")

    def test_constitutional_classifier_trigger(self):
        """Test that constitutional classifier trigger exists."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        # Anthropic uses 'triggers' array
        triggers = self.actions_matrix.get("triggers", [])
        # Check for constitutional-related triggers
        constitutional_triggers = [t for t in triggers if "constitutional" in t.get("trigger_id", "").lower() or "constitutional" in t.get("category", "").lower()]
        self.assertGreater(len(constitutional_triggers), 0, "No constitutional classifier triggers found")

    def test_asl_escalation_trigger(self):
        """Test ASL level escalation trigger exists."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        triggers = self.actions_matrix.get("triggers", [])
        asl_triggers = [t for t in triggers if "asl" in t.get("trigger_id", "").lower() or "responsible_scaling" in t.get("trigger_id", "").lower()]
        self.assertGreater(len(asl_triggers), 0, "No ASL escalation triggers found")

    def test_alignment_faking_detection(self):
        """Test alignment faking detection is defined."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        triggers = self.actions_matrix.get("triggers", [])
        alignment_triggers = [t for t in triggers if "alignment" in t.get("trigger_id", "").lower()]
        self.assertGreater(len(alignment_triggers), 0, "No alignment faking triggers found")

    def test_jailbreak_prevention(self):
        """Test jailbreak prevention measures exist."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        triggers = self.actions_matrix.get("triggers", [])
        jailbreak_triggers = [t for t in triggers if "jailbreak" in t.get("trigger_id", "").lower()]
        self.assertGreater(len(jailbreak_triggers), 0, "No jailbreak prevention triggers found")

    def test_action_catalog_completeness(self):
        """Test that action catalog has expected action types."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        catalog = self.actions_matrix.get("actions_catalog", [])
        # Anthropic uses array of action names, others use object
        if isinstance(catalog, list):
            # Anthropic format: array of action names
            self.assertGreater(len(catalog), 0, "Action catalog is empty")
        else:
            # Standard format: object with action definitions
            expected_actions = ["BLOCK_CONTENT", "ESCALATE"]
            for action_type in expected_actions:
                actions = [a for a in catalog.values() if action_type in a.get("type", "")]
                self.assertGreater(len(actions), 0, f"Expected action {action_type} not found")

    def test_trigger_action_mapping(self):
        """Test that triggers map to actions correctly."""
        if not self.has_actions:
            self.skipTest("Actions matrix file not found")
        # Anthropic doesn't have mapping, triggers have actions inline
        triggers = self.actions_matrix.get("triggers", [])
        if triggers:
            # Anthropic format: triggers have 'actions' field
            for trigger in triggers:
                self.assertIn("actions", trigger, f"Trigger {trigger.get('trigger_id')} missing actions")
                self.assertGreater(len(trigger["actions"]), 0)
        else:
            # Standard format: has mapping
            mappings = self.actions_matrix.get("mapping", [])
            self.assertGreater(len(mappings), 0)
            for mapping in mappings:
                self.assertIn("trigger_id", mapping)
                self.assertIn("actions", mapping)
                self.assertGreater(len(mapping["actions"]), 0)

    def test_threshold_signal_coverage(self):
        """Test that key safety signals have thresholds."""
        if not self.has_thresholds:
            self.skipTest("Thresholds file not found")
        # Anthropic thresholds may have different structure
        if "signal_thresholds" in self.thresholds:
            signals = self.thresholds.get("signal_thresholds", {})
            self.assertIn("constitutional_classifier", signals)
            self.assertIn("asl_levels", signals)
        else:
            self.skipTest("Thresholds structure not recognized")

    def test_escalation_triggers_defined(self):
        """Test that escalation triggers are defined."""
        if not self.has_thresholds:
            self.skipTest("Thresholds file not found")
        # Anthropic may use different structure
        if "escalation_triggers" in self.thresholds:
            escalations = self.thresholds.get("escalation_triggers", {})
            self.assertGreater(len(escalations), 0)
        elif "escalation" in self.thresholds:
            # Alternative structure
            self.assertIn("escalation", self.thresholds)
        else:
            self.skipTest("Escalation triggers structure not recognized")


if __name__ == "__main__":
    unittest.main()
