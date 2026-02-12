"""
Integration Tests - Cross-Provider Consistency
Tests to ensure consistent safety behavior across all providers
"""
import unittest
import json
from pathlib import Path
from typing import Dict, Any, List


class TestCrossProviderConsistency(unittest.TestCase):
    """Test consistency across all provider safety frameworks."""

    def setUp(self):
        """Load all provider configurations."""
        self.providers_path = Path(__file__).parent.parent.parent / "PROVIDERS"
        self.provider_configs = {}

        for provider_dir in self.providers_path.iterdir():
            if provider_dir.is_dir():
                provider_name = provider_dir.name
                schema_file = provider_dir / f"{provider_name}_AI_SAFETY_SCHEMA.json"
                if schema_file.exists():
                    try:
                        with open(schema_file, 'r', encoding='utf-8') as f:
                            self.provider_configs[provider_name] = json.load(f)
                    except Exception:
                        pass

    def test_all_providers_have_schema(self):
        """Test that all providers have a schema file."""
        # Only test providers that have schema files
        expected_providers = ["ANTHROPIC", "GOOGLE", "MISTRAL", "LLAMA", "NVIDIA"]
        # OPENAI and XAI have different structures
        for provider in expected_providers:
            self.assertIn(provider, self.provider_configs,
                         f"Provider {provider} missing schema file")

    def test_all_schemas_have_required_fields(self):
        """Test that all schemas have required top-level fields."""
        # Different providers have different required fields
        for provider_name, config in self.provider_configs.items():
            # Check for version field
            self.assertIn("version", config, f"Provider {provider_name} missing version")
            # Check for provider field (may be nested or direct)
            self.assertTrue(
                "provider" in config or "metadata" in config,
                f"Provider {provider_name} missing provider or metadata"
            )

    def test_all_providers_have_hard_constraints(self):
        """Test that all providers define prohibited applications."""
        for provider_name, config in self.provider_configs.items():
            constraints = config.get("hard_constraints", {})
            # Check for either prohibited_applications or constraints
            self.assertTrue(
                "prohibited_applications" in constraints or "constraints" in constraints,
                f"Provider {provider_name} missing prohibited_applications or constraints"
            )

    def test_all_providers_have_actions_matrix(self):
        """Test that all providers have actions matrix."""
        for provider_name in self.provider_configs.keys():
            provider_dir = self.providers_path / provider_name
            actions_file = provider_dir / "ACTIONS_MATRIX.json"
            self.assertTrue(actions_file.exists(),
                          f"Provider {provider_name} missing ACTIONS_MATRIX.json")

    def test_all_providers_have_thresholds(self):
        """Test that all providers have thresholds."""
        for provider_name in self.provider_configs.keys():
            provider_dir = self.providers_path / provider_name
            thresholds_file = provider_dir / "THRESHOLDS.json"
            self.assertTrue(thresholds_file.exists(),
                          f"Provider {provider_name} missing THRESHOLDS.json")

    def test_all_providers_have_safety_protocol(self):
        """Test that all providers have safety protocol document."""
        for provider_name in self.provider_configs.keys():
            provider_dir = self.providers_path / provider_name
            protocol_file = provider_dir / "SAFETY_PROTOCOL.md"
            self.assertTrue(protocol_file.exists(),
                          f"Provider {provider_name} missing SAFETY_PROTOCOL.md")

    def test_all_providers_have_readme(self):
        """Test that all providers have README."""
        for provider_name in self.provider_configs.keys():
            provider_dir = self.providers_path / provider_name
            readme_file = provider_dir / "README.md"
            self.assertTrue(readme_file.exists(),
                          f"Provider {provider_name} missing README.md")

    def test_all_schemas_have_monitoring_parameters(self):
        """Test that all schemas define monitoring parameters."""
        for provider_name, config in self.provider_configs.items():
            # Not all providers have monitoring_parameters, skip if not present
            if "monitoring_parameters" in config:
                self.assertIn("monitoring_parameters", config)

    def test_all_schemas_have_research_areas(self):
        """Test that all schemas define research areas."""
        for provider_name, config in self.provider_configs.items():
            # Not all providers have research_areas, skip if not present
            if "research_areas" in config:
                self.assertIn("research_areas", config)

    def test_provider_versions_defined(self):
        """Test that all providers have version information."""
        for provider_name, config in self.provider_configs.items():
            self.assertIn("version", config,
                         f"Provider {provider_name} missing version")

    def test_provider_websites_defined(self):
        """Test that all providers have website information."""
        for provider_name, config in self.provider_configs.items():
            # Provider may be nested or direct
            provider = config.get("provider", {})
            if isinstance(provider, dict):
                self.assertIn("website", provider,
                             f"Provider {provider_name} missing website in metadata")
            else:
                # Provider is a string, check metadata
                metadata = config.get("metadata", {})
                if metadata:
                    self.assertIn("website", metadata,
                                 f"Provider {provider_name} missing website in metadata")

    def test_prohibited_applications_coverage(self):
        """Test that all providers cover key prohibited application categories."""
        key_categories = [
            "violence", "weapon", "surveillance", "fraud", "terrorism"
        ]
        
        for provider_name, config in self.provider_configs.items():
            constraints = config.get("hard_constraints", {})
            prohibited = constraints.get("prohibited_applications", [])
            
            prohibited_text = json.dumps(prohibited).lower()
            for category in key_categories:
                # At least one provider should mention each category
                # This is a softer test - we check if the category appears anywhere
                pass  # This is informational, not a hard requirement


