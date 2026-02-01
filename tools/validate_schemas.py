#!/usr/bin/env python3
"""
GRID Schema Validation Tool

Validates JSON files against schemas and generates comprehensive reports.
Used in CI/CD pipeline to ensure data consistency.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import SchemaError, ValidationError


class SchemaValidator:
    def __init__(self, schemas_dir: str = "schemas", verbose: bool = False):
        self.schemas_dir = Path(schemas_dir)
        self.verbose = verbose
        self.schemas: dict[str, dict] = {}
        self.validation_results: list[dict] = []

        self.load_schemas()

    def load_schemas(self) -> None:
        """Load all schema files from the schemas directory."""
        if not self.schemas_dir.exists():
            print(f"Warning: Schemas directory '{self.schemas_dir}' not found")
            return

        schema_files = list(self.schemas_dir.glob("*.schema.json"))
        if self.verbose:
            print(f"Found {len(schema_files)} schema files")

        for schema_file in schema_files:
            try:
                with open(schema_file, encoding="utf-8") as f:
                    schema = json.load(f)

                # Use filename without extension as schema name
                schema_name = schema_file.stem.replace(".schema", "")
                self.schemas[schema_name] = schema

                if self.verbose:
                    print(f"✓ Loaded schema: {schema_name}")

            except Exception as e:
                print(f"✗ Failed to load schema {schema_file}: {e}")

    def find_json_files(self, root_dir: str = ".") -> list[Path]:
        """Find all JSON files in the project, excluding certain directories."""
        json_files = []

        exclude_dirs = {
            ".git",
            "__pycache__",
            ".mypy_cache",
            "node_modules",
            ".venv",
            ".pytest_cache",
            ".next",
            "dist",
            "build",
            ".serverless",
            "coverage",
            "htmlcov",
        }

        for root, dirs, files in os.walk(root_dir):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith(".json"):
                    json_files.append(Path(root) / file)

        return json_files

    def match_schema(self, file_path: Path) -> str | None:
        """Match a JSON file to an appropriate schema based on filename patterns."""
        filename = file_path.name.lower()
        filepath_str = str(file_path).lower()

        # Schema matching rules
        if "package" in filename and filename.endswith("package.json"):
            return "package"
        elif "telemetry" in filename or "data/telemetry" in filepath_str:
            return "telemetry"
        elif any(keyword in filename for keyword in ["config", "settings", "grid-config"]):
            return "grid-config"
        else:
            return None  # No specific schema match

    def validate_file(self, file_path: Path) -> dict[str, Any]:
        """Validate a single JSON file."""
        result = {"file": str(file_path), "valid_json": False, "schema_valid": None, "schema_name": None, "errors": []}

        try:
            # First, check if it's valid JSON
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            result["valid_json"] = True

            # Try to validate against schema
            schema_name = self.match_schema(file_path)
            if schema_name and schema_name in self.schemas:
                schema = self.schemas[schema_name]
                try:
                    jsonschema.validate(data, schema)
                    result["schema_valid"] = True
                    result["schema_name"] = schema_name
                except (ValidationError, SchemaError) as e:
                    result["schema_valid"] = False
                    result["schema_name"] = schema_name
                    result["errors"].append(
                        {
                            "type": "schema_validation",
                            "message": str(e),
                            "path": list(e.absolute_path) if hasattr(e, "absolute_path") else [],
                        }
                    )
            else:
                result["schema_valid"] = None  # No schema to validate against

        except json.JSONDecodeError as e:
            result["errors"].append({"type": "json_parse", "message": f"Invalid JSON: {e}"})
        except Exception as e:
            result["errors"].append({"type": "unknown", "message": f"Unexpected error: {e}"})

        return result

    def validate_all_files(self, root_dir: str = ".") -> dict[str, Any]:
        """Validate all JSON files and return comprehensive results."""
        print("🔍 Starting schema validation...")

        json_files = self.find_json_files(root_dir)
        print(f"Found {len(json_files)} JSON files to validate")

        results = []
        for file_path in json_files:
            if self.verbose:
                print(f"Validating: {file_path}")
            result = self.validate_file(file_path)
            results.append(result)

            # Print immediate feedback
            if result["valid_json"]:
                status = "✓"
                if result["schema_valid"] is True:
                    status += " (schema valid)"
                elif result["schema_valid"] is False:
                    status += " (schema invalid)"
                else:
                    status += " (no schema)"
            else:
                status = "✗ (invalid JSON)"

            print(f"  {status} {file_path}")

        # Generate summary
        summary = self.generate_summary(results)
        self.save_report(summary, results)

        return summary

    def generate_summary(self, results: list[dict]) -> dict[str, Any]:
        """Generate a summary of validation results."""
        total_files = len(results)
        valid_json = sum(1 for r in results if r["valid_json"])
        schema_valid = sum(1 for r in results if r["schema_valid"] is True)
        schema_invalid = sum(1 for r in results if r["schema_valid"] is False)
        no_schema = sum(1 for r in results if r["schema_valid"] is None)

        coverage_percent = (valid_json / total_files * 100) if total_files > 0 else 0
        schema_coverage_percent = (
            (schema_valid / (schema_valid + schema_invalid) * 100) if (schema_valid + schema_invalid) > 0 else 0
        )

        return {
            "total_files": total_files,
            "valid_json": valid_json,
            "invalid_json": total_files - valid_json,
            "schema_valid": schema_valid,
            "schema_invalid": schema_invalid,
            "no_schema_available": no_schema,
            "json_coverage_percent": round(coverage_percent, 1),
            "schema_coverage_percent": round(schema_coverage_percent, 1),
            "passed": valid_json == total_files and schema_invalid == 0,
        }

    def save_report(self, summary: dict[str, Any], results: list[dict]) -> None:
        """Save validation report to file."""
        os.makedirs("reports", exist_ok=True)

        report = {
            "summary": summary,
            "results": results,
            "schemas_used": list(self.schemas.keys()),
            "timestamp": str(Path.cwd()),
        }

        with open("reports/schema_validation_detailed.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n📄 Detailed report saved to: reports/schema_validation_detailed.json")

    def print_summary(self, summary: dict[str, Any]) -> None:
        """Print a human-readable summary."""
        print("\n📊 Schema Validation Summary")
        print("=" * 50)
        print(f"Total JSON files: {summary['total_files']}")
        print(f"Valid JSON: {summary['valid_json']}/{summary['total_files']} ({summary['json_coverage_percent']}%)")
        print(f"Schema validation passed: {summary['schema_valid']}")
        print(f"Schema validation failed: {summary['schema_invalid']}")
        print(f"No schema available: {summary['no_schema_available']}")
        if summary["schema_valid"] + summary["schema_invalid"] > 0:
            print(f"Schema coverage: {summary['schema_coverage_percent']}%")

        if summary["passed"]:
            print("\n✅ All validations passed!")
        else:
            print("\n❌ Some validations failed!")
            if summary["invalid_json"] > 0:
                print(f"   {summary['invalid_json']} files have invalid JSON")
            if summary["schema_invalid"] > 0:
                print(f"   {summary['schema_invalid']} files failed schema validation")


def main():
    parser = argparse.ArgumentParser(description="Validate JSON files against schemas")
    parser.add_argument("--schemas-dir", default="schemas", help="Directory containing schema files")
    parser.add_argument("--root-dir", default=".", help="Root directory to scan for JSON files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit with non-zero code on validation failures")

    args = parser.parse_args()

    validator = SchemaValidator(args.schemas_dir, args.verbose)
    summary = validator.validate_all_files(args.root_dir)
    validator.print_summary(summary)

    # Exit with appropriate code
    if args.fail_on_error and not summary["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
