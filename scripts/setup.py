#!/usr/bin/env python3
"""
GRID Simplified Setup Script

A single command to set up your local development environment.

Usage:
    python scripts/setup.py                    # Interactive mode
    python scripts/setup.py --quick            # Use defaults, minimal input
    python scripts/setup.py --env development  # Specific environment
    python scripts/setup.py --migrate          # Migrate from .env file

This script:
1. Creates local secrets manager with encrypted storage
2. Sets up environment configuration
3. Migrates existing .env secrets if present
4. Validates the setup
5. Provides next steps
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Use ASCII-safe characters for Windows compatibility
CHECK_MARK = "[OK]"
WARNING_MARK = "[WARN]"
ERROR_MARK = "[FAIL]"
INFO_MARK = "[INFO]"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{GREEN}{CHECK_MARK} {text}{RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{YELLOW}{WARNING_MARK} {text}{RESET}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{RED}{ERROR_MARK} {text}{RESET}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{BLUE}{INFO_MARK} {text}{RESET}")


def run_command(cmd: str, description: str = "") -> tuple:
    """Run a command securely and return result.

    Security: Uses shlex.split() instead of shell=True to prevent command injection.
    """
    import shlex
    import subprocess

    print_info(f"Running: {cmd}")
    # Security fix: Use shlex.split() instead of shell=True to prevent injection
    try:
        cmd_list = shlex.split(cmd)
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except ValueError as e:
        # Handle parsing errors gracefully
        print_error(f"Failed to parse command: {e}")
        return 1, "", str(e)


class GRIDSetup:
    """GRID Development Environment Setup."""

    def __init__(self, args: argparse.Namespace):
        """Initialize setup with parsed arguments."""
        self.args = args
        self.project_root = Path(__file__).resolve().parent.parent
        self.grid_home = Path.home() / ".grid"
        self.errors = []
        self.warnings = []

    def run(self) -> int:
        """Run the complete setup process."""
        print_header("GRID Development Environment Setup")

        # Step 1: Check prerequisites
        if not self._check_prerequisites():
            return 1

        # Step 2: Create directories
        self._create_directories()

        # Step 3: Initialize local secrets manager
        self._init_secrets_manager()

        # Step 4: Migrate existing secrets (if migrating)
        if self.args.migrate:
            self._migrate_from_env()

        # Step 5: Set default secrets
        self._set_default_secrets()

        # Step 6: Generate environment configuration
        self._generate_env_config()

        # Step 7: Validate setup
        self._validate_setup()

        # Step 8: Print summary
        self._print_summary()

        return 0 if not self.errors else 1

    def _check_prerequisites(self) -> bool:
        """Check that prerequisites are met."""
        print_header("Step 1: Checking Prerequisites")

        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 10):
            print_error(f"Python 3.10+ required. You have {python_version.major}.{python_version.minor}")
            return False
        print_success(f"Python {python_version.major}.{python_version.minor} detected")

        # Check we're in the project directory
        if not (self.project_root / "pyproject.toml").exists():
            print_error("Not in a GRID project directory (pyproject.toml not found)")
            return False
        print_success(f"Project root: {self.project_root}")

        # Check uv is installed (preferred)
        code, _, _ = run_command("uv --version", "Check uv")
        if code == 0:
            print_success("uv package manager detected")
        else:
            print_warning("uv not found. Using pip instead")

        return True

    def _create_directories(self) -> None:
        """Create necessary directories."""
        print_header("Step 2: Creating Directories")

        directories = [
            self.grid_home,
            self.grid_home / "secrets",
            self.grid_home / "cache",
            self.grid_home / "logs",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print_success(f"Created: {directory}")

        # Create .gitkeep to track directories
        for directory in directories:
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.write_text("# This file ensures the directory is tracked by git\n")

    def _init_secrets_manager(self) -> None:
        """Initialize of local secrets manager."""
        print_header("Step 3: Initializing Local Secrets Manager")

        try:
            # Add src/ to path for imports
            sys.path.insert(0, str(self.project_root / "src"))
            from grid.security.local_secrets_manager import LocalSecretsManager

            manager = LocalSecretsManager(
                storage_path=self.grid_home / "secrets" / "secrets.db", environment=self.args.env or "development"
            )

            print_success("Local secrets manager initialized")
            print_info(f"Secrets database: {self.grid_home / 'secrets' / 'secrets.db'}")
            print_info("Secrets are encrypted with AES-256-GCM")

            # Test: manager
            test_key = "__test_secret"
            test_value = "test_value_" + datetime.now().isoformat()
            manager.set(test_key, test_value)
            retrieved = manager.get(test_key)

            if retrieved == test_value:
                print_success("Secrets manager validation passed")
                manager.delete(test_key)  # Clean up test
            else:
                print_error("Secrets manager validation failed")
                self.errors.append("Secrets manager validation failed")

        except Exception as e:
            print_error(f"Failed to initialize secrets manager: {e}")
            self.errors.append(str(e))

    def _migrate_from_env(self) -> None:
        """Migrate secrets from existing .env file."""
        print_header("Step 4: Migrating from .env")

        env_file = self.project_root / ".env"
        if not env_file.exists():
            print_warning("No .env file found to migrate")
            return

        print_info(f"Migrating secrets from: {env_file}")

        try:
            sys.path.insert(0, str(self.project_root / "src"))
            from grid.security.local_secrets_manager import LocalSecretsManager

            manager = LocalSecretsManager(
                storage_path=self.grid_home / "secrets" / "secrets.db", environment=self.args.env or "development"
            )

            # Parse .env file
            secrets_migrated = 0
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Skip non-secret entries
                    if key in ["GRID_ENVIRONMENT", "MOTHERSHIP_ENVIRONMENT", "GRID_HOME"]:
                        continue

                    # Check if it's a secret-like entry
                    if any(
                        secret_indicator in key.upper()
                        for secret_indicator in ["API_KEY", "SECRET", "PASSWORD", "CREDENTIAL", "TOKEN"]
                    ):
                        manager.set(key, value)
                        secrets_migrated += 1
                        print_success(f"Migrated: {key}")

            print_success(f"Migrated {secrets_migrated} secrets from .env")

            # Backup and clean up .env
            backup_path = env_file.with_suffix(".env.backup")
            env_file.rename(backup_path)
            print_info(f"Backed up .env to: {backup_path}")
            print_info("You can delete the backup once you verify the migration")

        except Exception as e:
            print_error(f"Migration failed: {e}")
            self.errors.append(str(e))

    def _set_default_secrets(self) -> None:
        """Set default secrets for development."""
        print_header("Step 5: Setting Default Secrets")

        try:
            sys.path.insert(0, str(self.project_root / "src"))
            from grid.security.local_secrets_manager import LocalSecretsManager

            manager = LocalSecretsManager(
                storage_path=self.grid_home / "secrets" / "secrets.db", environment=self.args.env or "development"
            )

            # Set required secrets if not already set
            required_secrets = {
                "MOTHERSHIP_SECRET_KEY": self._generate_secret(64),
                "MISTRAL_API_KEY": "your-mistral-api-key-here",
                "GRID_API_KEY": self._generate_secret(32),
            }

            for key, value in required_secrets.items():
                if not manager.exists(key):
                    manager.set(key, value)
                    print_success(f"Set: {key}")
                else:
                    print_info(f"Already exists: {key}")

            print_success("Default secrets configured")
            print_warning("Update MISTRAL_API_KEY with your actual API key")

        except Exception as e:
            print_error(f"Failed to set default secrets: {e}")
            self.errors.append(str(e))

    def _generate_secret(self, length: int = 32) -> str:
        """Generate a secure random secret."""
        import secrets as secrets_module

        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        return "".join(secrets_module.choice(alphabet) for _ in range(length))

    def _generate_env_config(self) -> None:
        """Generate environment configuration."""
        print_header("Step 6: Generating Environment Configuration")

        try:
            # Create a local .env file with just the environment variable
            env_file = self.project_root / ".env"

            # Only create if it doesn't exist
            if not env_file.exists():
                env_content = f"""# GRID Environment Configuration
