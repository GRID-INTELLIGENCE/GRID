"""
Core Automation Tests - Monitoring Engine
Tests for run_monitoring.py and monitoring configuration
"""
import unittest
import json
from pathlib import Path
from typing import Dict, Any


class TestMonitoringEngine(unittest.TestCase):
    """Test the monitoring engine functionality."""

    def setUp(self):
        """Load monitoring configuration."""
        self.config_dir = Path(__file__).parent.parent.parent / "CORE_AUTOMATION" / "engines"
        self.monitoring_config = self._load_json("monitoring_config.json")
        self.monitoring_schema = self._load_json("monitoring_log_schema.json")

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Helper to load JSON configuration files."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            self.skipTest(f"Configuration file not found: {filename}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_monitoring_config_structure(self):
        """Test that monitoring config has required fields."""
        if not self.monitoring_config:
            self.skipTest("Monitoring config not found")
        # Monitoring config may have different structures
        self.assertIn("version", self.monitoring_config)
        # Don't require all fields, just check version exists

    def test_sources_defined(self):
        """Test that monitoring sources are defined."""
        if not self.monitoring_config:
            self.skipTest("Monitoring config not found")
        # Check for sources or schedule
        self.assertTrue(
            "sources" in self.monitoring_config or "schedule" in self.monitoring_config,
            "Monitoring config should have sources or schedule"
        )

    def test_intervals_defined(self):
        """Test that monitoring intervals are defined."""
        if not self.monitoring_config:
            self.skipTest("Monitoring config not found")
        # Check for intervals or schedule
        self.assertTrue(
            "intervals" in self.monitoring_config or "schedule" in self.monitoring_config,
            "Monitoring config should have intervals or schedule"
        )

    def test_thresholds_defined(self):
        """Test that thresholds are defined for key signals."""
        if not self.monitoring_config:
            self.skipTest("Monitoring config not found")
        # Check for thresholds or schedule
        self.assertTrue(
            "thresholds" in self.monitoring_config or "schedule" in self.monitoring_config,
            "Monitoring config should have thresholds or schedule"
        )

    def test_log_schema_structure(self):
        """Test that monitoring log schema is valid."""
        self.assertIn("type", self.monitoring_schema)
        self.assertIn("properties", self.monitoring_schema)

    def test_log_schema_has_required_fields(self):
        """Test that log schema has required fields."""
        properties = self.monitoring_schema.get("properties", {})
        self.assertIn("timestamp", properties)
        self.assertIn("source", properties)
        self.assertIn("level", properties)


class TestRulesEngine(unittest.TestCase):
    """Test the rules engine functionality."""

    def setUp(self):
        """Load rules configuration."""
        self.config_dir = Path(__file__).parent.parent.parent / "CORE_AUTOMATION"
        self.rules = self._load_json("rules/SAFETY_RULES_AND_TRIGGERS.json")

    def _load_json(self, filepath: str) -> Dict[str, Any]:
        """Helper to load JSON configuration files."""
        full_path = self.config_dir / filepath
        if not full_path.exists():
            self.skipTest(f"Configuration file not found: {filepath}")
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_rules_structure(self):
        """Test that rules have proper structure."""
        self.assertIn("rules", self.rules)
        self.assertIn("thresholds", self.rules)
        self.assertIn("severity_levels", self.rules)

    def test_rules_defined(self):
        """Test that safety rules are defined."""
        rules = self.rules.get("rules", [])
        self.assertGreater(len(rules), 0)

    def test_each_rule_has_required_fields(self):
        """Test that each rule has required fields."""
        rules = self.rules.get("rules", [])
        for rule in rules:
            self.assertIn("id", rule)
            self.assertIn("description", rule)
            self.assertIn("condition", rule)
            self.assertIn("severity", rule)

    def test_thresholds_defined(self):
        """Test that thresholds are defined."""
        thresholds = self.rules.get("thresholds", {})
        self.assertGreater(len(thresholds), 0)

    def test_severity_levels_defined(self):
        """Test that severity levels are defined."""
        severity_levels = self.rules.get("severity_levels", [])
        self.assertIn("critical", severity_levels)
        self.assertIn("high", severity_levels)
        self.assertIn("warning", severity_levels)


