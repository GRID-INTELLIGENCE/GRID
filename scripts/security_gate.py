#!/usr/bin/env python3
"""
Security Gate Script for GRID CI/CD Pipeline

Transforms bandit-report.json from diagnostic tool into a blocking gate.
Enforces security thresholds before allowing pipeline to proceed.
"""

import argparse
import json
import sys
from typing import Any


def load_security_report(report_path: str) -> dict[str, Any]:
    """Load and validate the bandit security report."""
    try:
        with open(report_path) as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"❌ SECURITY GATE ERROR: Security report not found at {report_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ SECURITY GATE ERROR: Invalid JSON in security report: {e}")
        sys.exit(1)


def extract_severity_counts(report_data: dict[str, Any]) -> dict[str, int]:
    """Extract severity counts from bandit report."""
    totals = report_data.get("metrics", {}).get("_totals", {}).get("SEVERITY", {})

    return {
        "HIGH": totals.get("HIGH", 0),
        "MEDIUM": totals.get("MEDIUM", 0),
        "LOW": totals.get("LOW", 0),
        "UNDEFINED": totals.get("UNDEFINED", 0),
    }


def check_security_thresholds(severity_counts: dict[str, int], max_high: int = 0, max_medium: int = 5) -> bool:
    """
    Check if security issues exceed acceptable thresholds.

    Args:
        severity_counts: Dictionary with HIGH, MEDIUM, LOW counts
        max_high: Maximum allowed HIGH severity issues (default: 0)
        max_medium: Maximum allowed MEDIUM severity issues (default: 5)

    Returns:
        True if within thresholds, False otherwise
    """
    high_count = severity_counts["HIGH"]
    medium_count = severity_counts["MEDIUM"]

    if high_count > max_high:
        print(f"❌ SECURITY GATE FAILED: Found {high_count} HIGH severity issues (max allowed: {max_high})")
        return False

    if medium_count > max_medium:
        print(f"⚠️  SECURITY WARNING: Found {medium_count} MEDIUM severity issues (max allowed: {max_medium})")
        # Medium issues don't fail the gate, but provide warning

    return True


def print_security_summary(severity_counts: dict[str, int], report_path: str):
    """Print a formatted security summary."""
    print("\n" + "=" * 60)
    print("🛡️  GRID SECURITY GATE SUMMARY")
    print("=" * 60)
    print(f"Report Source: {report_path}")
    print(f"HIGH Severity:    {severity_counts['HIGH']:3d} {'❌' if severity_counts['HIGH'] > 0 else '✅'}")
    print(f"MEDIUM Severity:  {severity_counts['MEDIUM']:3d} {'⚠️'  if severity_counts['MEDIUM'] > 5 else '✅'}")
    print(f"LOW Severity:     {severity_counts['LOW']:3d} {'ℹ️'  if severity_counts['LOW'] > 0 else '✅'}")
    print("=" * 60)


def generate_github_summary(severity_counts: dict[str, int]) -> str:
    """Generate GitHub Actions step summary markdown."""
    summary = []
    summary.append("## 🛡️ Security Scan Results")
    summary.append("")
    summary.append("| Severity | Count | Status |")
    summary.append("|----------|-------|--------|")

    status_map = {
        "HIGH": "❌ FAILED" if severity_counts["HIGH"] > 0 else "✅ PASSED",
        "MEDIUM": "⚠️ WARNING" if severity_counts["MEDIUM"] > 5 else "✅ PASSED",
        "LOW": "ℹ️ INFO" if severity_counts["LOW"] > 0 else "✅ PASSED",
    }

    for severity in ["HIGH", "MEDIUM", "LOW"]:
        count = severity_counts[severity]
        status = status_map[severity]
        summary.append(f"| {severity} | {count} | {status} |")

    summary.append("")
    if severity_counts["HIGH"] > 0:
        summary.append("### 🚨 Action Required")
        summary.append("HIGH severity security issues must be resolved before merge.")
        summary.append("Run `bandit -r src/` locally to see detailed findings.")

    return "\n".join(summary)


def main():
    """Main security gate execution."""
    parser = argparse.ArgumentParser(description="GRID Security Gate Checker")
    parser.add_argument("report_path", help="Path to bandit-report.json")
    parser.add_argument("--max-high", type=int, default=0, help="Max allowed HIGH severity issues")
    parser.add_argument("--max-medium", type=int, default=5, help="Max allowed MEDIUM severity issues")
    parser.add_argument("--summary-file", help="Write GitHub summary to file")

    args = parser.parse_args()

    # Load and analyze security report
    report_data = load_security_report(args.report_path)
    severity_counts = extract_severity_counts(report_data)

    # Print summary to console
    print_security_summary(severity_counts, args.report_path)

    # Generate GitHub summary if requested
    if args.summary_file:
        with open(args.summary_file, "w") as f:
            f.write(generate_github_summary(severity_counts))
        print(f"\n📝 GitHub summary written to: {args.summary_file}")

    # Check security thresholds
    if check_security_thresholds(severity_counts, args.max_high, args.max_medium):
        print("✅ SECURITY GATE PASSED: Pipeline may proceed")
        sys.exit(0)
    else:
        print("🚫 SECURITY GATE FAILED: Pipeline blocked")
        sys.exit(1)


if __name__ == "__main__":
    main()
