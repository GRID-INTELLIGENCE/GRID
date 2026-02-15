#!/usr/bin/env python3
"""
Project Path Protection Validator
Validates operations against protected project path rules
"""

import json
from enum import Enum
from pathlib import Path


class ProtectionLevel(Enum):
    """Protection enforcement levels"""

    EXPLICIT = "EXPLICIT"
    IMPLICIT = "IMPLICIT"


class ViolationType(Enum):
    """Types of protection violations"""

    PATH_CHANGE = "path_change"
    MOVE_OPERATION = "move_operation"
    RENAME_OPERATION = "rename_operation"
    RELOCATION = "relocation"
    RESTRUCTURE = "restructure"


class PathProtectionViolation(Exception):
    """Raised when a protected path operation is attempted"""

    pass


class ProjectPathProtector:
    """Validates and enforces project path protection rules"""

    def __init__(self, config_path: str = "config/project_path_protection.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.protected_projects = self.config["protected_projects"]
        self.enforcement_rules = self.config["enforcement_rules"]

    def _load_config(self) -> dict:
        """Load protection configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Protection config not found: {self.config_path}")

        with open(self.config_path) as f:
            return json.load(f)

    def _normalize_path(self, path: str) -> str:
        """Normalize path for comparison"""
        return str(Path(path)).lower().replace("/", "\\")

    def is_protected_path(self, path: str) -> tuple[bool, str | None]:
        """
        Check if a path is protected
        Returns: (is_protected, project_name)
        """
        normalized = self._normalize_path(path)

        for project_name, project_config in self.protected_projects.items():
            canonical = self._normalize_path(project_config["canonical_path"])

            # Check canonical path
            if normalized.startswith(canonical):
                return True, project_name

            # Check alternate paths
            for alt_path in project_config.get("alternate_paths", []):
                if normalized.startswith(self._normalize_path(alt_path)):
                    return True, project_name

        return False, None

    def validate_operation(
        self, operation: str, source_path: str, dest_path: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Validate if an operation is allowed
        Returns: (is_allowed, reason)
        """
        # Check if source path is protected
        is_protected, project_name = self.is_protected_path(source_path)

        if not is_protected:
            return True, None

        # Get project config
        project_config = self.protected_projects[project_name]

        # Check if modification is allowed
        if not project_config["modification_allowed"]:
            # Check prohibited operations
            prohibited = self.enforcement_rules["prohibited_operations"]

            if operation in prohibited:
                reason = f"Operation '{operation}' is prohibited on protected project '{project_name}'"
                return False, reason

        # If destination path is provided, check if it's outside protected area
        if dest_path:
            dest_normalized = self._normalize_path(dest_path)
            source_normalized = self._normalize_path(project_config["canonical_path"])

            if not dest_normalized.startswith(source_normalized):
                reason = f"Cannot move protected project '{project_name}' outside its canonical path"
                return False, reason

        return True, None

    def require_protection_check(self, operation: str, path: str, dest_path: str | None = None):
        """
        Require protection check before operation
        Raises PathProtectionViolation if operation is not allowed
        """
        is_allowed, reason = self.validate_operation(operation, path, dest_path)

        if not is_allowed:
            raise PathProtectionViolation(
                f"PROTECTION VIOLATION: {reason}\n"
                f"Operation: {operation}\n"
                f"Path: {path}\n"
                f"Destination: {dest_path or 'N/A'}\n\n"
                f"This path is EXPLICITLY PROTECTED by user request.\n"
                f"Modification not allowed. Operation stopped."
            )

    def get_canonical_path(self, project_name: str) -> str | None:
        """Get canonical path for a project"""
        project_config = self.protected_projects.get(project_name)
        if project_config:
            return project_config["canonical_path"]
        return None

    def list_protected_projects(self) -> list[dict]:
        """List all protected projects"""
        projects = []
        for name, config in self.protected_projects.items():
            projects.append(
                {
                    "name": name,
                    "canonical_path": config["canonical_path"],
                    "protection_level": config["protection_level"],
                    "modification_allowed": config["modification_allowed"],
                    "tags": config.get("tags", []),
                }
            )
        return projects

    def generate_report(self) -> str:
        """Generate protection status report"""
        lines = ["=" * 80, "PROJECT PATH PROTECTION STATUS", "=" * 80, ""]

        for project in self.list_protected_projects():
            lines.extend(
                [
                    f"Project: {project['name']}",
                    f"  Path: {project['canonical_path']}",
                    f"  Protection: {project['protection_level']}",
                    f"  Modification Allowed: {project['modification_allowed']}",
                    f"  Tags: {', '.join(project['tags'])}",
                    "",
                ]
            )

        lines.extend(
            [
                "-" * 80,
                "ENFORCEMENT RULES",
                "-" * 80,
                f"No Path Changes: {self.enforcement_rules['no_path_changes']}",
                f"No Moves: {self.enforcement_rules['no_moves']}",
                f"No Renames: {self.enforcement_rules['no_renames']}",
                f"Violation Action: {self.enforcement_rules['violation_action']}",
                "",
                "=" * 80,
            ]
        )

        return "\n".join(lines)


def main():
    """CLI for path protection validation"""
    import argparse

    parser = argparse.ArgumentParser(description="Project Path Protection Validator")
    parser.add_argument("--config", default="config/project_path_protection.json", help="Path to protection config")
    parser.add_argument("--check", help="Check if path is protected")
    parser.add_argument("--validate", help="Validate operation on path")
    parser.add_argument("--operation", help="Operation type (move, rename, etc)")
    parser.add_argument("--dest", help="Destination path for move operations")
    parser.add_argument("--report", action="store_true", help="Generate protection report")
    parser.add_argument("--list", action="store_true", help="List protected projects")

    args = parser.parse_args()

    protector = ProjectPathProtector(args.config)

    if args.report:
        print(protector.generate_report())

    if args.list:
        print("\nPROTECTED PROJECTS:\n")
        for project in protector.list_protected_projects():
            print(f"  {project['name']}: {project['canonical_path']}")

    if args.check:
        is_protected, project_name = protector.is_protected_path(args.check)
        if is_protected:
            print("✗ PATH IS PROTECTED")
            print(f"  Project: {project_name}")
            print(f"  Path: {args.check}")
        else:
            print(f"✓ Path is not protected: {args.check}")

    if args.validate and args.operation:
        try:
            protector.require_protection_check(args.operation, args.validate, args.dest)
            print(f"✓ Operation '{args.operation}' is ALLOWED on path: {args.validate}")
        except PathProtectionViolation as e:
            print(f"\n{e}\n")
            exit(1)


if __name__ == "__main__":
    main()
