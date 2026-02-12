# CI/CD Automation Snippets

Ready-to-use CI/CD automation patterns for agent validation and system evolution workflows.

## A. GitHub Actions - Validate System

Complete workflow for running inventory and validation on pull requests:

```yaml
name: Validate System
on:
  pull_request:
    paths:
      - '**/manifest.json'
      - 'system_template.json'
      - 'modules/**'
      - 'contracts/**'
      - '.github/workflows/agent_validation.yml'
  push:
    branches:
      - main
      - develop

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install jsonschema pyyaml semver openapi-spec-validator

      - name: Run inventory
        id: inventory
        run: |
          python tools/inventory.py --repo . --output inventory.json
        continue-on-error: true

      - name: Run validate_system
        run: |
          python validate_system.py manifest.json || python scaffolds/DOC/validate_system.py system_template.json
        continue-on-error: true

      - name: Upload inventory
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: inventory
          path: inventory.json

      - name: Check contract coverage
        run: |
          python tools/agent_validate.py --check-contracts --inventory inventory.json

  contract_test:
    runs-on: ubuntu-latest
    needs: analyze
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install openapi-spec-validator jsonschema pyyaml

      - name: Validate OpenAPI schemas
        run: |
          python - <<'PY'
          from openapi_spec_validator import validate_spec
          import yaml
          import json
          import sys
          import os

          # Find all OpenAPI files
          openapi_files = []
          for root, dirs, files in os.walk('contracts'):
              for file in files:
                  if file.endswith(('.yaml', '.yml')):
                      openapi_files.append(os.path.join(root, file))

          errors = []
          for spec_path in openapi_files:
              try:
                  with open(spec_path) as f:
                      spec = yaml.safe_load(f)
                  validate_spec(spec)
                  print(f"✓ {spec_path} is valid")
              except Exception as e:
                  errors.append(f"✗ {spec_path}: {e}")

          if errors:
              print("\n".join(errors))
              sys.exit(1)

          print("All OpenAPI schemas valid")
          PY

      - name: Validate JSON schemas
        run: |
          python - <<'PY'
          import json
          import jsonschema
          import os
          import sys

          schema_files = []
          for root, dirs, files in os.walk('contracts'):
              for file in files:
                  if file.endswith('.json'):
                      schema_files.append(os.path.join(root, file))

          errors = []
          for schema_path in schema_files:
              try:
                  with open(schema_path) as f:
                      schema = json.load(f)
                  jsonschema.Draft7Validator.check_schema(schema)
                  print(f"✓ {schema_path} is valid")
              except Exception as e:
                  errors.append(f"✗ {schema_path}: {e}")

          if errors:
              print("\n".join(errors))
              sys.exit(1)

          print("All JSON schemas valid")
          PY

  unit_test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run unit tests
        run: |
          pytest tests/ --cov=grid --cov-report=term-missing --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests

  integration_test:
    runs-on: ubuntu-latest
    needs: [analyze, contract_test]
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run integration tests
        run: |
          pytest tests/integration/ -v

      - name: Dry-run composition root
        run: |
          python - <<'PY'
          import sys
          import os
          sys.path.insert(0, os.getcwd())

          # Try to import and run composition_root dry-run
          try:
              from composition_root import main
              import argparse
              args = argparse.Namespace(dry_run=True)
              result = main(args)
              if result != 0:
                  sys.exit(1)
          except ImportError:
              print("composition_root.py not found, skipping")
              sys.exit(0)
          PY
```

## B. Contract Test Job Skeleton

Standalone contract test job that can be added to existing workflows:

```yaml
  contract_test:
    runs-on: ubuntu-latest
    needs: analyze
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install contract test dependencies
        run: |
          pip install openapi-spec-validator jsonschema pyyaml

      - name: Validate contract schemas
        run: |
          python tools/agent_validate.py --check-contracts

      - name: Run consumer-driven contract tests
        run: |
          pytest tests/contract/ -v
```

## C. Agent Output Validation

Script snippet for validating agent-generated artifacts:

```python
# tools/agent_validate.py snippet
def validate_agent_output(output_json: dict) -> dict:
    """Validate agent output against schema."""
    required_fields = ['task_id', 'files', 'tests', 'pr_text']
    missing = [f for f in required_fields if f not in output_json]

    if missing:
        return {
            "valid": False,
            "errors": [f"Missing required fields: {missing}"]
        }

    # Validate file paths
    for file in output_json.get('files', []):
        if 'path' not in file or 'content' not in file:
            return {
                "valid": False,
                "errors": [f"Invalid file entry: {file}"]
            }

    return {"valid": True, "errors": []}
```

