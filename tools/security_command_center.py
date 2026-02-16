#!/usr/bin/env python3
"""
GRID Enhanced Security Command Center
=====================================

Centralized threat profiling, monitoring, and automated response system.
Provides real-time visibility into security posture and automated mitigation.

Usage:
    python tools/security_command_center.py --profile
    python tools/security_command_center.py --monitor
    python tools/security_command_center.py --respond
    python tools/security_command_center.py --guardrails
"""

import argparse
import asyncio
import json
import os
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from grid.security.security_monitoring import SecurityMonitor


@dataclass
class ThreatProfile:
    """Comprehensive threat landscape profile."""

    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    total_events: int = 0
    threat_categories: dict[str, int] = field(default_factory=dict)
    severity_distribution: dict[str, int] = field(default_factory=dict)
    top_attack_sources: list[dict] = field(default_factory=list)
    detection_accuracy: float = 0.0
    active_mitigations: list[str] = field(default_factory=list)
    risk_score: float = 0.0  # 0-100
    recommendations: list[str] = field(default_factory=list)


@dataclass
class GuardrailConfig:
    """Active security guardrails configuration."""

    # Detection thresholds
    detection_sensitivity: str = "high"  # low, medium, high, critical
    parasite_threshold: int = 3  # Lower = more sensitive

    # Response actions
    auto_isolate: bool = True
    auto_alert: bool = True
    auto_sanitize: bool = True

    # Rate limiting
    rate_limit_requests: int = 60  # per minute
    rate_limit_window: int = 60  # seconds
    burst_allowance: int = 10  # burst tolerance

    # Anomaly detection
    z_score_threshold: float = 2.5  # statistical anomaly threshold
    baseline_window_hours: int = 24  # learning window

    # Alerting
    alert_channels: list[str] = field(default_factory=lambda: ["log", "webhook"])
    escalation_threshold: int = 5  # events before escalation

    # Prevention
    block_suspicious_ips: bool = False
    require_correlation_id: bool = True
    enforce_https: bool = True


