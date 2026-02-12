"""
Environment Configuration Setup and Validation
==============================================
Production-ready environment variable management for Coinbase platform.

Usage:
    python -m coinbase.config.setup_env
    python -m coinbase.config.setup_env --validate
    python -m coinbase.config.setup_env --production
"""

import argparse
import os
import sys
from pathlib import Path


class EnvValidator:
    """Validates environment configuration for production deployment."""

    REQUIRED_VARS = {
        "production": [
            "DATABRICKS_HOST",
            "DATABRICKS_TOKEN",
            "DATABRICKS_HTTP_PATH",
            "GRID_ENCRYPTION_KEY",
            "JWT_SECRET_KEY",
        ],
        "staging": [
            "DATABRICKS_HOST",
            "DATABRICKS_TOKEN",
            "DATABRICKS_HTTP_PATH",
            "GRID_ENCRYPTION_KEY",
        ],
        "development": [
            "DATABRICKS_HOST",
            "DATABRICKS_TOKEN",
            "DATABRICKS_HTTP_PATH",
        ],
    }

    OPTIONAL_VARS = [
        "DATABRICKS_CLUSTER_ID",
        "DATABRICKS_OFFLINE",
        "COINBASE_ENV",
        "COINBASE_PROJECT_ROOT",
        "LOG_LEVEL",
        "LOG_FILE_PATH",
        "RATE_LIMIT_ENABLED",
        "RATE_LIMIT_REQUESTS",
        "RATE_LIMIT_WINDOW_SECONDS",
        "ENABLE_PORTFOLIO_SYNC",
        "ENABLE_REAL_TIME_PRICES",
        "ENABLE_AI_RECOMMENDATIONS",
    ]

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self) -> tuple[bool, list[str], list[str]]:
        """
        Validate environment configuration.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Check required variables
        required = self.REQUIRED_VARS.get(self.environment, [])
        for var in required:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required variable: {var}")
            elif self._is_placeholder(value):
                self.errors.append(f"Variable {var} contains placeholder value")
            else:
                self._validate_value(var, value)

        # Check optional variables
        for var in self.OPTIONAL_VARS:
            value = os.getenv(var)
            if value and self._is_placeholder(value):
                self.warnings.append(f"Variable {var} contains placeholder value")

        # Environment-specific validations
        if self.environment == "production":
            self._validate_production()

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _is_placeholder(self, value: str) -> bool:
        """Check if value is a placeholder."""
        value_lower = value.lower()

        # Standalone placeholder patterns
        placeholders = [
            "your_",
            "your-",
            "placeholder",
            "changeme",
            "admin",
            "xxx",
            "...",
        ]

        for ph in placeholders:
            if ph in value_lower:
                return True

        # Check for common password patterns as standalone values
        if value_lower in ["password", "secret", "admin"]:
            return True

        return False

    def _validate_value(self, var: str, value: str) -> None:
        """Validate specific variable values."""
        if var == "DATABRICKS_HOST":
            if not value.startswith("https://"):
                self.errors.append(f"{var} must start with https://")
            if ".cloud.databricks.com" not in value:
                self.warnings.append(f"{var} may not be a valid Databricks workspace URL")

        elif var == "DATABRICKS_TOKEN":
            if not value.startswith("dapi"):
                self.warnings.append(f"{var} should start with 'dapi'")
            if len(value) < 20:
                self.errors.append(f"{var} appears to be too short")

        elif var == "DATABRICKS_HTTP_PATH":
            if not value.startswith("/sql/"):
                self.errors.append(f"{var} must start with /sql/")

        elif var == "GRID_ENCRYPTION_KEY":
            try:
                import base64

                decoded = base64.b64decode(value)
                if len(decoded) != 32:
                    self.errors.append(f"{var} must be 32 bytes when decoded")
            except Exception:
                self.errors.append(f"{var} must be valid base64")

        elif var == "JWT_SECRET_KEY":
            if len(value) < 32:
                self.errors.append(f"{var} must be at least 32 characters")

    def _validate_production(self) -> None:
        """Additional validations for production environment."""
        # Check that development settings are not used
        if os.getenv("DATABRICKS_OFFLINE", "").lower() == "true":
            self.errors.append("DATABRICKS_OFFLINE should not be true in production")

        if os.getenv("LOG_LEVEL", "").upper() == "DEBUG":
            self.warnings.append("LOG_LEVEL is set to DEBUG in production")

        # Check for strong security settings
        if os.getenv("RATE_LIMIT_ENABLED", "").lower() != "true":
            self.warnings.append("RATE_LIMIT_ENABLED should be true in production")


def setup_environment(env_file: str | None = None) -> None:
    """
    Setup environment by loading .env file.

    Args:
        env_file: Path to .env file (default: .env in project root)
    """
    env_path: Path
    if env_file is None:
        # Find project root
        current_dir = Path(__file__).parent
        while current_dir.name != "coinbase" and current_dir.parent != current_dir:
            current_dir = current_dir.parent
        env_path = current_dir.parent / ".env"
    else:
        env_path = Path(env_file)

    if not env_path.exists():
        print(f"❌ Environment file not found: {env_path}")
        print("\nTo setup environment:")
        print("1. Copy env.template to .env")
        print("2. Fill in your values")
        print("3. Run this script again")
        sys.exit(1)

    # Load environment variables
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"'")
                if key not in os.environ:
                    os.environ[key] = value

    print(f"✅ Loaded environment from: {env_path}")


def generate_env_template() -> str:
    """Generate a secure random encryption key."""
    import base64
    import secrets

    key = base64.b64encode(secrets.token_bytes(32)).decode()
    jwt_secret = secrets.token_urlsafe(32)

    template = f"""# ============================================================================