# Generated by scripts/setup.py on {datetime.now().isoformat()}

# Environment (development, staging, production)
GRID_ENVIRONMENT={self.args.env or "development"}

# Local secrets manager - no configuration needed, uses ~/.grid/
# Secrets are stored encrypted in ~/.grid/secrets/secrets.db

# For production, you can switch to GCP Secret Manager:
# GRID_SECRETS_PROVIDER=gcp
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
"""
                env_file.write_text(env_content)
                print_success(f"Created: {env_file}")
            else:
                print_info(f".env already exists: {env_file}")

        except Exception as e:
            print_error(f"Failed to generate env config: {e}")
            self.errors.append(str(e))

    def _validate_setup(self) -> None:
        """Validate the setup."""
        print_header("Step 7: Validating Setup")

        validations = []

        # Check secrets database exists
        secrets_db = self.grid_home / "secrets" / "secrets.db"
        if secrets_db.exists():
            validations.append(("Secrets database exists", True))
        else:
            validations.append(("Secrets database exists", False))

        # Check we can read a secret
        try:
            sys.path.insert(0, str(self.project_root / "src"))
            from grid.security.local_secrets_manager import LocalSecretsManager

            manager = LocalSecretsManager(
                storage_path=self.grid_home / "secrets" / "secrets.db", environment=self.args.env or "development"
            )

            test_key = "__validation_test"
            test_value = "test_" + datetime.now().isoformat()
            manager.set(test_key, test_value)
            retrieved = manager.get(test_key)
            manager.delete(test_key)

            if retrieved == test_value:
                validations.append(("Secrets read/write works", True))
            else:
                validations.append(("Secrets read/write works", False))
        except Exception as e:
            validations.append((f"Secrets validation: {e}", False))

        # Check .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            validations.append((".env file exists", True))
        else:
            validations.append((".env file exists", False))

        # Print validation results
        for desc, passed in validations:
            if passed:
                print_success(desc)
            else:
                print_error(desc)
                self.errors.append(f"Validation failed: {desc}")

        return all(passed for _, passed in validations)

    def _print_summary(self) -> None:
        """Print setup summary."""
        print_header("Setup Complete!")

        print(
            f"""
{BOLD}Summary:{RESET}
  • Environment: {self.args.env or "development"}
  • Secrets Location: {self.grid_home / "secrets"}
  • Configuration: {self.project_root / ".env"}

