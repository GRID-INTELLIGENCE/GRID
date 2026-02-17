#!/usr/bin/env python3
"""Agent output validation script.

Validates agent-generated artifacts against schemas and checks contract coverage.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    jsonschema = None

try:
    import yaml  # type: ignore[import-untyped]
    from openapi_spec_validator import validate_spec  # type: ignore[import-untyped]
except ImportError:
    yaml = None
    validate_spec = None


def validate_json_schema(data: dict[str, Any], schema_path: Path) -> list[str]:
    """Validate JSON data against schema."""
    errors = []

    if jsonschema is None:
        errors.append("jsonschema not installed. Install with: pip install jsonschema")
        return errors

    try:
        with open(schema_path) as f:
            schema = json.load(f)

        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(data):
            errors.append(f"{error.json_path}: {error.message}")
    except FileNotFoundError:
        errors.append(f"Schema file not found: {schema_path}")
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON schema: {e}")
    except jsonschema.SchemaError as e:
        errors.append(f"Invalid schema: {e}")

    return errors


def validate_agent_output(output_json: dict[str, Any]) -> dict[str, Any]:
    """Validate agent output structure."""
    required_fields = ["task_id", "files", "tests", "pr_text"]
    missing = [f for f in required_fields if f not in output_json]

    errors = []
    if missing:
        errors.append(f"Missing required fields: {missing}")

    # Validate file entries
    for file in output_json.get("files", []):
        if "path" not in file or "content" not in file:
            errors.append(f"Invalid file entry: {file}")
        if file.get("action") not in ["create", "update", "delete"]:
            errors.append(f"Invalid file action: {file.get('action')}")

    # Validate test entries
    for test in output_json.get("tests", []):
        if "path" not in test or "content" not in test:
            errors.append(f"Invalid test entry: {test}")

    return {"valid": len(errors) == 0, "errors": errors}


def check_contracts(repo_root: Path, inventory_path: Path | None = None) -> dict[str, Any]:
    """Check contract coverage from inventory."""
    if inventory_path is None:
        inventory_path = repo_root / "inventory.json"

    if not inventory_path.exists():
        return {
            "contract_coverage": 0.0,
            "modules_with_schemas": 0,
            "total_modules": 0,
            "errors": ["Inventory file not found"],
        }

    try:
        with open(inventory_path) as f:
            inventory = json.load(f)
    except Exception as e:
        return {
            "contract_coverage": 0.0,
            "modules_with_schemas": 0,
            "total_modules": 0,
            "errors": [f"Failed to load inventory: {e}"],
        }

    modules = inventory.get("modules", [])
    total_modules = len(modules)
    modules_with_schemas = sum(1 for m in modules if m.get("interface_schema"))

    coverage = modules_with_schemas / total_modules if total_modules > 0 else 0.0

    # Validate schemas exist and are parseable
    schema_errors = []
    contracts_dir = repo_root / "contracts"

    for module in modules:
        schema_path = module.get("interface_schema")
        if schema_path:
            # Handle OpenAPI references like "openapi.yaml#/components/schemas/BassSpec"
            if "#/" in schema_path:
                schema_path = schema_path.split("#/")[0]

            # Try to find schema file
            if schema_path.startswith("contracts/"):
                full_path = repo_root / schema_path
            elif contracts_dir.exists():
                full_path = contracts_dir / schema_path
            else:
                full_path = repo_root / schema_path

            if not full_path.exists():
                schema_errors.append(f"Schema not found for {module['name']}: {schema_path}")
            else:
                # Try to validate schema
                if full_path.suffix in [".yaml", ".yml"]:
                    if yaml and validate_spec:
                        try:
                            with open(full_path) as f:
                                spec = yaml.safe_load(f)
                            validate_spec(spec)
                        except Exception as e:
                            schema_errors.append(f"Invalid OpenAPI schema for {module['name']}: {e}")
                elif full_path.suffix == ".json":
                    if jsonschema:
                        try:
                            with open(full_path) as f:
                                schema = json.load(f)
                            jsonschema.Draft7Validator.check_schema(schema)
                        except Exception as e:
                            schema_errors.append(f"Invalid JSON schema for {module['name']}: {e}")

    return {
        "contract_coverage": coverage,
        "modules_with_schemas": modules_with_schemas,
        "total_modules": total_modules,
        "schema_errors": schema_errors,
        "errors": schema_errors,
    }


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate agent output and contracts")
    parser.add_argument("--check-schema", help="Validate JSON against schema file")
    parser.add_argument("--check-contracts", action="store_true", help="Check contract coverage")
    parser.add_argument("--check-all", action="store_true", help="Run all checks")
    parser.add_argument("--inventory", default="inventory.json", help="Inventory file path")
    parser.add_argument("--repo", default=".", help="Repository root path")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()

    errors = []
    warnings = []

    # Check contracts
    if args.check_contracts or args.check_all:
        contract_result = check_contracts(repo_root, Path(args.inventory))
        if contract_result.get("errors"):
            errors.extend(contract_result["errors"])

        coverage = contract_result.get("contract_coverage", 0.0)
        if coverage < 1.0:
            warnings.append(f"Contract coverage: {coverage:.1%} (target: 100%)")
        else:
            print(f"✓ Contract coverage: {coverage:.1%}")

        print(
            f"Modules with schemas: {contract_result.get('modules_with_schemas')}/{contract_result.get('total_modules')}"
        )

    # Check schema
    if args.check_schema:
        try:
            with open(args.check_schema) as f:
                data = json.load(f)
            schema_path = repo_root / "tools" / "agent_prompts" / "schema.json"
            schema_errors = validate_json_schema(data, schema_path)
            if schema_errors:
                errors.extend(schema_errors)
            else:
                print("✓ JSON schema validation passed")
        except Exception as e:
            errors.append(f"Schema validation failed: {e}")

    # Print results
    if warnings:
        for warning in warnings:
            print(f"⚠ {warning}", file=sys.stderr)

    if errors:
        print("✗ Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if not errors and not warnings:
        print("✓ All validations passed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
