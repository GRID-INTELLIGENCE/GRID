#!/usr/bin/env python3
"""
AI Safety-Aware Server Denylist Manager
Integrates with AI safety tracing and structured logging
"""

import sys
from pathlib import Path
from typing import Any

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from init_safety_logging import (
    EventType,
    SafetyLogger,
    Severity,
    calculate_safety_score,
    create_safety_event,
    determine_risk_level,
)
from server_denylist_manager import ServerDenylistManager


class SafetyAwareServerManager(ServerDenylistManager):
    """
    Server Denylist Manager with AI Safety integration

    Adds:
    - Safety scoring and risk assessment
    - Structured logging to AI safety framework
    - Trace correlation with safety events
    - Metrics collection and reporting
    """

    def __init__(self, config_path: str, safety_log_dir: str | None = None):
        super().__init__(config_path)

        # Initialize safety logger if directory provided
        self.safety_logger = None
        if safety_log_dir:
            self.safety_logger = SafetyLogger(Path(safety_log_dir))

    def is_denied(self, server_name: str) -> tuple[bool, str]:
        """Check if server is denied with safety logging"""
        is_denied, reason = super().is_denied(server_name)

        # Log to safety system
        if self.safety_logger:
            event_type = EventType.SERVER_DENIED if is_denied else EventType.SERVER_ALLOWED
            severity = self._determine_severity(reason or "") if is_denied else Severity.INFO

            event = create_safety_event(
                event_type=event_type,
                severity=severity,
                server_name=server_name,
                denylist_reason=reason,
                context={
                    "scope": "server_lifecycle",
                    "action": "deny" if is_denied else "allow",
                    "config_source": str(self.config_path),
                },
            )

            self.safety_logger.log_event(event)

        return is_denied, reason or ""

    def apply_to_mcp_config(self, mcp_config_path: str, output_path: str | None = None):
        """Apply denylist with safety boundary enforcement logging"""

        # Log configuration sanitization start
        if self.safety_logger:
            start_event = create_safety_event(
                event_type=EventType.CONFIG_SANITIZED,
                severity=Severity.INFO,
                context={
                    "action": "config_sanitization_start",
                    "config_path": mcp_config_path,
                    "output_path": output_path or mcp_config_path,
                },
            )
            self.safety_logger.log_event(start_event)

        # Apply denylist (calls is_denied which logs each server)
        super().apply_to_mcp_config(mcp_config_path, output_path)

        # Log configuration sanitization complete
        if self.safety_logger:
            denied_servers = self.get_denied_servers()

            end_event = create_safety_event(
                event_type=EventType.SAFETY_BOUNDARY_ENFORCED,
                severity=Severity.INFO,
                context={
                    "action": "config_sanitization_complete",
                    "config_path": mcp_config_path,
                    "denied_count": len(denied_servers),
                    "allowed_count": len(self.get_allowed_servers()),
                },
                metadata={
                    "denied_servers": [name for name, _ in denied_servers]  # type: ignore[reportOptionalMemberAccess]
                },
            )
            self.safety_logger.log_event(end_event)

    def detect_violations(self) -> list[dict[str, Any]]:
        """Detect policy violations in current configuration"""
        violations = []

        for server in self.inventory:
            is_denied, reason = self.is_denied(server.name)

            # Check for critical violations
            if is_denied and reason in ["security-concern", "startup-failure"]:
                safety_score = calculate_safety_score(reason)
                risk_level = determine_risk_level(safety_score)

                violation = {
                    "server": server.name,
                    "violation_type": reason,
                    "safety_score": safety_score,
                    "risk_level": risk_level,
                    "severity": "critical" if safety_score < 0.3 else "high",
                }
                violations.append(violation)

                # Log violation
                if self.safety_logger:
                    event = create_safety_event(
                        event_type=EventType.VIOLATION_DETECTED,
                        severity=Severity.CRITICAL if safety_score < 0.3 else Severity.ERROR,
                        server_name=server.name,
                        denylist_reason=reason,
                        context={"violation_type": reason, "requires_immediate_action": safety_score < 0.3},
                    )
                    self.safety_logger.log_event(event)

        return violations

    def generate_safety_report(self) -> str:
        """Generate safety-focused report with risk analysis"""
        base_report = super().generate_report()

        # Add safety analysis section
        violations = self.detect_violations()

        safety_section = ["\n" + "=" * 80, "AI SAFETY ANALYSIS", "=" * 80]

        if violations:
            safety_section.append(f"\n⚠ CRITICAL VIOLATIONS DETECTED: {len(violations)}\n")

            for v in violations:
                safety_section.append(f"Server: {v['server']}")
                safety_section.append(f"  Violation: {v['violation_type']}")
                safety_section.append(f"  Risk Level: {v['risk_level'].upper()}")
                safety_section.append(f"  Safety Score: {v['safety_score']:.2f}")
                safety_section.append(f"  Severity: {v['severity'].upper()}")
                safety_section.append("")
        else:
            safety_section.append("\n✓ No critical violations detected")

        # Add metrics summary if available
        if self.safety_logger:
            metrics = self.safety_logger.metrics.get_summary()
            safety_section.extend(
                [
                    "\n" + "-" * 80,
                    "SAFETY METRICS",
                    "-" * 80,
                    f"Total Evaluations: {metrics['total_evaluations']}",
                    f"Denial Rate: {metrics['denial_rate']:.1%}",
                    f"Average Safety Score: {metrics['average_safety_score']:.2f}",
                    f"High Risk Servers: {metrics['high_risk_count']}",
                ]
            )

        safety_section.append("=" * 80)

        return base_report + "\n".join(safety_section)

    def save_safety_metrics(self):
        """Save current safety metrics"""
        if self.safety_logger:
            return self.safety_logger.save_metrics()
        return None

    def _determine_severity(self, reason: str) -> Severity:
        """Determine event severity from denylist reason"""
        severity_map = {
            "security-concern": Severity.CRITICAL,
            "startup-failure": Severity.ERROR,
            "missing-dependencies": Severity.WARNING,
            "resource-intensive": Severity.WARNING,
            "network-dependent": Severity.INFO,
            "deprecated": Severity.WARNING,
            "redundant": Severity.INFO,
            "development-only": Severity.INFO,
            "user-disabled": Severity.INFO,
        }

        return severity_map.get(reason, Severity.WARNING)


