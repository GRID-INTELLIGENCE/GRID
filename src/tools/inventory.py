#!/usr/bin/env python3
"""System inventory script for agent evolution workflow.

Generates a comprehensive inventory of the system including:
- Manifest files
- Modules with metadata
- CI configuration files
- Test files and coverage
- Code owners
- Evidence for validation
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z-.]+)?(?:\+[0-9A-Za-z-.]+)?$")


def find_manifests(repo_root: Path) -> list[str]:
    """Find all manifest files."""
    manifests = []
    patterns = ["**/manifest.json", "**/system_template.json", "**/components.json", "**/project_template.json"]

    for pattern in patterns:
        for manifest_file in repo_root.glob(pattern):
            # Skip node_modules and other common ignore patterns
            if any(ignore in str(manifest_file) for ignore in ["node_modules", ".git", "__pycache__", ".venv"]):
                continue
            rel_path = str(manifest_file.relative_to(repo_root))
            if rel_path not in manifests:
                manifests.append(rel_path)

    return sorted(manifests)


def parse_components_json(components_file: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Parse components.json and extract module information."""
    modules = []
    try:
        with open(components_file) as f:
            data = json.load(f)
            for comp in data.get("components", []):
                modules.append(
                    {
                        "name": comp.get("name", "unknown"),
                        "path": str(components_file.relative_to(repo_root)),
                        "interface_schema": comp.get("api_contract"),
                        "version": comp.get("version"),
                        "owner": comp.get("owner"),
                        "type": comp.get("type", "module"),
                    }
                )
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return modules


