#!/usr/bin/env python3
"""
GRID Secrets CLI - Easy command-line interface for secrets management.

Usage:
    python -m grid.secrets set MY_KEY "my-value"
    python -m grid.secrets get MY_KEY
    python -m grid.secrets list
    python -m grid.secrets delete MY_KEY
"""

import argparse
import sys
from pathlib import Path

# Add src/ to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from grid.security import get_local_secrets_manager

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

CHECK_MARK = "[OK]"
ERROR_MARK = "[FAIL]"


def print_success(text: str) -> None:
    print(f"[OK] {text}")


def print_error(text: str) -> None:
    print(f"[FAIL] {text}")


def print_info(text: str) -> None:
    print(f"[INFO] {text}")


def main():
    parser = argparse.ArgumentParser(
        description="GRID Secrets CLI - Manage local encrypted secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m grid.secrets set API_KEY "my-secret"
  python -m grid.secrets get API_KEY
  python -m grid.secrets list
  python -m grid.secrets delete API_KEY
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Set command
    set_parser = subparsers.add_parser("set", help="Set a secret")
    set_parser.add_argument("key", help="Secret key name")
    set_parser.add_argument("value", help="Secret value")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get a secret")
    get_parser.add_argument("key", help="Secret key name")

    # List command
    subparsers.add_parser("list", help="List all secrets")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a secret")
    delete_parser.add_argument("key", help="Secret key name")

    # Optional arguments
    parser.add_argument("--env", help="Environment (development, staging, production)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Get secrets manager
    manager = get_local_secrets_manager(environment=args.env)

    # Execute command
    if args.command == "set":
        if manager.set(args.key, args.value):
            print_success(f"Secret set: {args.key}")
        else:
            print_error(f"Failed to set secret: {args.key}")
            sys.exit(1)

    elif args.command == "get":
        value = manager.get(args.key)
        if value:
            print(value)
        else:
            print_error(f"Secret not found: {args.key}")
            sys.exit(1)

    elif args.command == "list":
        keys = manager.list()
        if keys:
            for key in keys:
                print(key)
        else:
            print_info("No secrets found")

    elif args.command == "delete":
        if manager.delete(args.key):
            print_success(f"Secret deleted: {args.key}")
        else:
            print_error(f"Failed to delete secret: {args.key}")
            sys.exit(1)


if __name__ == "__main__":
    main()
