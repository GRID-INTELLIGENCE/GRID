#!/usr/bin/env python3
"""
Audit Trail Verification CLI
Verifies the integrity of audit log files with tamper-evident hash chaining.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from audit_logger import AuditEvent, AuditLogger


def load_audit_events(file_path: str) -> list[AuditEvent]:
    """Load audit events from a JSON file.

    Args:
        file_path: Path to the audit log file

    Returns:
        List of AuditEvent instances
    """
    path = Path(file_path)
    if not path.exists():
        print(f"Error: Audit log file '{file_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    events = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        event = AuditEvent.from_dict(data)
                        events.append(event)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Skipping malformed JSON line: {e}", file=sys.stderr)
                        continue
    except Exception as e:
        print(f"Error reading audit log: {e}", file=sys.stderr)
        sys.exit(1)

    return events


def verify_audit_trail(file_path: str, verbose: bool = False) -> bool:
    """Verify the integrity of an audit trail.

    Args:
        file_path: Path to the audit log file
        verbose: Whether to print detailed verification steps

    Returns:
        True if verification passes, False otherwise
    """
    events = load_audit_events(file_path)

    if not events:
        print("Error: No valid events found in audit log", file=sys.stderr)
        return False

    if verbose:
        print(f"Loaded {len(events)} audit events")
        print("Starting chain integrity verification...")

    # Create a logger instance for verification
    logger = AuditLogger()

    # Verify chain integrity
    is_valid, errors = logger.verify_chain_integrity(events)

    if verbose:
        if is_valid:
            print("✅ Chain integrity verification PASSED")
        else:
            print("❌ Chain integrity verification FAILED")
            for error in errors:
                print(f"   {error}")

    return is_valid


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Verify GRID audit trail integrity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m vection.security.verify_audit_trail audit.log
  python -m vection.security.verify_audit_trail --verbose audit.log
        """,
    )
    parser.add_argument("file", help="Path to the audit log file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed verification information")

    args = parser.parse_args()

    # Verify the audit trail
    success = verify_audit_trail(args.file, args.verbose)

    if success:
        event_count = len(load_audit_events(args.file))
        print(f"OK - Chain integrity: {event_count:,} events verified")
        sys.exit(0)
    else:
        print("FAIL - Chain integrity verification failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