def parse_system_template(system_template_file: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Parse system_template.json and extract module information."""
    modules = []
    try:
        with open(system_template_file) as f:
            data = json.load(f)
            sys_template = data.get("system_template", {})
            module_names = sys_template.get("modules", [])

            for module_name in module_names:
                modules.append(
                    {
                        "name": module_name,
                        "path": str(system_template_file.relative_to(repo_root)),
                        "interface_schema": None,
                        "version": None,
                        "owner": sys_template.get("owner"),
                        "type": "module",
                    }
                )
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return modules


def find_modules(repo_root: Path) -> list[dict[str, Any]]:
    """Find all modules with their metadata."""
    modules = []
    seen_modules = set()

    # Check for components.json files
    for components_file in repo_root.rglob("components.json"):
        if any(ignore in str(components_file) for ignore in ["node_modules", ".git", "__pycache__", ".venv"]):
            continue
        parsed = parse_components_json(components_file, repo_root)
        for module in parsed:
            if module["name"] not in seen_modules:
                modules.append(module)
                seen_modules.add(module["name"])

    # Check for system_template.json files
    for template_file in repo_root.rglob("system_template.json"):
        if any(ignore in str(template_file) for ignore in ["node_modules", ".git", "__pycache__", ".venv"]):
            continue
        parsed = parse_system_template(template_file, repo_root)
        for module in parsed:
            if module["name"] not in seen_modules:
                modules.append(module)
                seen_modules.add(module["name"])

    # Scan grid/ directory for Python modules (Embedded Agentic System)
    grid_dir = repo_root / "grid"
    if grid_dir.exists():
        for py_file in grid_dir.rglob("*.py"):
            if py_file.name == "__init__.py" or any(ignore in str(py_file) for ignore in ["__pycache__", ".git"]):
                continue

            # Extract module name from path
            rel_path = py_file.relative_to(repo_root)
            module_name = py_file.stem

            # Skip if already seen
            if module_name in seen_modules:
                continue

            # Try to infer module type from path
            module_type = "library"
            if "skills" in str(rel_path):
                module_type = "service"
            elif "patterns" in str(rel_path) or "evolution" in str(rel_path) or "knowledge" in str(rel_path):
                module_type = "library"

            modules.append(
                {
                    "name": module_name,
                    "path": str(rel_path),
                    "interface_schema": None,  # Would need to parse to find
                    "version": None,  # Would need to parse __version__ or similar
                    "owner": None,  # Would need to parse CODEOWNERS
                    "type": module_type,
                }
            )
            seen_modules.add(module_name)

    return modules


def find_ci_configs(repo_root: Path) -> list[dict[str, Any]]:
    """Find CI configuration files."""
    ci_files = []

    # GitHub Actions
    workflows_dir = repo_root / ".github" / "workflows"
    if workflows_dir.exists():
        for yml_file in workflows_dir.glob("*.yml"):
            ci_files.append(
                {
                    "path": str(yml_file.relative_to(repo_root)),
                    "provider": "github_actions",
                    "triggers": ["push", "pull_request"],  # Would parse YAML to get actual triggers
                    "stages": ["lint", "unit_test", "contract_test"],  # Would parse to get actual stages
                }
            )
        for yml_file in workflows_dir.glob("*.yaml"):
            ci_files.append(
                {
                    "path": str(yml_file.relative_to(repo_root)),
                    "provider": "github_actions",
                    "triggers": ["push", "pull_request"],
                    "stages": ["lint", "unit_test", "contract_test"],
                }
            )

    # GitLab CI
    gitlab_ci = repo_root / ".gitlab-ci.yml"
    if gitlab_ci.exists():
        ci_files.append(
            {
                "path": str(gitlab_ci.relative_to(repo_root)),
                "provider": "gitlab_ci",
                "triggers": ["push", "merge_request"],
                "stages": [],  # Would parse to get actual stages
            }
        )

    return ci_files


def find_tests(repo_root: Path) -> dict[str, Any]:
    """Find test files and categorize them."""
    tests_dir = repo_root / "tests"
    if not tests_dir.exists():
        return {
            "unit": {"files": [], "runner": "pytest", "count": 0},
            "integration": {"files": [], "runner": "pytest", "count": 0},
            "contract": {"files": [], "runner": "pytest", "count": 0},
        }

    unit_tests = []
    integration_tests = []
    contract_tests = []

    for test_file in tests_dir.rglob("test_*.py"):
        if any(ignore in str(test_file) for ignore in ["__pycache__", ".git"]):
            continue

        rel_path = str(test_file.relative_to(repo_root))

        if "integration" in rel_path or "integration" in test_file.parent.name:
            integration_tests.append(rel_path)
        elif "contract" in rel_path or "contract" in test_file.parent.name:
            contract_tests.append(rel_path)
        else:
            unit_tests.append(rel_path)

    return {
        "unit": {"files": sorted(unit_tests), "runner": "pytest", "count": len(unit_tests)},
        "integration": {"files": sorted(integration_tests), "runner": "pytest", "count": len(integration_tests)},
        "contract": {"files": sorted(contract_tests), "runner": "pytest", "count": len(contract_tests)},
    }


def find_owners(repo_root: Path) -> dict[str, str]:
    """Find code owners from CODEOWNERS file or module metadata."""
    owners = {}

    # Check CODEOWNERS file
    codeowners = repo_root / "CODEOWNERS"
    if codeowners.exists():
        try:
            with open(codeowners) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2:
                            path_pattern = parts[0]
                            owner = parts[1]
                            # Simple mapping - would need glob matching for full implementation
                            if "grid/" in path_pattern:
                                owners["grid"] = owner
        except Exception:
            pass

    # Extract owners from components.json
    for components_file in repo_root.rglob("components.json"):
        try:
            with open(components_file) as f:
                data = json.load(f)
                for comp in data.get("components", []):
                    if comp.get("owner"):
                        owners[comp.get("name")] = comp.get("owner")
        except Exception:
            pass

    return owners


def collect_evidence(repo_root: Path, modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect evidence for validation."""
    evidence = []

    for module in modules:
        module_path = repo_root / module["path"]
        if module_path.exists():
            evidence.append({"file": module["path"], "line": 1, "type": "module_definition"})

    # Add manifest evidence
    for manifest in find_manifests(repo_root):
        evidence.append({"file": manifest, "line": 1, "type": "manifest"})

    return evidence


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate system inventory")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--output", default="inventory.json", help="Output JSON file")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()

    if not repo_root.exists():
        print(f"Error: Repository root does not exist: {repo_root}", file=sys.stderr)
        return 1

    print(f"Generating inventory for: {repo_root}", file=sys.stderr)

    # Collect inventory data
    manifest_paths = find_manifests(repo_root)
    modules = find_modules(repo_root)
    ci_files = find_ci_configs(repo_root)
    tests = find_tests(repo_root)
    owners = find_owners(repo_root)
    evidence = collect_evidence(repo_root, modules)

    inventory = {
        "manifest_paths": manifest_paths,
        "modules": modules,
        "ci_files": ci_files,
        "tests": tests,
        "owners": owners,
        "evidence": evidence,
    }

    # Write output
    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(inventory, f, indent=2)

    print(f"Inventory written to {output_path}", file=sys.stderr)
    print(f"Found {len(manifest_paths)} manifests, {len(modules)} modules, {len(ci_files)} CI configs", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
