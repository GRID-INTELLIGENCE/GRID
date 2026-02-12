"""Main entry point for Coinbase."""

import argparse


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Coinbase crypto project")
    parser.add_argument(
        "--crypto",
        action="store_true",
        help="Enable crypto scope",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    if args.crypto:
        print("Crypto scope enabled")
    if args.verbose:
        print("Verbose mode enabled")
    print("Coinbase running")


if __name__ == "__main__":
    main()