{BOLD}Next Steps:{RESET}
  1. Update your API keys:
     python -c "from grid.security.local_secrets_manager import get_secret; get_secret('MISTRAL_API_KEY')"

  2. Start developing:
     python -m src.grid

  3. Add new secrets:
     python -m grid.security.local_secrets_manager set MY_KEY my_value

  4. List secrets:
     python -m grid.security.local_secrets_manager list

{BOLD}For Production:{RESET}
  • Run: python scripts/setup.py --env production
  • Configure GCP Secret Manager
  • Migrate secrets to cloud

{BOLD}Documentation:{RESET}
  • See: docs/SECURITY.md
  • See: docs/LOCAL_DEVELOPMENT.md
"""
        )

        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for warning in self.warnings:
                print(f"  • {warning}")

        if self.errors:
            print(f"\n{RED}Errors:{RESET}")
            for error in self.errors:
                print(f"  • {error}")
            print("\nPlease resolve the errors above before proceeding.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GRID Development Environment Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup.py                    # Interactive mode
  python scripts/setup.py --quick            # Quick setup with defaults
  python scripts/setup.py --env development  # Development environment
  python scripts/setup.py --env production   # Production environment
  python scripts/setup.py --migrate          # Migrate from .env file
        """,
    )

    parser.add_argument(
        "--env",
        "-e",
        choices=["development", "staging", "production"],
        help="Environment to configure (default: development)",
    )
    parser.add_argument("--quick", "-q", action="store_true", help="Quick setup with minimal output")
    parser.add_argument("--migrate", "-m", action="store_true", help="Migrate secrets from existing .env file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Run setup
    setup = GRIDSetup(args)
    sys.exit(setup.run())


if __name__ == "__main__":
    main()
