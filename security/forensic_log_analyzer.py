#!/usr/bin/env python3
"""
Forensic Log Analyzer
Analyzes security logs to detect unauthorized access attempts and generate reports.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ForensicLogAnalyzer:
    """Analyzes security logs for forensic evidence."""

    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
        self.audit_log = logs_dir / "audit.log"
        self.network_log = logs_dir / "network_access.log"

    def parse_audit_log(self) -> list[dict[str, Any]]:
        """Parse audit.log for security events."""
        events = []
        if not self.audit_log.exists():
            return events

        with open(self.audit_log, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse audit log line: {e}")
        return events

    def parse_network_log(self) -> list[dict[str, Any]]:
        """Parse network_access.log for initialization and events."""
        events = []
        if not self.network_log.exists():
            return events

        with open(self.network_log, encoding="utf-8") as f:
            for line in f:
                # Parse log format: timestamp - logger - level - message
                parts = line.strip().split(" - ", 3)
                if len(parts) >= 4:
                    timestamp_str, logger, level, message = parts
                    try:
                        # Parse timestamp
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                        event = {
                            "timestamp": timestamp.isoformat(),
                            "logger": logger,
                            "level": level,
                            "message": message,
                        }
                        events.append(event)
                    except ValueError:
                        continue
        return events

    def analyze_events(self, audit_events: list[dict], network_events: list[dict]) -> dict[str, Any]:
        """Analyze events for security insights."""
        analysis = {
            "summary": {
                "total_audit_events": len(audit_events),
                "total_network_events": len(network_events),
                "time_range": self._get_time_range(audit_events + network_events),
            },
            "blocked_requests": [],
            "network_initializations": [],
            "errors_warnings": [],
            "anomalies": [],
        }

        # Analyze audit events
        for event in audit_events:
            if event.get("event_type") == "REQUEST_BLOCKED":
                analysis["blocked_requests"].append(
                    {
                        "timestamp": event["timestamp"],
                        "url": event["details"].get("url"),
                        "method": event["details"].get("method"),
                        "reason": event["details"].get("reason"),
                        "caller": event["details"].get("caller"),
                    }
                )

        # Analyze network events
        for event in network_events:
            message = event["message"]
            if "Network Access Control initialized" in message:
                analysis["network_initializations"].append({"timestamp": event["timestamp"], "message": message})
            elif event["level"] in ["ERROR", "WARNING"]:
                analysis["errors_warnings"].append(event)

        # Detect anomalies
        if len(analysis["blocked_requests"]) > 0:
            analysis["anomalies"].append(f"Detected {len(analysis['blocked_requests'])} blocked network requests")

        if not analysis["network_initializations"]:
            analysis["anomalies"].append("No network access control initialization found")

        return analysis

    def _get_time_range(self, events: list[dict]) -> dict[str, str]:
        """Get time range of events."""
        if not events:
            return {"start": "", "end": ""}

        timestamps = [datetime.fromisoformat(e["timestamp"]) for e in events if "timestamp" in e]
        if not timestamps:
            return {"start": "", "end": ""}

        return {"start": min(timestamps).isoformat(), "end": max(timestamps).isoformat()}

    def generate_report(self, analysis: dict[str, Any]) -> str:
        """Generate human-readable report."""
        report = []
        report.append("# Forensic Security Log Analysis Report")
        report.append(f"**Generated:** {datetime.now().isoformat()}")
        report.append("")

        # Summary
        summary = analysis["summary"]
        report.append("## Summary")
        report.append(f"- Total audit events: {summary['total_audit_events']}")
        report.append(f"- Total network events: {summary['total_network_events']}")
        if summary["time_range"]["start"]:
            report.append(f"- Time range: {summary['time_range']['start']} to {summary['time_range']['end']}")
        report.append("")

        # Blocked requests
        blocked = analysis["blocked_requests"]
        if blocked:
            report.append("## Blocked Requests")
            for req in blocked:
                report.append(f"- **{req['timestamp']}**: {req['method']} {req['url']} (Reason: {req['reason']})")
            report.append("")
        else:
            report.append("## Blocked Requests")
            report.append("No blocked requests detected.")
            report.append("")

        # Network initializations
        inits = analysis["network_initializations"]
        if inits:
            report.append("## Network Access Control")
            for init in inits:
                report.append(f"- **{init['timestamp']}**: {init['message']}")
            report.append("")
        else:
            report.append("## Network Access Control")
            report.append("No initialization events found.")
            report.append("")

        # Errors and warnings
        errors = analysis["errors_warnings"]
        if errors:
            report.append("## Errors and Warnings")
            for err in errors:
                report.append(f"- **{err['level']}** {err['timestamp']}: {err['message']}")
            report.append("")

        # Anomalies
        anomalies = analysis["anomalies"]
        if anomalies:
            report.append("## Anomalies Detected")
            for anomaly in anomalies:
                report.append(f"- {anomaly}")
            report.append("")

        # Assessment
        report.append("## Security Assessment")
        if blocked:
            report.append(
                "✅ **Hardening Effective**: Unauthorized network access attempts are being blocked and logged."
            )
        else:
            report.append("ℹ️ **No Unauthorized Access Detected**: No blocked requests in the analyzed logs.")

        if inits:
            report.append("✅ **Network Control Active**: Access control is initialized and enforcing policies.")
        else:
            report.append("⚠️ **Network Control Status Unknown**: No initialization logs found.")

        return "\n".join(report)


def main():
    """Main function."""
    logs_dir = Path(__file__).parent / "logs"
    if not logs_dir.exists():
        print(f"Logs directory not found: {logs_dir}")
        return

    analyzer = ForensicLogAnalyzer(logs_dir)

    print("Analyzing logs...")
    audit_events = analyzer.parse_audit_log()
    network_events = analyzer.parse_network_log()

    analysis = analyzer.analyze_events(audit_events, network_events)
    report = analyzer.generate_report(analysis)

    # Save report
    report_file = logs_dir / f"forensic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report saved to: {report_file}")
    print("\n" + "=" * 50)
    print(report)


if __name__ == "__main__":
    main()