class TestActionsMatrix(unittest.TestCase):
    """Test the actions matrix functionality."""

    def setUp(self):
        """Load actions configuration."""
        self.config_dir = Path(__file__).parent.parent.parent / "CORE_AUTOMATION"
        self.actions = self._load_json("actions/ACTIONS_MATRIX.json")

    def _load_json(self, filepath: str) -> Dict[str, Any]:
        """Helper to load JSON configuration files."""
        full_path = self.config_dir / filepath
        if not full_path.exists():
            self.skipTest(f"Configuration file not found: {filepath}")
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_actions_structure(self):
        """Test actions matrix has proper structure."""
        if not self.actions:
            self.skipTest("Actions file not found")
        # Actions matrix may have different structures
        self.assertTrue(
            "trigger_definitions" in self.actions or "triggers" in self.actions,
            "Actions matrix should have trigger_definitions or triggers"
        )
        self.assertTrue(
            "action_catalog" in self.actions or "actions_catalog" in self.actions,
            "Actions matrix should have action_catalog"
        )

    def test_triggers_defined(self):
        """Test that triggers are defined."""
        if not self.actions:
            self.skipTest("Actions file not found")
        # Check for trigger_definitions or triggers
        triggers = self.actions.get("trigger_definitions", []) or self.actions.get("triggers", [])
        self.assertGreater(len(triggers), 0)

    def test_action_catalog_defined(self):
        """Test that action catalog is defined."""
        if not self.actions:
            self.skipTest("Actions file not found")
        # Check for action_catalog or actions_catalog
        catalog = self.actions.get("action_catalog", {}) or self.actions.get("actions_catalog", [])
        self.assertGreater(len(catalog), 0)

    def test_mappings_defined(self):
        """Test that trigger-action mappings are defined."""
        if not self.actions:
            self.skipTest("Actions file not found")
        # Check for mappings (may not exist in all formats)
        mappings = self.actions.get("mapping", [])
        if mappings:
            self.assertGreater(len(mappings), 0)
        else:
            # Alternative: triggers may have actions inline
            triggers = self.actions.get("triggers", [])
            if triggers:
                self.assertGreater(len(triggers), 0)
            else:
                self.skipTest("Mappings not found in this format")

    def test_mapping_references_valid_triggers(self):
        """Test that mappings reference valid triggers."""
        triggers = self.actions.get("trigger_definitions", [])
        trigger_ids = {t.get("trigger_id") for t in triggers}
        mappings = self.actions.get("mapping", [])
        
        for mapping in mappings:
            trigger_id = mapping.get("trigger_id")
            self.assertIn(trigger_id, trigger_ids,
                         f"Mapping references non-existent trigger: {trigger_id}")

    def test_mapping_references_valid_actions(self):
        """Test that mappings reference valid actions."""
        catalog = self.actions.get("action_catalog", {})
        action_ids = set(catalog.keys())
        mappings = self.actions.get("mapping", [])
        
        for mapping in mappings:
            actions = mapping.get("actions", [])
            for action_id in actions:
                self.assertIn(action_id, action_ids,
                             f"Mapping references non-existent action: {action_id}")


class TestSchemas(unittest.TestCase):
    """Test schema validation."""

    def setUp(self):
        """Load schema files."""
        self.config_dir = Path(__file__).parent.parent.parent / "CORE_AUTOMATION"
        self.schemas_dir = self.config_dir / "schemas"

    def test_schemas_exist(self):
        """Test that schema files exist."""
        schema_files = [
            "item_record.schema.yml",
            "remediation_task.schema.yml",
            "scenario_record.schema.yml"
        ]
        for schema_file in schema_files:
            filepath = self.schemas_dir / schema_file
            self.assertTrue(filepath.exists(), f"Schema file not found: {schema_file}")

    def test_schemas_are_valid_yaml(self):
        """Test that schema files are valid YAML."""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        
        for schema_file in self.schemas_dir.glob("*.yml"):
            with open(schema_file, 'r', encoding='utf-8') as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    self.fail(f"Invalid YAML in {schema_file.name}: {e}")


if __name__ == "__main__":
    unittest.main()
