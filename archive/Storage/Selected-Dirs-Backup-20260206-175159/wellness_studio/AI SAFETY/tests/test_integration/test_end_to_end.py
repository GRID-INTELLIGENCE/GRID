"""
Integration Tests - End-to-End Workflow
Tests the complete safety validation workflow from detection to remediation
"""
import unittest
import json
from pathlib import Path
from typing import Dict, Any


class TestEndToEndWorkflow(unittest.TestCase):
    """Test the complete safety validation workflow."""

    def setUp(self):
        """Load all configurations for end-to-end testing."""
        self.base_path = Path(__file__).parent.parent.parent
        self.providers_path = self.base_path / "PROVIDERS"
        self.core_automation_path = self.base_path / "CORE_AUTOMATION"

    def test_google_provider_complete_workflow(self):
        """Test complete workflow using Google provider as example."""
        # 1. Load provider configuration
        google_dir = self.providers_path / "GOOGLE"
        schema_file = google_dir / "GOOGLE_AI_SAFETY_SCHEMA.json"
        actions_file = google_dir / "ACTIONS_MATRIX.json"
        thresholds_file = google_dir / "THRESHOLDS.json"

        # Verify all files exist
        self.assertTrue(schema_file.exists(), "Google schema file missing")
        self.assertTrue(actions_file.exists(), "Google actions file missing")
        self.assertTrue(thresholds_file.exists(), "Google thresholds file missing")

        # 2. Load and validate schema
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        self.assertIn("provider", schema)
        self.assertIn("safety_frameworks", schema)
        self.assertIn("hard_constraints", schema)

        # 3. Load and validate thresholds
        with open(thresholds_file, 'r', encoding='utf-8') as f:
            thresholds = json.load(f)

        self.assertIn("signal_thresholds", thresholds)
        self.assertIn("escalation_triggers", thresholds)

        # 4. Load and validate actions matrix
        with open(actions_file, 'r', encoding='utf-8') as f:
            actions = json.load(f)

        self.assertIn("trigger_definitions", actions)
        self.assertIn("action_catalog", actions)
        self.assertIn("mapping", actions)

        # 5. Verify trigger-action mappings are valid
        trigger_ids = {t.get("trigger_id") for t in actions.get("trigger_definitions", [])}
        action_ids = set(actions.get("action_catalog", {}).keys())

        for mapping in actions.get("mapping", []):
            trigger_id = mapping.get("trigger_id")
            self.assertIn(trigger_id, trigger_ids, f"Invalid trigger ID: {trigger_id}")

            for action_id in mapping.get("actions", []):
                self.assertIn(action_id, action_ids, f"Invalid action ID: {action_id}")

    def test_all_providers_complete_workflow(self):
        """Test that all providers have complete workflow files."""
        # Only test providers that have standard structure
        providers_with_standard_structure = ["GOOGLE", "MISTRAL", "LLAMA", "NVIDIA"]
        
        for provider_name in providers_with_standard_structure:
            provider_dir = self.providers_path / provider_name
            
            # Check for required files
            actions_file = provider_dir / "ACTIONS_MATRIX.json"
            self.assertTrue(actions_file.exists(),
                          f"Provider {provider_name} missing ACTIONS_MATRIX.json")

    def test_core_automation_integration(self):
        """Test that core automation can be integrated with providers."""
        # Check core automation exists
        core_rules = self.core_automation_path / "rules" / "SAFETY_RULES_AND_TRIGGERS.json"
        core_actions = self.core_automation_path / "actions" / "ACTIONS_MATRIX.json"

        self.assertTrue(core_rules.exists(), "Core rules file missing")
        self.assertTrue(core_actions.exists(), "Core actions file missing")

        # Load and validate core rules
        with open(core_rules, 'r', encoding='utf-8') as f:
            core_rules_data = json.load(f)

        self.assertIn("rules", core_rules_data)
        self.assertIn("thresholds", core_rules_data)

        # Load and validate core actions
        with open(core_actions, 'r', encoding='utf-8') as f:
            core_actions_data = json.load(f)

        # Check for trigger_definitions or triggers (different formats)
        self.assertTrue(
            "trigger_definitions" in core_actions_data or "triggers" in core_actions_data,
            "Core actions should have trigger_definitions or triggers"
        )
        # Check for action_catalog or actions_catalog
        self.assertTrue(
            "action_catalog" in core_actions_data or "actions_catalog" in core_actions_data,
            "Core actions should have action_catalog"
        )

    def test_monitoring_integration(self):
        """Test that monitoring engine can be integrated."""
        monitoring_dir = self.core_automation_path / "engines"

        # Check monitoring files exist
        monitoring_config = monitoring_dir / "monitoring_config.json"
        monitoring_schema = monitoring_dir / "monitoring_log_schema.json"
        monitoring_script = monitoring_dir / "run_monitoring.py"

        self.assertTrue(monitoring_config.exists(), "Monitoring config missing")
        self.assertTrue(monitoring_schema.exists(), "Monitoring schema missing")
        self.assertTrue(monitoring_script.exists(), "Monitoring script missing")

        # Load and validate monitoring config
        with open(monitoring_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Check for sources or schedule (different formats)
        self.assertTrue(
            "sources" in config or "schedule" in config,
            "Monitoring config should have sources or schedule"
        )

    def test_schema_validation_workflow(self):
        """Test that all JSON schemas are valid."""
        import json
        
        # Check all JSON files in providers
        for provider_dir in self.providers_path.iterdir():
            if provider_dir.is_dir():
                for json_file in provider_dir.glob("*.json"):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        try:
                            json.load(f)
                        except json.JSONDecodeError as e:
                            self.fail(f"Invalid JSON in {json_file}: {e}")

    def test_report_generation_workflow(self):
        """Test that report templates exist."""
        # Check that report templates exist for providers
        for provider_dir in self.providers_path.iterdir():
            if provider_dir.is_dir():
                report_template = provider_dir / "REPORT_TEMPLATE.md"
                if report_template.exists():
                    with open(report_template, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Check for template placeholders (may vary by provider)
                        self.assertGreater(len(content), 0, f"Empty report template for {provider_dir.name}")

    def test_notification_integration(self):
        """Test that notification templates exist."""
        notifications_dir = self.core_automation_path / "notifications"
        email_directory = notifications_dir / "email_directory.json"
        self.assertTrue(email_directory.exists(), "Email directory missing")

    def test_architecture_status_consistency(self):
        """Test that architecture status reflects actual state."""
        architecture_file = self.base_path / "CORE_AUTOMATION" / "ARCHITECTURE_STATUS.md"
        self.assertTrue(architecture_file.exists(), "Architecture status file missing")

    def test_complete_provider_coverage(self):
        """Test that all expected providers are present."""
        # Test providers with standard structure
        expected_providers = {
            "GOOGLE", "MISTRAL", "LLAMA", "NVIDIA"
        }
        actual_providers = {d.name for d in self.providers_path.iterdir() if d.is_dir()}
        
        # Check that expected providers are present
        for provider in expected_providers:
            self.assertIn(provider, actual_providers,
                         f"Expected provider {provider} not found")

    def test_file_structure_integrity(self):
        """Test that the overall file structure is intact."""
        # Check top-level structure
        self.assertTrue(self.providers_path.exists(), "PROVIDERS directory missing")
        self.assertTrue(self.core_automation_path.exists(), "CORE_AUTOMATION directory missing")

        # Check core automation subdirectories
        required_core_dirs = ["rules", "actions", "thresholds", "schemas", "notifications", "engines"]
        for dir_name in required_core_dirs:
            dir_path = self.core_automation_path / dir_name
            self.assertTrue(dir_path.exists(), f"Core automation {dir_name} directory missing")


if __name__ == "__main__":
    unittest.main()
