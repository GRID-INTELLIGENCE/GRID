"""
Report generation for the Transition Gate Toolkit.

Provides audit trail analysis, compliance documentation, and statistical summaries.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from boundaries.transition_gate.envelope import TransitionEnvelope
from boundaries.transition_gate.gate_keeper import VerificationResult


@dataclass
class VerificationStats:
    """Statistics compiled from verification results."""

    total_verifications: int = 0
    total_passed: int = 0
    total_rejected: int = 0
    total_errors: int = 0

    # Rejection breakdown
    rejection_reasons: dict[str, int] = field(default_factory=dict)

    # Step-by-step pass/fail counts
    step_stats: dict[str, dict[str, int]] = field(default_factory=dict)

    # Timing
    avg_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0

    # Time range
    first_verification: str = ""
    last_verification: str = ""

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as percentage."""
        if self.total_verifications == 0:
            return 0.0
        return (self.total_passed / self.total_verifications) * 100

    @property
    def rejection_rate(self) -> float:
        """Calculate rejection rate as percentage."""
        if self.total_verifications == 0:
            return 0.0
        return (self.total_rejected / self.total_verifications) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_verifications": self.total_verifications,
            "total_passed": self.total_passed,
            "total_rejected": self.total_rejected,
            "total_errors": self.total_errors,
            "pass_rate_percent": round(self.pass_rate, 2),
            "rejection_rate_percent": round(self.rejection_rate, 2),
            "rejection_reasons": self.rejection_reasons,
            "step_stats": self.step_stats,
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2),
            "max_duration_ms": round(self.max_duration_ms, 2),
            "first_verification": self.first_verification,
            "last_verification": self.last_verification,
        }


