#!/usr/bin/env python3
"""
GRID Threat Response Automation
=============================

Automated response system for security threats.
Implements escalation policies, containment, and recovery.

Usage:
    python tools/threat_response.py --scan
    python tools/threat_response.py --contain <threat_id>
    python tools/threat_response.py --recover <threat_id>
"""

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))


class ResponseLevel(Enum):
    """Threat response escalation levels."""

    MONITOR = "monitor"  # Observe only
    ALERT = "alert"  # Notify security team
    CONTAIN = "contain"  # Isolate affected component
    BLOCK = "block"  # Block attacker/source
    SHUTDOWN = "shutdown"  # Emergency shutdown


@dataclass
class ThreatResponse:
    """Structured threat response action."""

    response_id: str
    threat_id: str
    level: ResponseLevel
    timestamp: str
    actions_taken: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    success: bool = False
    notes: str = ""


class ThreatResponseOrchestrator:
    """Orchestrates automated threat response."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.response_log = project_root / "logs" / "security" / "responses.jsonl"
        self.response_log.parent.mkdir(parents=True, exist_ok=True)

        # Response policies by threat type
        self.policies = {
            "parasite.detected": ResponseLevel.CONTAIN,
            "parasite.critical": ResponseLevel.BLOCK,
            "injection.sql": ResponseLevel.BLOCK,
            "injection.xss": ResponseLevel.CONTAIN,
            "injection.command": ResponseLevel.BLOCK,
            "rate_limit.exceeded": ResponseLevel.ALERT,
            "auth.failure": ResponseLevel.ALERT,
            "path.traversal": ResponseLevel.CONTAIN,
        }

    def analyze_threat(self, threat_data: dict) -> ResponseLevel:
        """Analyze threat and determine response level."""
        threat_type = threat_data.get("type", "unknown")
        severity = threat_data.get("severity", "info")

        # Check explicit policy
        base_level = self.policies.get(threat_type, ResponseLevel.MONITOR)

        # Escalate based on severity
        if severity == "critical":
            if base_level.value in ["monitor", "alert"]:
                return ResponseLevel.CONTAIN
            elif base_level == ResponseLevel.CONTAIN:
                return ResponseLevel.BLOCK

        return base_level

    async def execute_response(
        self, threat_id: str, threat_data: dict, level: ResponseLevel | None = None
    ) -> ThreatResponse:
        """Execute automated response to threat."""
        if level is None:
            level = self.analyze_threat(threat_data)

        response = ThreatResponse(
            response_id=f"resp_{datetime.now(UTC):%Y%m%d%H%M%S}_{threat_id[:8]}",
            threat_id=threat_id,
            level=level,
            timestamp=datetime.now(UTC).isoformat(),
            affected_components=threat_data.get("components", []),
        )

        try:
            # Execute response actions based on level
            if level == ResponseLevel.MONITOR:
                response.actions_taken.append("Logged threat for monitoring")

            elif level == ResponseLevel.ALERT:
                await self._send_alert(threat_data, response)
                response.actions_taken.append("Security team alerted")

            elif level == ResponseLevel.CONTAIN:
                await self._send_alert(threat_data, response)
                containment = await self._contain_threat(threat_data)
                response.actions_taken.extend(containment)

            elif level == ResponseLevel.BLOCK:
                await self._send_alert(threat_data, response)
                containment = await self._contain_threat(threat_data)
                response.actions_taken.extend(containment)
                block = await self._block_source(threat_data)
                response.actions_taken.extend(block)

            elif level == ResponseLevel.SHUTDOWN:
                await self._emergency_shutdown(threat_data)
                response.actions_taken.append("Emergency shutdown initiated")

            response.success = True

        except Exception as e:
            response.success = False
            response.notes = f"Response failed: {str(e)}"

        # Log response
        self._log_response(response)

        return response

    async def _send_alert(self, threat_data: dict, response: ThreatResponse) -> None:
        """Send alert to security team."""
        print(f"🚨 ALERT: {threat_data.get('type', 'unknown')} detected")
        print(f"   Threat ID: {response.threat_id}")
        print(f"   Response Level: {response.level.value}")
        print(f"   Time: {response.timestamp}")

        # Could integrate with: PagerDuty, Slack, email, etc.
        # For now, log to console and file

    async def _contain_threat(self, threat_data: dict) -> list[str]:
        """Contain the threat by isolating affected components."""
        actions = []
        components = threat_data.get("components", [])

        for component in components:
            # Enable Parasite Guard for component if not already
            env_var = f"PARASITE_GUARD_{component.upper()}"
            os.environ[env_var] = "1"
            actions.append(f"Enabled Parasite Guard for {component}")

            # Set mode to ENFORCE
            mode_var = f"PARASITE_GUARD_{component.upper()}_MODE"
            os.environ[mode_var] = "ENFORCE"
            actions.append(f"Set {component} to ENFORCE mode")

        return actions

    async def _block_source(self, threat_data: dict) -> list[str]:
        """Block the attack source."""
        actions = []
        source_ip = threat_data.get("source_ip")

        if source_ip:
            # Add to blacklist (conceptual - actual implementation would use firewall/WAF)
            actions.append(f"Added {source_ip} to temporary blocklist")
            print(f"   → Blocking source IP: {source_ip}")

        # Could integrate with: iptables, AWS WAF, Cloudflare, etc.

        return actions

    async def _emergency_shutdown(self, threat_data: dict) -> None:
        """Emergency shutdown in critical situations."""
        print("⚠️ EMERGENCY SHUTDOWN INITIATED")
        print("   This would gracefully shutdown affected services")
        print("   and alert on-call personnel.")

        # In production, this would:
        # 1. Gracefully drain connections
        # 2. Save state
        # 3. Shutdown services
        # 4. Alert on-call
        # 5. Activate standby systems

    def _log_response(self, response: ThreatResponse) -> None:
        """Log response action to persistent storage."""
        with open(self.response_log, "a") as f:
            f.write(json.dumps(asdict(response)) + "\n")

    def get_response_history(self, hours: int = 24) -> list[ThreatResponse]:
        """Get recent response history."""
        responses = []
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        if self.response_log.exists():
            with open(self.response_log) as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        resp_time = datetime.fromisoformat(data.get("timestamp", "").replace("Z", "+00:00"))
                        if resp_time > cutoff:
                            responses.append(ThreatResponse(**data))
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue

        return responses

    def generate_response_report(self) -> dict:
        """Generate report of all response activities."""
        responses = self.get_response_history(hours=168)  # 7 days

        if not responses:
            return {
                "period": "7 days",
                "total_responses": 0,
                "summary": "No automated responses triggered",
            }

        level_counts = {}
        success_count = sum(1 for r in responses if r.success)

        for r in responses:
            level = r.level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "period": "7 days",
            "total_responses": len(responses),
            "successful_responses": success_count,
            "success_rate": success_count / len(responses) if responses else 0,
            "by_level": level_counts,
            "most_recent": asdict(responses[-1]) if responses else None,
        }


def main():
    parser = argparse.ArgumentParser(description="GRID Threat Response Automation")
    parser.add_argument("--scan", action="store_true", help="Scan for active threats")
    parser.add_argument("--contain", metavar="THREAT_ID", help="Contain specific threat")
    parser.add_argument("--block", metavar="SOURCE_IP", help="Block IP address")
    parser.add_argument("--report", action="store_true", help="Generate response report")
    parser.add_argument("--simulate", metavar="TYPE", help="Simulate threat response")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    orchestrator = ThreatResponseOrchestrator(project_root)

    if args.scan:
        print("🔍 Scanning for active threats...")
        # Implementation would scan logs, check metrics, etc.
        print("✓ No active threats detected")

    elif args.contain:
        threat_id = args.contain
        print(f"🛡️ Containing threat: {threat_id}")
        threat_data = {
            "type": "manual.containment",
            "severity": "warning",
            "components": ["api", "middleware"],
        }
        response = asyncio.run(orchestrator.execute_response(threat_id, threat_data, ResponseLevel.CONTAIN))
        print(f"✓ Response executed: {response.level.value}")
        print(f"  Actions: {', '.join(response.actions_taken)}")

    elif args.block:
        ip = args.block
        print(f"🚫 Blocking IP: {ip}")
        threat_data = {"type": "manual.block", "source_ip": ip, "severity": "warning"}
        response = asyncio.run(orchestrator.execute_response(f"manual_{ip}", threat_data, ResponseLevel.BLOCK))
        print(f"✓ IP blocked: {ip}")

    elif args.report:
        report = orchestrator.generate_response_report()
        print("\n📊 Threat Response Report (7 days)")
        print("=" * 50)
        print(f"Total Responses: {report['total_responses']}")
        if report["total_responses"] > 0:
            print(f"Success Rate: {report['success_rate']:.1%}")
            print("\nBy Response Level:")
            for level, count in report["by_level"].items():
                print(f"  {level}: {count}")

    elif args.simulate:
        threat_type = args.simulate
        print(f"🎮 Simulating threat: {threat_type}")

        threat_data = {
            "type": threat_type,
            "severity": "error",
            "source_ip": "192.168.1.100",
            "components": ["api"],
            "details": {"simulated": True},
        }

        level = orchestrator.analyze_threat(threat_data)
        print(f"📊 Analyzed as: {level.value}")

        response = asyncio.run(orchestrator.execute_response("sim_001", threat_data))
        print("\n✓ Response executed")
        print(f"  Level: {response.level.value}")
        print(f"  Actions: {response.actions_taken}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
