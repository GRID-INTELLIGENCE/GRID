"""
Contract loader with YAML schema alignment.
Maps YAML structure to Pydantic models with proper field aliases.
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .contracts import (
    AccountabilityContract,
    ComplianceRequirement,
    DataValidationRule,
    PerformanceSLA,
    SecurityRequirement,
    ServiceLevelObjective,
)

logger = logging.getLogger(__name__)


class ContractLoader:
    """Loads accountability contracts from YAML with schema alignment."""

    def __init__(self, config_path: Path | None = None):
        """Initialize contract loader.

        Args:
            config_path: Path to contracts YAML file.
                Defaults to standard location.
        """
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent.parent.parent / "config" / "accountability" / "contracts.yaml"
            )

        self.config_path = Path(config_path)
        self._contract_cache: AccountabilityContract | None = None

    def load_contracts(self, force_reload: bool = False) -> AccountabilityContract:
        """Load contracts from YAML with schema alignment.

        Args:
            force_reload: Force reload even if cached.

        Returns:
            AccountabilityContract with loaded and validated data.
        """
        if self._contract_cache is not None and not force_reload:
            return self._contract_cache

        try:
            # Load YAML
            with open(self.config_path, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            # Align YAML schema to Pydantic models
            aligned_data = self._align_yaml_schema(yaml_data)

            # Validate and create contract
            contract = AccountabilityContract(**aligned_data)

            self._contract_cache = contract
            logger.info(f"Loaded accountability contract: {contract.service_name} v{contract.version}")

            return contract

        except FileNotFoundError:
            logger.error(f"Contract file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in contract file: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Contract validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load contracts: {e}")
            raise

    def _align_yaml_schema(self, yaml_data: dict[str, Any]) -> dict[str, Any]:
        """Align YAML schema to Pydantic model fields.

        Maps:
        - defaults.security -> default_security
        - defaults.compliance -> default_compliance
        - service_level_objectives -> slos
        """

        aligned_data = {
            "service_name": yaml_data.get("service_name", "unknown"),
            "version": yaml_data.get("version", "1.0.0"),
            "description": yaml_data.get("description", ""),
        }

        # Handle defaults section
        defaults = yaml_data.get("defaults", {})
        if defaults:
            # Map defaults.security -> default_security
            if "security" in defaults:
                aligned_data["default_security"] = SecurityRequirement(**defaults["security"])

            # Map defaults.compliance -> default_compliance
            if "compliance" in defaults:
                aligned_data["default_compliance"] = ComplianceRequirement(**defaults["compliance"])

        # Handle endpoints
        endpoints = yaml_data.get("endpoints", [])
        aligned_endpoints = []

        for endpoint_data in endpoints:
            aligned_endpoint = self._align_endpoint_data(endpoint_data)
            aligned_endpoints.append(aligned_endpoint)

        aligned_data["endpoints"] = aligned_endpoints

        # Handle service_level_objectives -> slos
        slos = yaml_data.get("service_level_objectives", [])
        aligned_slos = []

        for slo_data in slos:
            aligned_slo = ServiceLevelObjective(**slo_data)
            aligned_slos.append(aligned_slo)

        aligned_data["slos"] = aligned_slos

        return aligned_data

    def _align_endpoint_data(self, endpoint_data: dict[str, Any]) -> dict[str, Any]:
        """Align individual endpoint data to Pydantic model."""

        aligned = {
            "path": endpoint_data["path"],
            "methods": endpoint_data["methods"],
            "description": endpoint_data.get("description", ""),
        }

        # Handle performance section
        if "performance" in endpoint_data:
            aligned["performance"] = PerformanceSLA(**endpoint_data["performance"])

        # Handle security section
        if "security" in endpoint_data:
            aligned["security"] = SecurityRequirement(**endpoint_data["security"])

        # Handle compliance section
        if "compliance" in endpoint_data:
            aligned["compliance"] = ComplianceRequirement(**endpoint_data["compliance"])

        # Handle validation rules
        if "request_validation" in endpoint_data:
            aligned["request_validation"] = self._align_validation_rules(endpoint_data["request_validation"])

        if "response_validation" in endpoint_data:
            aligned["response_validation"] = self._align_validation_rules(endpoint_data["response_validation"])

        # Handle other fields
        if "tags" in endpoint_data:
            aligned["tags"] = endpoint_data["tags"]

        if "enabled" in endpoint_data:
            aligned["enabled"] = endpoint_data["enabled"]

        return aligned

    def _align_validation_rules(self, rules_data: dict[str, Any]) -> dict[str, DataValidationRule]:
        """Align validation rules to DataValidationRule objects."""

        aligned_rules = {}

        for field_name, rule_data in rules_data.items():
            if isinstance(rule_data, dict):
                # Set the field name from the dictionary key
                rule_data_with_field = {"field": field_name, **rule_data}
                aligned_rules[field_name] = DataValidationRule(**rule_data_with_field)
            else:
                # Handle simple type specification
                aligned_rules[field_name] = DataValidationRule(field=field_name, type=rule_data, required=True)

        return aligned_rules

    def validate_websocket_support(self) -> bool:
        """Validate that WebSocket methods and wildcard paths are supported."""

        try:
            contract = self.load_contracts()

            websocket_endpoints = [ep for ep in contract.endpoints if "WEBSOCKET" in ep.methods]

            wildcard_endpoints = [ep for ep in contract.endpoints if "*" in ep.path]

            logger.info(f"Found {len(websocket_endpoints)} WebSocket endpoints")
            logger.info(f"Found {len(wildcard_endpoints)} wildcard endpoints")

            # Test matching logic
            test_cases = [
                ("/api/v1/rag/ws/123", "WEBSOCKET"),
                ("/api/v1/rag/ws/session-456", "WEBSOCKET"),
                ("/api/v1/users/123", "GET"),
            ]

            for path, method in test_cases:
                contract = contract.get_endpoint_contract(path, method)
                if contract:
                    logger.info(f"✓ Matched {method} {path} to {contract.path}")
                else:
                    logger.warning(f"✗ No match for {method} {path}")

            return True

        except Exception as e:
            logger.error(f"WebSocket validation failed: {e}")
            return False


# Global contract loader instance
_global_contract_loader: ContractLoader | None = None


def get_contract_loader() -> ContractLoader:
    """Get global contract loader instance."""
    global _global_contract_loader
    if _global_contract_loader is None:
        _global_contract_loader = ContractLoader()
    return _global_contract_loader


def load_accountability_contract(force_reload: bool = False) -> AccountabilityContract:
    """Load accountability contract using global loader."""
    return get_contract_loader().load_contracts(force_reload)