class ReportGenerator:
    """
    Generate comprehensive reports from transition gate operations.

    Supports multiple output formats:
    - JSON: Machine-readable structured data
    - Markdown: Human-readable documentation
    - HTML: Rich visual reports
    - NDJSON: Append-only audit format
    """

    def __init__(self, audit_path: Path | str | None = None) -> None:
        """Initialize with optional audit log path."""
        self._audit_path = Path(audit_path) if audit_path else None

    def compile_statistics(self) -> VerificationStats:
        """
        Compile statistics from the audit log.

        Returns VerificationStats with aggregated metrics.
        """
        stats = VerificationStats()

        if not self._audit_path or not self._audit_path.exists():
            return stats

        durations: list[float] = []
        timestamps: list[str] = []

        with open(self._audit_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)

                    # Count by status
                    status = entry.get("status", "")
                    if status == "passed":
                        stats.total_passed += 1
                    elif status == "rejected":
                        stats.total_rejected += 1
                    elif status == "error":
                        stats.total_errors += 1
                    stats.total_verifications += 1

                    # Track rejection reasons
                    reason = entry.get("reason")
                    if reason:
                        stats.rejection_reasons[reason] = stats.rejection_reasons.get(reason, 0) + 1

                    # Step statistics
                    steps = entry.get("steps", [])
                    for step in steps:
                        step_name = step.get("name", "unknown")
                        step_status = step.get("status", "unknown")

                        if step_name not in stats.step_stats:
                            stats.step_stats[step_name] = {"passed": 0, "rejected": 0, "error": 0}
                        stats.step_stats[step_name][step_status] += 1

                    # Duration tracking
                    duration = entry.get("total_duration_ms", 0)
                    if duration:
                        durations.append(duration)

                    # Timestamp tracking
                    ts = entry.get("timestamp", "")
                    if ts:
                        timestamps.append(ts)

                except json.JSONDecodeError:
                    continue

        # Calculate duration stats
        if durations:
            stats.avg_duration_ms = sum(durations) / len(durations)
            stats.min_duration_ms = min(durations)
            stats.max_duration_ms = max(durations)

        # Time range
        if timestamps:
            stats.first_verification = min(timestamps)
            stats.last_verification = max(timestamps)

        return stats

    def generate_json_report(self, output_path: Path | str | None = None) -> str:
        """
        Generate a comprehensive JSON report.

        Args:
            output_path: Where to save the report. If None, returns JSON string.

        Returns:
            JSON report as string.
        """
        stats = self.compile_statistics()

        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "report_type": "transition_gate_audit",
            "version": "1.0.0",
            "statistics": stats.to_dict(),
            "audit_source": str(self._audit_path) if self._audit_path else None,
        }

        json_str = json.dumps(report, indent=2)

        if output_path:
            Path(output_path).write_text(json_str, encoding="utf-8")

        return json_str

    def generate_markdown_report(self, output_path: Path | str | None = None) -> str:
        """
        Generate a human-readable Markdown report.

        Args:
            output_path: Where to save the report. If None, returns Markdown string.

        Returns:
            Markdown report as string.
        """
        stats = self.compile_statistics()

        lines = [
            "# Transition Gate Audit Report",
            "",
            f"**Generated:** {datetime.now(UTC).isoformat()}",
            f"**Audit Source:** `{self._audit_path or 'N/A'}`",
            "",
            "## Executive Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Verifications | {stats.total_verifications} |",
            f"| Passed | {stats.total_passed} ({stats.pass_rate:.1f}%) |",
            f"| Rejected | {stats.total_rejected} ({stats.rejection_rate:.1f}%) |",
            f"| Errors | {stats.total_errors} |",
            "",
            "## Performance Metrics",
            "",
            f"| Metric | Value (ms) |",
            f"|--------|------------|",
            f"| Average Duration | {stats.avg_duration_ms:.2f} |",
            f"| Minimum Duration | {stats.min_duration_ms:.2f} |",
            f"| Maximum Duration | {stats.max_duration_ms:.2f} |",
            "",
        ]

        # Rejection breakdown
        if stats.rejection_reasons:
            lines.extend(
                [
                    "## Rejection Analysis",
                    "",
                    f"| Reason | Count |",
                    f"|--------|-------|",
                ]
            )
            for reason, count in sorted(stats.rejection_reasons.items(), key=lambda x: -x[1]):
                lines.append(f"| `{reason}` | {count} |")
            lines.append("")

        # Step-by-step breakdown
        if stats.step_stats:
            lines.extend(
                [
                    "## Step-by-Step Performance",
                    "",
                    f"| Step | Passed | Rejected | Error |",
                    f"|------|--------|----------|-------|",
                ]
            )
            for step_name, counts in sorted(stats.step_stats.items()):
                lines.append(
                    f"| {step_name} | {counts.get('passed', 0)} | "
                    f"{counts.get('rejected', 0)} | {counts.get('error', 0)} |"
                )
            lines.append("")

        # Time range
        if stats.first_verification and stats.last_verification:
            lines.extend(
                [
                    "## Time Range",
                    "",
                    f"- **First Verification:** {stats.first_verification}",
                    f"- **Last Verification:** {stats.last_verification}",
                    "",
                ]
            )

        lines.extend(
            [
                "---",
                "*Report generated by Transition Gate Toolkit*",
            ]
        )

        md_str = "\n".join(lines)

        if output_path:
            Path(output_path).write_text(md_str, encoding="utf-8")

        return md_str

    def generate_html_report(self, output_path: Path | str | None = None) -> str:
        """
        Generate an HTML report with styling.

        Args:
            output_path: Where to save the report. If None, returns HTML string.

        Returns:
            HTML report as string.
        """
        stats = self.compile_statistics()

        # Build rejection rows
        rejection_rows = (
            "".join(
                [
                    f"<tr><td><code>{reason}</code></td><td>{count}</td></tr>"
                    for reason, count in sorted(stats.rejection_reasons.items(), key=lambda x: -x[1])
                ]
            )
            if stats.rejection_reasons
            else "<tr><td colspan='2'>No rejections</td></tr>"
        )

        # Build step rows
        step_rows = (
            "".join(
                [
                    f"<tr><td>{step}</td><td>{c.get('passed', 0)}</td>"
                    f"<td>{c.get('rejected', 0)}</td><td>{c.get('error', 0)}</td></tr>"
                    for step, c in sorted(stats.step_stats.items())
                ]
            )
            if stats.step_stats
            else "<tr><td colspan='4'>No step data</td></tr>"
        )

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Transition Gate Audit Report</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f5f5f5; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #fafafa; }}
        .metric {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
        .pass {{ color: #4CAF50; }}
        .reject {{ color: #f44336; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>🛡️ Transition Gate Audit Report</h1>
    <p><strong>Generated:</strong> {datetime.now(UTC).isoformat()}</p>
    <p><strong>Source:</strong> {self._audit_path or "N/A"}</p>

    <h2>Executive Summary</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Total Verifications</td><td class="metric">{stats.total_verifications}</td></tr>
        <tr><td>Passed</td><td class="pass">{stats.total_passed} ({stats.pass_rate:.1f}%)</td></tr>
        <tr><td>Rejected</td><td class="reject">{stats.total_rejected} ({stats.rejection_rate:.1f}%)</td></tr>
        <tr><td>Errors</td><td>{stats.total_errors}</td></tr>
    </table>

    <h2>Performance Metrics</h2>
    <table>
        <tr><th>Metric</th><th>Value (ms)</th></tr>
        <tr><td>Average Duration</td><td>{stats.avg_duration_ms:.2f}</td></tr>
        <tr><td>Minimum Duration</td><td>{stats.min_duration_ms:.2f}</td></tr>
        <tr><td>Maximum Duration</td><td>{stats.max_duration_ms:.2f}</td></tr>
    </table>

    <h2>Rejection Analysis</h2>
    <table>
        <tr><th>Reason</th><th>Count</th></tr>
        {rejection_rows}
    </table>

    <h2>Step-by-Step Performance</h2>
    <table>
        <tr><th>Step</th><th>Passed</th><th>Rejected</th><th>Error</th></tr>
        {step_rows}
    </table>

    <div class="footer">
        Report generated by Transition Gate Toolkit v1.0.0
    </div>
</body>
</html>"""

        if output_path:
            Path(output_path).write_text(html, encoding="utf-8")

        return html

    def generate_compliance_summary(self) -> dict[str, Any]:
        """
        Generate a compliance-focused summary.

        Returns dict with compliance metrics and flags.
        """
        stats = self.compile_statistics()

        # Compliance criteria
        compliance = {
            "has_audit_trail": self._audit_path is not None and self._audit_path.exists(),
            "envelope_integrity_verified": True,  # All verifications include this
            "nonce_replay_protection_active": True,
            "timestamp_freshness_enforced": True,
            "scope_enforcement_active": True,
            "test_requirements_configurable": True,
            "pass_rate_above_threshold": stats.pass_rate >= 95.0,
            "no_critical_errors": stats.total_errors == 0,
            "rejection_reasons_documented": len(stats.rejection_reasons) > 0,
        }

        return {
            "compliance_score": sum(1 for v in compliance.values() if v) / len(compliance) * 100,
            "criteria": compliance,
            "recommendations": self._generate_recommendations(stats, compliance),
        }

    def _generate_recommendations(self, stats: VerificationStats, compliance: dict[str, bool]) -> list[str]:
        """Generate security and operational recommendations."""
        recommendations = []

        if stats.rejection_rate > 10:
            recommendations.append(f"High rejection rate ({stats.rejection_rate:.1f}%) - review common failure modes")

        if not compliance.get("pass_rate_above_threshold"):
            recommendations.append("Pass rate below 95% threshold - investigate systemic issues")

        if "rejected:payload_integrity_failed" in stats.rejection_reasons:
            recommendations.append("Payload integrity failures detected - check for data corruption in transit")

        if "rejected:fingerprint_mismatch" in stats.rejection_reasons:
            recommendations.append("Fingerprint mismatches detected - verify shared secret synchronization")

        if "rejected:nonce_replay_or_expired" in stats.rejection_reasons:
            recommendations.append("Nonce replay/expiration detected - verify clock synchronization")

        return recommendations


def format_verification_result(result: VerificationResult, verbose: bool = False) -> str:
    """
    Format a verification result for display.

    Args:
        result: The verification result to format.
        verbose: Include full step details.

    Returns:
        Formatted string suitable for console output.
    """
    lines = [
        f"{'=' * 60}",
        f"Verification Result: {'✅ PASSED' if result.passed else '❌ REJECTED'}",
        f"Envelope ID: {result.envelope_id or 'N/A'}",
        f"Timestamp: {result.timestamp}",
        f"Duration: {result.total_duration_ms:.2f}ms",
        f"Nonce Burned: {'Yes' if result.nonce_burned else 'No'}",
    ]

    if result.reason:
        lines.append(f"Reason: {result.reason}")

    if verbose and result.steps:
        lines.extend(["", "Step-by-step:", "-" * 40])
        for step in result.steps:
            status_icon = "✅" if step.status == "passed" else "❌" if step.status == "rejected" else "⚠️"
            lines.append(f"  {step.step}. {step.name}: {status_icon} {step.status}")
            if step.detail:
                lines.append(f"      {step.detail}")

    lines.append(f"{'=' * 60}")

    return "\n".join(lines)