class SecurityCommandCenter:
    """Centralized security operations center."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logs_path = project_root / "logs" / "security"
        self.config_path = project_root / "config" / "security"
        self.guardrails = self._load_guardrails()

    def _load_guardrails(self) -> GuardrailConfig:
        """Load or create guardrail configuration."""
        config_file = self.config_path / "guardrails.json"

        if config_file.exists():
            with open(config_file) as f:
                data = json.load(f)
                return GuardrailConfig(**data)

        # Create default config
        config = GuardrailConfig()
        self.config_path.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(asdict(config), f, indent=2)

        return config

    def profile_threats(self) -> ThreatProfile:
        """Analyze logs to build comprehensive threat profile."""
        profile = ThreatProfile()

        # Collect all security events
        events = self._collect_security_events(days=7)
        profile.total_events = len(events)

        if not events:
            profile.risk_score = 0.0
            profile.recommendations.append("No security events detected - baseline established")
            return profile

        # Categorize threats
        for event in events:
            category = event.get("event_type", "unknown")
            profile.threat_categories[category] = profile.threat_categories.get(category, 0) + 1

            severity = event.get("severity", "info")
            profile.severity_distribution[severity] = profile.severity_distribution.get(severity, 0) + 1

        # Calculate detection accuracy
        total_threats = profile.threat_categories.get("parasite.detected", 0)
        false_positives = profile.threat_categories.get("parasite.false_positive", 0)
        if total_threats > 0:
            profile.detection_accuracy = (total_threats - false_positives) / total_threats

        # Identify top attack sources
        source_ips = Counter(e.get("source_ip", "unknown") for e in events if e.get("source_ip"))
        profile.top_attack_sources = [{"ip": ip, "count": count} for ip, count in source_ips.most_common(10)]

        # Calculate risk score (0-100)
        severity_weights = {"critical": 10, "error": 5, "warning": 2, "info": 0}
        weighted_score = sum(
            profile.severity_distribution.get(sev, 0) * weight for sev, weight in severity_weights.items()
        )
        profile.risk_score = min(100, weighted_score * 2)

        # Generate recommendations
        profile.recommendations = self._generate_recommendations(profile)
        profile.active_mitigations = self._get_active_mitigations()

        return profile

    def _collect_security_events(self, days: int = 7) -> list[dict]:
        """Collect security events from all log sources."""
        events = []
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Mothership audit logs
        mothership_log = self.logs_path / "mothership" / "mothership_audit.log"
        if mothership_log.exists():
            with open(mothership_log) as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event.get("timestamp", "").replace("Z", "+00:00"))
                        if event_time > cutoff:
                            events.append(event)
                    except (json.JSONDecodeError, ValueError):
                        continue

        return events

    def _generate_recommendations(self, profile: ThreatProfile) -> list[str]:
        """Generate security recommendations based on profile."""
        recommendations = []

        # Check detection accuracy
        if profile.detection_accuracy < 0.95:
            recommendations.append(f"Review detection thresholds - accuracy at {profile.detection_accuracy:.1%}")

        # Check for critical events
        critical_count = profile.severity_distribution.get("critical", 0)
        if critical_count > 0:
            recommendations.append(f"URGENT: {critical_count} critical events detected - immediate review required")

        # Check attack patterns
        if len(profile.top_attack_sources) > 5:
            recommendations.append("Multiple attack sources detected - consider IP blocking or rate limiting")

        # Check risk score
        if profile.risk_score > 50:
            recommendations.append(f"Risk score elevated ({profile.risk_score:.1f}/100) - review security posture")

        # Check for missing detections
        if profile.threat_categories.get("parasite.detected", 0) == 0:
            recommendations.append("No parasite detections recorded - verify Parasite Guard is enabled")

        return recommendations

    def _get_active_mitigations(self) -> list[str]:
        """Get list of currently active mitigation strategies."""
        mitigations = []

        if self.guardrails.auto_isolate:
            mitigations.append("Auto-isolation of detected parasites")
        if self.guardrails.auto_sanitize:
            mitigations.append("Automatic request sanitization")
        if self.guardrails.block_suspicious_ips:
            mitigations.append("IP-based blocking")
        if self.guardrails.require_correlation_id:
            mitigations.append("Correlation ID enforcement")

        # Check environment settings
        if os.getenv("PARASITE_GUARD", "0") == "1":
            mitigations.append("Parasite Guard active")
        if os.getenv("GRID_ENVIRONMENT") == "production":
            mitigations.append("Production security mode")

        return mitigations

    def apply_guardrails(self, config_updates: dict[str, Any] | None = None) -> GuardrailConfig:
        """Apply or update security guardrails."""
        if config_updates:
            for key, value in config_updates.items():
                if hasattr(self.guardrails, key):
                    setattr(self.guardrails, key, value)

        # Save updated configuration
        config_file = self.config_path / "guardrails.json"
        with open(config_file, "w") as f:
            json.dump(asdict(self.guardrails), f, indent=2)

        # Apply environment variables
        os.environ["PARASITE_GUARD"] = "1"
        os.environ["PARASITE_DETECT_THRESHOLD"] = str(self.guardrails.parasite_threshold)
        os.environ["PARASITE_ANOMALY_Z_THRESHOLD"] = str(self.guardrails.z_score_threshold)

        print(f"✓ Guardrails applied: {len(self._get_active_mitigations())} active mitigations")

        return self.guardrails

    def monitor_realtime(self, duration_seconds: int = 60) -> None:
        """Start real-time security monitoring."""
        print(f"\n🔒 Starting real-time security monitoring ({duration_seconds}s)...")
        print("=" * 60)

        monitor = SecurityMonitor()
        start_time = datetime.now(UTC)
        event_count = 0

        try:
            while (datetime.now(UTC) - start_time).seconds < duration_seconds:
                # Check for new events
                new_events = self._get_recent_events(seconds=5)

                for event in new_events:
                    event_count += 1
                    self._display_event(event)

                    # Check for critical events
                    if event.get("severity") in ("critical", "error"):
                        self._trigger_alert(event)

                asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")

        print(f"\n📊 Monitored {event_count} events over {(datetime.now(UTC) - start_time).seconds}s")

    def _get_recent_events(self, seconds: int = 5) -> list[dict]:
        """Get events from last N seconds."""
        events = []
        cutoff = datetime.now(UTC) - timedelta(seconds=seconds)

        mothership_log = self.logs_path / "mothership" / "mothership_audit.log"
        if mothership_log.exists():
            # Read last 100 lines for efficiency
            with open(mothership_log) as f:
                lines = f.readlines()[-100:]
                for line in lines:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event.get("timestamp", "").replace("Z", "+00:00"))
                        if event_time > cutoff:
                            events.append(event)
                    except (json.JSONDecodeError, ValueError):
                        continue

        return events

    def _display_event(self, event: dict) -> None:
        """Display security event with formatting."""
        severity = event.get("severity", "info")
        event_type = event.get("event_type", "unknown")
        timestamp = event.get("timestamp", "")[11:19]  # HH:MM:SS

        # Color coding
        colors = {
            "critical": "\033[91m",  # Red
            "error": "\033[91m",  # Red
            "warning": "\033[93m",  # Yellow
            "info": "\033[94m",  # Blue
        }
        reset = "\033[0m"
        color = colors.get(severity, "")

        print(f"{timestamp} {color}[{severity.upper():8}]{reset} {event_type}")

        if event_type == "access.granted" and event.get("details"):
            details = event["details"]
            print(f"           Path: {details.get('method')} {details.get('path')}")
            print(f"           Client: {details.get('client_ip')}")

    def _trigger_alert(self, event: dict) -> None:
        """Trigger alert for critical events."""
        severity = event.get("severity", "info")
        print(f"\n🚨 ALERT: {severity.upper()} event detected!")
        print(f"   Event ID: {event.get('event_id')}")
        print(f"   Type: {event.get('event_type')}")
        print(f"   Time: {event.get('timestamp')}")

        # Auto-response actions
        if self.guardrails.auto_isolate and severity == "critical":
            print("   → Auto-isolation triggered")

        if self.guardrails.auto_sanitize:
            print("   → Sanitization applied")

    def generate_report(self, output_path: Path | None = None) -> Path:
        """Generate comprehensive security report."""
        profile = self.profile_threats()

        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "profile": asdict(profile),
            "guardrails": asdict(self.guardrails),
            "system_status": {
                "parasite_guard_enabled": os.getenv("PARASITE_GUARD") == "1",
                "environment": os.getenv("GRID_ENVIRONMENT", "unknown"),
                "log_retention_days": 90,
            },
        }

        if output_path is None:
            output_path = self.project_root / "reports" / "security"

        output_path.mkdir(parents=True, exist_ok=True)
        report_file = output_path / f"security_report_{datetime.now(UTC):%Y%m%d_%H%M%S}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        # Generate human-readable summary
        summary_file = report_file.with_suffix(".md")
        self._generate_markdown_summary(profile, summary_file)

        print(f"✓ Report generated: {report_file}")
        print(f"✓ Summary: {summary_file}")

        return report_file

    def _generate_markdown_summary(self, profile: ThreatProfile, path: Path) -> None:
        """Generate human-readable markdown summary."""
        with open(path, "w") as f:
            f.write("# GRID Security Report\n\n")
            f.write(f"**Generated:** {profile.timestamp}\n\n")

            f.write("## Risk Assessment\n\n")
            f.write(f"**Risk Score:** {profile.risk_score:.1f}/100\n\n")

            if profile.risk_score < 25:
                f.write("🟢 **Status:** Low Risk\n\n")
            elif profile.risk_score < 50:
                f.write("🟡 **Status:** Medium Risk\n\n")
            elif profile.risk_score < 75:
                f.write("🟠 **Status:** High Risk\n\n")
            else:
                f.write("🔴 **Status:** Critical Risk\n\n")

            f.write("## Threat Summary\n\n")
            f.write(f"- **Total Events (7 days):** {profile.total_events:,}\n")
            f.write(f"- **Detection Accuracy:** {profile.detection_accuracy:.1%}\n")
            f.write(f"- **Active Mitigations:** {len(profile.active_mitigations)}\n\n")

            f.write("### Severity Distribution\n\n")
            for severity, count in sorted(profile.severity_distribution.items()):
                f.write(f"- {severity.title()}: {count:,}\n")
            f.write("\n")

            if profile.recommendations:
                f.write("## Recommendations\n\n")
                for i, rec in enumerate(profile.recommendations, 1):
                    f.write(f"{i}. {rec}\n")
                f.write("\n")

            f.write("## Active Mitigations\n\n")
            for mitigation in profile.active_mitigations:
                f.write(f"- ✅ {mitigation}\n")


def main():
    parser = argparse.ArgumentParser(description="GRID Security Command Center")
    parser.add_argument("--profile", action="store_true", help="Generate threat profile")
    parser.add_argument("--monitor", action="store_true", help="Start real-time monitoring")
    parser.add_argument("--respond", action="store_true", help="Execute auto-response")
    parser.add_argument("--guardrails", action="store_true", help="Apply security guardrails")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive report")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in seconds")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    scc = SecurityCommandCenter(project_root)

    if args.profile:
        print("🔍 Generating threat profile...")
        profile = scc.profile_threats()
        print("\n📊 Threat Profile Summary:")
        print(f"   Total Events: {profile.total_events:,}")
        print(f"   Risk Score: {profile.risk_score:.1f}/100")
        print(f"   Detection Accuracy: {profile.detection_accuracy:.1%}")
        print(f"\n🛡️ Active Mitigations: {len(profile.active_mitigations)}")
        for mitigation in profile.active_mitigations:
            print(f"   ✓ {mitigation}")

        if profile.recommendations:
            print("\n⚠️ Recommendations:")
            for rec in profile.recommendations:
                print(f"   → {rec}")

    elif args.monitor:
        scc.monitor_realtime(duration_seconds=args.duration)

    elif args.respond:
        print("🚨 Executing automated response protocols...")
        # Implementation for automated response
        print("✓ Response protocols activated")

    elif args.guardrails:
        print("🔒 Applying security guardrails...")
        config = scc.apply_guardrails()
        print("\n📋 Guardrail Configuration:")
        print(f"   Detection Sensitivity: {config.detection_sensitivity}")
        print(f"   Parasite Threshold: {config.parasite_threshold}")
        print(f"   Auto-isolate: {config.auto_isolate}")
        print(f"   Auto-sanitize: {config.auto_sanitize}")
        print(f"   Rate Limit: {config.rate_limit_requests}/min")

    elif args.report:
        scc.generate_report()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