# COINBASE Production Environment Configuration
# ============================================================================

# Environment
COINBASE_ENV=production

# Databricks Configuration (REQUIRED)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi_your_token_here
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your_warehouse_id

# Security (Auto-generated - keep these secret!)
GRID_ENCRYPTION_KEY={key}
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Feature Flags
ENABLE_PORTFOLIO_SYNC=true
ENABLE_REAL_TIME_PRICES=true
ENABLE_AI_RECOMMENDATIONS=false

# Logging
LOG_LEVEL=INFO
"""
    return template


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Environment setup and validation")
    parser.add_argument("--validate", action="store_true", help="Validate current environment")
    parser.add_argument("--production", action="store_true", help="Validate for production")
    parser.add_argument("--generate", action="store_true", help="Generate secure .env template")
    parser.add_argument("--env-file", type=str, help="Path to .env file")

    args = parser.parse_args()

    if args.generate:
        print(generate_env_template())
        return 0

    # Setup environment
    setup_environment(args.env_file)

    # Determine environment
    environment = "production" if args.production else os.getenv("COINBASE_ENV", "development")

    if args.validate or args.production:
        print(f"\n🔍 Validating environment: {environment}")
        print("=" * 50)

        validator = EnvValidator(environment)
        is_valid, errors, warnings = validator.validate()

        if errors:
            print("\n❌ ERRORS:")
            for error in errors:
                print(f"  • {error}")

        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  • {warning}")

        if is_valid and not warnings:
            print("\n✅ Environment is valid!")
            return 0
        elif is_valid:
            print("\n✅ Environment is valid (with warnings)")
            return 0
        else:
            print("\n❌ Environment validation failed!")
            return 1
    else:
        # Show current configuration status
        print("\n📋 Current Environment Configuration")
        print("=" * 50)

        vars_to_show = [
            "COINBASE_ENV",
            "DATABRICKS_HOST",
            "DATABRICKS_HTTP_PATH",
            "LOG_LEVEL",
            "RATE_LIMIT_ENABLED",
        ]

        for var in vars_to_show:
            value = os.getenv(var, "NOT SET")
            if "TOKEN" in var or "KEY" in var or "SECRET" in var:
                value = "***REDACTED***" if value != "NOT SET" else value
            status = "✅" if value != "NOT SET" else "❌"
            print(f"{status} {var}={value}")

        print("\nRun with --validate to check configuration")
        print("Run with --production to validate for production")

    return 0


if __name__ == "__main__":
    sys.exit(main())