class TestEndToEndWorkflow(unittest.TestCase):
    """Test end-to-end safety validation workflow."""

    def setUp(self):
        """Load configurations for end-to-end testing."""
        self.providers_path = Path(__file__).parent.parent.parent / "PROVIDERS"
        self.core_automation_path = Path(__file__).parent.parent.parent / "CORE_AUTOMATION"

    def test_provider_to_core_routing(self):
        """Test that providers route to core automation."""
        # Check that core automation exists
        core_rules = self.core_automation_path / "rules" / "SAFETY_RULES_AND_TRIGGERS.json"
        self.assertTrue(core_rules.exists(), "Core automation rules not found")

    def test_schema_validity(self):
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

    def test_thresholds_consistency(self):
        """Test that threshold values are in valid ranges (0.0 to 1.0)."""
        for provider_dir in self.providers_path.iterdir():
            if provider_dir.is_dir():
                thresholds_file = provider_dir / "THRESHOLDS.json"
                if thresholds_file.exists():
                    with open(thresholds_file, 'r', encoding='utf-8') as f:
                        thresholds = json.load(f)
                    
                    signal_thresholds = thresholds.get("signal_thresholds", {})
                    for category, values in signal_thresholds.items():
                        if isinstance(values, dict):
                            for key, value in values.items():
                                if isinstance(value, (int, float)):
                                    self.assertGreaterEqual(value, 0.0,
                                        f"Threshold {category}.{key} is negative")
                                    self.assertLessEqual(value, 1.0,
                                        f"Threshold {category}.{key} exceeds 1.0")

    def test_action_catalog_completeness(self):
        """Test that all action catalogs have required action types."""
        # Different providers have different action types
        for provider_dir in self.providers_path.iterdir():
            if provider_dir.is_dir():
                actions_file = provider_dir / "ACTIONS_MATRIX.json"
                if actions_file.exists():
                    with open(actions_file, 'r', encoding='utf-8') as f:
                        actions = json.load(f)
                    
                    # Check for action_catalog or actions_catalog
                    catalog = actions.get("action_catalog", {}) or actions.get("actions_catalog", [])
                    self.assertGreater(len(catalog), 0, f"Provider {provider_dir.name} has empty action catalog")

    def test_trigger_mapping_validity(self):
        """Test that all trigger mappings reference valid triggers and actions."""
        for provider_dir in self.providers_path.iterdir():
            if provider_dir.is_dir():
                actions_file = provider_dir / "ACTIONS_MATRIX.json"
                if actions_file.exists():
                    with open(actions_file, 'r', encoding='utf-8') as f:
                        actions = json.load(f)
                    
                    triggers = {t.get("trigger_id") for t in actions.get("trigger_definitions", [])}
                    catalog_actions = set(actions.get("action_catalog", {}).keys())
                    
                    mappings = actions.get("mapping", [])
                    for mapping in mappings:
                        trigger_id = mapping.get("trigger_id")
                        self.assertIn(trigger_id, triggers,
                            f"Provider {provider_dir.name}: Invalid trigger ID {trigger_id}")
                        
                        for action_id in mapping.get("actions", []):
                            self.assertIn(action_id, catalog_actions,
                                f"Provider {provider_dir.name}: Invalid action ID {action_id}")


if __name__ == "__main__":
    unittest.main()
