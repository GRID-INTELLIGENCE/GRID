#!/usr/bin/env python
"""
GRID Dev Programs Manager

Manages program-specific configurations, workflows, and skills.
"""

import argparse
import json
from pathlib import Path
from typing import Any

PROGRAMS_DIR = Path(".cursor/devprograms/programs")
WORKFLOWS_DIR = Path(".cursor/devprograms/workflows")
SKILLS_DIR = Path(".cursor/devprograms/skills")


class DevProgramsManager:
    """Manages dev program configurations"""

    def __init__(self):
        self.current_program = "default"
        self.configs = {}

    def list_programs(self) -> list[dict[str, Any]]:
        """List all available dev programs"""
        programs: list[dict[str, Any]] = []
        if PROGRAMS_DIR.exists():
            for config_file in PROGRAMS_DIR.glob("*.yml"):
                config = self._load_config(config_file)
                if config:
                    programs.append(
                        {
                            "name": config_file.stem,
                            "program": config.get("program", config_file.stem),
                            "version": config.get("version", "1.0"),
                            "model": config.get("model", "ministral"),
                            "timeout": config.get("timeout_sec", 30),
                        }
                    )

        # Add default program
        programs.append(
            {
                "name": "default",
                "program": "default",
                "version": "1.0",
                "model": "ministral",
                "timeout": 45,
                "description": "Default configuration",
            }
        )

        return programs

    def get_program_config(self, program: str) -> dict[str, Any]:
        """Get configuration for a specific program"""
        if program == "default":
            return self._get_default_config()

        config_file = PROGRAMS_DIR / f"{program}.yml"
        if not config_file.exists():
            return self._get_default_config()

        config = self._load_config(config_file)
        if not config:
            return self._get_default_config()

        # Merge with default config
        default = self._get_default_config()
        default.update(config)
        return default

    def set_program(self, program: str) -> bool:
        """Set active dev program"""
        if self.current_program == program:
            return True

        config = self.get_program_config(program)
        if config:
            self.current_program = program
            return True
        return False

    def get_current_config(self) -> dict[str, Any]:
        """Get current program configuration"""
        return self.get_program_config(self.current_program)

    from typing import Optional

    def list_workflows(self, program: str | None = None) -> list[dict[str, Any]]:
        """List workflows for a program"""
        if program is None:
            program = self.current_program

        workflows_dir = WORKFLOWS_DIR / program
        if not workflows_dir.exists():
            return []

        workflows: list[dict[str, Any]] = []
        for workflow_file in workflows_dir.glob("*.json"):
            workflow = self._load_json(workflow_file)
            if workflow:
                workflows.append(workflow)

        return workflows

    def list_skills(self, program: str | None = None) -> list[str]:
        """List skills available for a program"""
        if program is None:
            program = self.current_program

        skills_dir = SKILLS_DIR / program
        skills: list[str] = []

        # Add global skills
        global_skills = SKILLS_DIR / "global"
        if global_skills.exists():
            for skill_file in global_skills.glob("*.py"):
                skills.append(skill_file.stem)

        # Add program-specific skills
        if skills_dir.exists():
            for skill_file in skills_dir.glob("*.py"):
                skills.append(skill_file.stem)

        return skills

    def validate_program(self, program: str) -> bool:
        """Validate program configuration"""
        config = self.get_program_config(program)

        # Required fields
        required_fields = ["program", "version", "model"]
        for field in required_fields:
            if field not in config:
                return False

        # Validate model exists
        model = config.get("model")
        if not self._model_available(str(model)):
            return False

        return True

    def _load_config(self, config_path: Path) -> dict[str, Any]:
        """Load YAML configuration"""
        import yaml

        if not config_path.exists():
            return {}

        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except Exception:
            return {}

    def _load_json(self, json_path: Path) -> dict[str, Any]:
        """Load JSON file"""
        if not json_path.exists():
            return {}

        try:
            with open(json_path) as f:
                return json.load(f)
        except Exception:
            return {}

    def _get_default_config(self) -> dict[str, Any]:
        """Get default program configuration"""
        return {
            "program": "default",
            "version": "1.0",
            "model": "ministral",
            "timeout_sec": 45,
            "strict_mode": True,
            "max_tokens": 4096,
            "coverage_threshold": 80,
            "allowed_tools": ["filesystem", "git", "python-repl", "ollama", "bash"],
            "blocked_tools": ["external_api", "network"],
        }

    def _model_available(self, model: str) -> bool:
        """Check if model is available"""
        if not model or model == "None":
            return True
        import subprocess

        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            return model in result.stdout
        except Exception:
            return model == "ministral"


def main():
    parser = argparse.ArgumentParser(description="GRID Dev Programs Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List programs
    subparsers.add_parser("list", help="List all dev programs")

    # Set program
    set_cmd = subparsers.add_parser("set", help="Set active dev program")
    set_cmd.add_argument("program", help="Program name")

    # Get config
    get_cmd = subparsers.add_parser("get", help="Get configuration")
    get_cmd.add_argument("--program", help="Program name (default: current)")

    # Validate
    validate_cmd = subparsers.add_parser("validate", help="Validate program")
    validate_cmd.add_argument("program", help="Program name")

    args = parser.parse_args()

    manager = DevProgramsManager()

    if args.command == "list":
        programs = manager.list_programs()
        print("\nAvailable Dev Programs:")
        print("=" * 60)
        for prog in programs:
            print(f"\n  {prog['name']}")
            print(f"    Program: {prog.get('program', 'N/A')}")
            print(f"    Version: {prog.get('version', 'N/A')}")
            print(f"    Model: {prog.get('model', 'N/A')}")
            print(f"    Timeout: {prog.get('timeout', 30)}s")
            print(f"    Description: {prog.get('description', 'N/A')}")
        print("\n" + "=" * 60)
        print(f"Current program: {manager.current_program}")

    elif args.command == "set":
        if manager.set_program(args.program):
            print(f"✓ Set active program to: {args.program}")
            print(f"  Config: {manager.get_current_config()}")
        else:
            print(f"✗ Failed to set program: {args.program}")

    elif args.command == "get":
        program = args.program or manager.current_program
        config = manager.get_program_config(program)
        print(f"\nConfiguration for {program}:")
        print("=" * 60)
        for key, value in config.items():
            print(f"  {key}: {value}")
        print("=" * 60)

    elif args.command == "validate":
        program = args.program
        if manager.validate_program(program):
            print(f"[OK] Program '{program}' configuration is valid")
        else:
            print(f"[ERROR] Program '{program}' configuration is invalid")

    elif args.command is None:
        parser.print_help()


if __name__ == "__main__":
    main()