def main():
    """Main CLI with safety integration"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Safety-Aware Server Denylist Manager")
    parser.add_argument("--config", required=True, help="Path to denylist config")
    parser.add_argument("--safety-logs", help="Path to safety log directory")
    parser.add_argument("--mcp-config", help="Path to MCP config to update")
    parser.add_argument("--output", help="Output path for modified MCP config")
    parser.add_argument("--report", action="store_true", help="Generate safety report")
    parser.add_argument("--check", help="Check if specific server is denied")
    parser.add_argument("--detect-violations", action="store_true", help="Detect violations")
    parser.add_argument("--save-metrics", action="store_true", help="Save safety metrics")

    args = parser.parse_args()

    # Initialize manager with safety logging
    manager = SafetyAwareServerManager(args.config, args.safety_logs)

    if args.report:
        print(manager.generate_safety_report())

    if args.check:
        is_denied, reason = manager.is_denied(args.check)
        if is_denied:
            safety_score = calculate_safety_score(reason)
            risk_level = determine_risk_level(safety_score)
            print(f"✗ {args.check} is DENIED")
            print(f"  Reason: {reason}")
            print(f"  Safety Score: {safety_score:.2f}")
            print(f"  Risk Level: {risk_level.upper()}")
        else:
            print(f"✓ {args.check} is ALLOWED")

    if args.detect_violations:
        violations = manager.detect_violations()
        if violations:
            print(f"\n⚠ VIOLATIONS DETECTED: {len(violations)}\n")
            for v in violations:
                print(f"Server: {v['server']}")
                print(f"  Type: {v['violation_type']}")
                print(f"  Risk: {v['risk_level'].upper()}")
                print(f"  Severity: {v['severity'].upper()}\n")
        else:
            print("✓ No violations detected")

    if args.mcp_config:
        manager.apply_to_mcp_config(args.mcp_config, args.output)

    if args.save_metrics:
        metrics = manager.save_safety_metrics()
        if metrics:
            print("\n✓ Safety metrics saved")
            print(f"  Evaluations: {metrics['total_evaluations']}")
            print(f"  Denial Rate: {metrics['denial_rate']:.1%}")
            print(f"  Avg Safety Score: {metrics['average_safety_score']:.2f}")


if __name__ == "__main__":
    main()