## D. Inventory Automation Script

Reference implementation for `tools/inventory.py`:

```python
#!/usr/bin/env python3
"""System inventory script for agent evolution workflow."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import re

def find_manifests(repo_root: Path) -> List[str]:
    """Find all manifest files."""
    manifests = []
    for pattern in ['**/manifest.json', '**/system_template.json', '**/components.json']:
        manifests.extend(repo_root.glob(pattern))
    return [str(m.relative_to(repo_root)) for m in manifests]

def find_modules(repo_root: Path) -> List[Dict[str, Any]]:
    """Find all modules with their metadata."""
    modules = []

    # Check for components.json
    components_file = repo_root / 'scaffolds' / 'DOC' / 'components.json'
    if components_file.exists():
        with open(components_file) as f:
            data = json.load(f)
            for comp in data.get('components', []):
                modules.append({
                    "name": comp.get('name'),
                    "path": f"scaffolds/DOC/components.json",
                    "interface_schema": comp.get('api_contract'),
                    "version": comp.get('version'),
                    "owner": comp.get('owner'),
                    "type": comp.get('type', 'module')
                })

    # Scan grid/ directory for Python modules
    grid_dir = repo_root / 'grid'
    if grid_dir.exists():
        for py_file in grid_dir.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
            rel_path = str(py_file.relative_to(repo_root))
            modules.append({
                "name": py_file.stem,
                "path": rel_path,
                "interface_schema": None,  # Would need to parse to find
                "version": None,
                "owner": None,
                "type": "library"
            })

    return modules

def find_ci_configs(repo_root: Path) -> List[Dict[str, Any]]:
    """Find CI configuration files."""
    ci_files = []

    # GitHub Actions
    workflows_dir = repo_root / '.github' / 'workflows'
    if workflows_dir.exists():
        for yml_file in workflows_dir.glob('*.yml'):
            ci_files.append({
                "path": str(yml_file.relative_to(repo_root)),
                "provider": "github_actions",
                "triggers": ["push", "pull_request"],  # Would parse YAML to get actual triggers
                "stages": ["lint", "unit_test", "contract_test"]  # Would parse to get actual stages
            })

    return ci_files

def find_tests(repo_root: Path) -> Dict[str, Any]:
    """Find test files and categorize them."""
    tests_dir = repo_root / 'tests'
    if not tests_dir.exists():
        return {"unit": {"files": [], "count": 0}, "integration": {"files": [], "count": 0}, "contract": {"files": [], "count": 0}}

    unit_tests = []
    integration_tests = []
    contract_tests = []

    for test_file in tests_dir.rglob('test_*.py'):
        rel_path = str(test_file.relative_to(repo_root))
        if 'integration' in rel_path:
            integration_tests.append(rel_path)
        elif 'contract' in rel_path:
            contract_tests.append(rel_path)
        else:
            unit_tests.append(rel_path)

    return {
        "unit": {
            "files": unit_tests,
            "runner": "pytest",
            "count": len(unit_tests)
        },
        "integration": {
            "files": integration_tests,
            "runner": "pytest",
            "count": len(integration_tests)
        },
        "contract": {
            "files": contract_tests,
            "runner": "pytest",
            "count": len(contract_tests)
        }
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate system inventory')
    parser.add_argument('--repo', default='.', help='Repository root path')
    parser.add_argument('--output', default='inventory.json', help='Output JSON file')
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()

    inventory = {
        "manifest_paths": find_manifests(repo_root),
        "modules": find_modules(repo_root),
        "ci_files": find_ci_configs(repo_root),
        "tests": find_tests(repo_root),
        "owners": {},  # Would parse CODEOWNERS or similar
        "evidence": []
    }

    with open(args.output, 'w') as f:
        json.dump(inventory, f, indent=2)

    print(f"Inventory written to {args.output}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

## E. Integration with Existing CI

To integrate with existing CI workflows, add this job:

```yaml
  agent_validation:
    runs-on: ubuntu-latest
    if: contains(github.event.pull_request.labels.*.name, 'agent-generated')
    steps:
      - uses: actions/checkout@v4
      - name: Validate agent output
        run: |
          python tools/agent_validate.py --check-all
```

## F. Pre-commit Hook

Add to `.git/hooks/pre-commit` or use pre-commit framework:

```bash
#!/bin/bash
# Validate system before commit
python validate_system.py manifest.json || {
    echo "Validation failed. Commit aborted."
    exit 1
}
```
