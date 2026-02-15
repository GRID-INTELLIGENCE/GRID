#!/usr/bin/env python3
"""
GRID Security Assessment Agent
==============================
AI agent for automated security testing of the GRID system, simulating attacks and analyzing defenses.
Developed based on the security assessment specification.
"""

import asyncio
import json
import logging
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for security module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import existing security modules if available
try:
    import security
    from security.forensic_log_analyzer import ForensicLogAnalyzer
    from security.network_interceptor import NetworkAccessDenied, nac
except ImportError:
    security = None
    nac = None
    ForensicLogAnalyzer = None


class GRIDSecurityAssessmentAgent:
    """Automated security testing agent for the GRID system."""

    def __init__(self, config: dict[str, Any]):
        self.agent_info = config.get("agent", {})
        self.tools_schema = config.get("tools", [])
        self.flows = config.get("flows", [])
        self.system_profile = config.get("system_profile", {})

        # Internal state
        self.audit_events = []
        self.session_findings = []

        # Setup logging
        self.security_dir = Path(__file__).parent
        self.logs_dir = self.security_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger("GRIDSecurityAgent")
        self.logger.setLevel(logging.INFO)

        # Session ID based on current time
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"assessment_{self.session_id}.log"
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Console output
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def log_event(self, event_type: str, details: dict[str, Any]):
        """Log a security event to the audit trail."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
            "user": self.system_profile.get("users", ["system"])[0],
        }
        self.audit_events.append(event)
        self.logger.info(f"AUDIT [{event_type}]: {json.dumps(details)}")

    # Tool Implementations

    def test_filesystem_access(self, path: str, operation: str, content: str = "") -> dict[str, Any]:
        """Test read/write access to filesystem paths."""
        self.logger.info(f"Executing tool: test_filesystem_access(path='{path}', operation='{operation}')")

        try:
            # Handle potential non-existent paths by resolving manually if possible
            try:
                path_obj = Path(path).resolve()
            except Exception:
                path_obj = Path(path)

            # Check if path is allowed in profile
            allowed_paths = self.system_profile.get("allowed_paths", [])
            is_path_allowed = False
            for allowed in allowed_paths:
                try:
                    if str(path_obj).startswith(str(Path(allowed).resolve())):
                        is_path_allowed = True
                        break
                except Exception:
                    continue

            # First, check authorization
            if not is_path_allowed:
                self.log_event(
                    "AUTHZ_ACCESS_DENIED", {"path": path, "operation": operation, "reason": "Path not in allowed list"}
                )
                return {"success": False, "error": "Access denied by security profile"}

            # Then, check existence and perform operation
            if operation == "read":
                if not path_obj.exists():
                    return {"success": False, "error": f"File not found: {path}"}

                with open(path_obj, encoding="utf-8", errors="replace") as f:
                    data = f.read(1024)  # Read first 1KB

                self.log_event("DATA_ACCESS", {"path": path, "operation": "read", "bytes": len(data)})
                return {
                    "success": True,
                    "result": (data[:100] + "...") if len(data) > 100 else data,
                    "audit_event": "DATA_ACCESS",
                }

            elif operation == "write":
                with open(path_obj, "w", encoding="utf-8") as f:
                    f.write(content)

                self.log_event("DATA_ACCESS", {"path": path, "operation": "write", "content_len": len(content)})
                return {"success": True, "result": "Successfully wrote content", "audit_event": "DATA_ACCESS"}

            elif operation == "list":
                if not path_obj.is_dir():
                    return {"success": False, "error": "Path is not a directory"}

                items = [p.name for p in path_obj.iterdir()]
                self.log_event("AUTHZ_ACCESS", {"path": path, "operation": "list", "count": len(items)})
                return {
                    "success": True,
                    "result": f"Found {len(items)} items: " + ", ".join(items[:5]),
                    "audit_event": "AUTHZ_ACCESS",
                }

            return {"success": False, "error": f"Unsupported operation: {operation}"}

        except PermissionError:
            self.log_event(
                "AUTHZ_ACCESS_DENIED", {"path": path, "operation": operation, "reason": "OS Permission Error"}
            )
            return {"success": False, "error": "OS Permission Denied"}
        except Exception as e:
            self.logger.error(f"Error in test_filesystem_access: {e}")
            return {"success": False, "error": str(e)}

    def test_network_access(self, url: str, method: str = "GET") -> dict[str, Any]:
        """Test network/SSRF access to URLs."""
        self.logger.info(f"Executing tool: test_network_access(url='{url}', method='{method}')")

        # 1. Check local SSRF patterns from profile
        blocked_patterns = self.system_profile.get("blocked_network_patterns", [])
        for pattern in blocked_patterns:
            if pattern in url:
                self.log_event("REQUEST_BLOCKED", {"url": url, "reason": f"SSRF pattern match: {pattern}"})
                return {
                    "success": False,
                    "blocked": True,
                    "reason": f"Blocked by SSRF filter: {pattern}",
                    "audit_event": "REQUEST_BLOCKED",
                }

        # 2. Perform actual request (integrated with NAC)
        try:
            import requests

            # If NAC is active, this request might be intercepted and raise NetworkAccessDenied
            response = requests.request(method, url, timeout=5)

            self.log_event("NETWORK_ACCESS", {"url": url, "method": method, "status": response.status_code})
            return {"success": True, "blocked": False, "reason": "Request allowed", "audit_event": "NETWORK_ACCESS"}

        except NetworkAccessDenied as e:
            self.log_event(
                "AUTHZ_ACCESS_DENIED", {"url": url, "method": method, "reason": "Blocked by GRID Security System"}
            )
            return {"success": False, "blocked": True, "reason": str(e), "audit_event": "AUTHZ_ACCESS_DENIED"}
        except ImportError:
            self.logger.warning("Requests library not found, simulating network access")
            return {"success": True, "blocked": False, "result": "Simulated access (requests not installed)"}
        except Exception as e:
            # Handle standard network errors (timeout, connection refused, etc)
            self.log_event("NETWORK_ERROR", {"url": url, "error": str(e)})
            return {"success": False, "blocked": False, "error": str(e)}

    def scan_anomalies(self, scan_type: str, hours: int = 24) -> dict[str, Any]:
        """Scan for network and filesystem anomalies using existing Forensic Analyzer."""
        self.logger.info(f"Executing tool: scan_anomalies(scan_type='{scan_type}', hours={hours})")

        if not ForensicLogAnalyzer:
            return {
                "anomalies_found": 0,
                "details": ["ForensicLogAnalyzer not available - install security module dependencies"],
                "alerts": [],
            }

        try:
            analyzer = ForensicLogAnalyzer(self.logs_dir)

            audit_events = analyzer.parse_audit_log()
            network_events = analyzer.parse_network_log()

            analysis = analyzer.analyze_events(audit_events, network_events)

            anomalies = analysis.get("anomalies", [])
            alerts = analysis.get("errors_warnings", [])

            if scan_type == "network":
                anomalies = [a for a in anomalies if "network" in a.lower() or "blocked" in a.lower()]
            elif scan_type == "filesystem":
                anomalies = [a for a in anomalies if "file" in a.lower() or "access" in a.lower()]
            elif scan_type == "connections":
                anomalies = [a for a in anomalies if "initialization" in a.lower()]

            self.logger.info(f"Anomaly scan complete. Found {len(anomalies)} anomalies and {len(alerts)} alerts.")
            return {"anomalies_found": len(anomalies), "details": anomalies, "alerts": alerts}

        except Exception as e:
            self.logger.error(f"Error in scan_anomalies: {e}")
            return {"anomalies_found": 0, "details": [], "error": str(e)}

    def generate_security_report(
        self, include_paths: bool = True, include_users: bool = True, include_anomalies: bool = True
    ) -> dict[str, Any]:
        """Generate a comprehensive security assessment report in Markdown."""
        self.logger.info("Generating security report...")

        report = []
        report.append(f"# {self.agent_info.get('name', 'GRID Security Report')}")
        report.append(f"**Version:** {self.agent_info.get('version', '1.0')}")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Session ID:** {self.session_id}")
        report.append("")

        report.append("## 1. Executive Summary")
        report.append(self.agent_info.get("description", "Automated security assessment of the GRID system."))
        report.append("")

        report.append("## 2. System Profile & Environment")
        report.append(f"- **OS:** {self.agent_info.get('environment', {}).get('os', 'Unknown')}")
        report.append(
            f"- **Hardening Level:** {self.agent_info.get('environment', {}).get('hardening_level', 'Unknown')}"
        )
        report.append(
            f"- **Audit Status:** {'Enabled' if self.agent_info.get('environment', {}).get('audit_enabled') else 'Disabled'}"
        )
        report.append("")

        if include_paths:
            report.append("### Allowed Paths")
            for p in self.system_profile.get("allowed_paths", []):
                report.append(f"- `{p}`")
            report.append("")

        if include_users:
            report.append("### Authorized Users")
            for u in self.system_profile.get("users", []):
                report.append(f"- `{u}`")
            report.append("")

        report.append("## 3. Session Activity & Audit Log")
        if not self.audit_events:
            report.append("No security-relevant activities recorded in this session.")
        else:
            report.append("| Timestamp | Event Type | Details |")
            report.append("| :--- | :--- | :--- |")
            for event in self.audit_events:
                details_str = json.dumps(event["details"])
                report.append(f"| {event['timestamp']} | **{event['event_type']}** | {details_str} |")
        report.append("")

        # Findings Analysis
        blocked_count = sum(
            1 for e in self.audit_events if e["event_type"] in ["AUTHZ_ACCESS_DENIED", "REQUEST_BLOCKED"]
        )
        allowed_count = sum(1 for e in self.audit_events if e["event_type"] in ["DATA_ACCESS", "NETWORK_ACCESS"])

        report.append("## 4. Assessment Results")
        report.append(f"- **Blocked Unauthorized Attempts:** {blocked_count}")
        report.append(f"- **Authorized Data Accesses:** {allowed_count}")
        report.append("")

        if blocked_count > 0:
            report.append("### 🚨 SECURITY FINDINGS")
            report.append("The system successfully blocked the following unauthorized actions:")
            for e in self.audit_events:
                if e["event_type"] in ["AUTHZ_ACCESS_DENIED", "REQUEST_BLOCKED"]:
                    report.append(f"- **{e['event_type']}**: {json.dumps(e['details'])}")
        else:
            report.append(
                "✅ **No security breaches simulated.** All attempts were either authorized or no attacks were performed."
            )
        report.append("")

        if include_anomalies:
            report.append("## 5. Anomaly Detection Summary")
            # Quick re-scan for the report
            anomalies = self.scan_anomalies("network")
            if anomalies["anomalies_found"] > 0:
                for d in anomalies["details"]:
                    report.append(f"- ⚠️ {d}")
            else:
                report.append("No anomalies detected in recent logs.")
            report.append("")

        report.append("## 6. Recommendations")
        recommendations = [
            "Maintain strict whitelist for all outbound network requests.",
            "Enable real-time alerting for AUTHZ_ACCESS_DENIED events.",
            "Review filesystem permissions for non-authorized paths.",
            "Regularly rotate encryption keys and API tokens if detected in logs.",
        ]
        for rec in recommendations:
            report.append(f"- {rec}")

        markdown = "\n".join(report)

        # Save report artifact
        report_file = self.logs_dir / f"security_assessment_report_{self.session_id}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"\n✅ Security Report Generated: {report_file}")

        return {
            "report_markdown": markdown,
            "summary": {
                "blocked_attempts": blocked_count,
                "authorized_access": allowed_count,
                "anomalies_found": 0,  # Placeholder
            },
            "recommendations": recommendations,
            "report_path": str(report_file),
        }

    # Flow Orchestration

    def run_flow(self, flow_name: str):
        """Execute a predefined security flow."""
        flow = next((f for f in self.flows if f["name"] == flow_name), None)
        if not flow:
            self.logger.error(f"Flow not found: {flow_name}")
            return

        self.logger.info(f"Starting Flow: {flow_name} - {flow['description']}")
        print("\n" + "=" * 80)
        print(f"  EXECUTING FLOW: {flow_name}")
        print("=" * 80 + "\n")

        for i, step in enumerate(flow["steps"], 1):
            tool_name = step["tool"]
            params = step["parameters"]

            print(f"[{i}/{len(flow['steps'])}] Calling {tool_name}...")

            if tool_name == "test_filesystem_access":
                result = self.test_filesystem_access(**params)
            elif tool_name == "test_network_access":
                result = self.test_network_access(**params)
            elif tool_name == "scan_anomalies":
                result = self.scan_anomalies(**params)
            elif tool_name == "generate_security_report":
                result = self.generate_security_report(**params)
            else:
                self.logger.error(f"Unknown tool: {tool_name}")
                continue

            status_emoji = "✅" if result.get("success", True) or result.get("blocked") else "❌"
            print(
                f"      Result: {status_emoji} " + (result.get("audit_event", result.get("reason", "Completed"))) + "\n"
            )

        print("=" * 80)
        print(f"  FLOW '{flow_name}' COMPLETED")
        print("=" * 80 + "\n")


# Main execution logic for CLI
def main():
    # Load configuration (in a real scenario, this would be from a file or the user request)
    config = {
        "agent": {
            "name": "GRID Security Assessment Agent",
            "description": "AI agent for automated security testing of the GRID system, simulating attacks and analyzing defenses",
            "version": "1.0",
            "capabilities": [
                "filesystem_access_testing",
                "network_ssrf_testing",
                "anomaly_detection",
                "forensic_reporting",
            ],
            "environment": {
                "os": "Windows 11 Pro",
                "hardening_level": "95%",
                "audit_enabled": False,
                "network_access": "disabled",
            },
        },
        "flows": [
            {
                "name": "filesystem_attack_simulation",
                "description": "Simulate filesystem access attacks",
                "steps": [
                    {
                        "tool": "test_filesystem_access",
                        "parameters": {"path": "C:/windows/system32/drivers/etc/hosts", "operation": "read"},
                    },
                    {"tool": "test_filesystem_access", "parameters": {"path": "e:/grid/.env", "operation": "read"}},
                    {"tool": "generate_security_report", "parameters": {"include_paths": True}},
                ],
            },
            {
                "name": "network_ssrf_testing",
                "description": "Test SSRF and network access controls",
                "steps": [
                    {"tool": "test_network_access", "parameters": {"url": "http://localhost:8080"}},
                    {"tool": "test_network_access", "parameters": {"url": "https://api.github.com"}},
                    {"tool": "scan_anomalies", "parameters": {"scan_type": "network"}},
                    {"tool": "generate_security_report", "parameters": {"include_anomalies": True}},
                ],
            },
            {
                "name": "comprehensive_assessment",
                "description": "Full security assessment workflow",
                "steps": [
                    {"tool": "test_filesystem_access", "parameters": {"path": "C:/blocked", "operation": "read"}},
                    {"tool": "test_network_access", "parameters": {"url": "http://192.168.1.1"}},
                    {"tool": "scan_anomalies", "parameters": {"scan_type": "connections"}},
                    {"tool": "generate_security_report", "parameters": {}},
                ],
            },
        ],
        "system_profile": {
            "allowed_paths": ["C:/Users/irfan", "e:/grid", "e:/grid/security"],
            "blocked_network_patterns": ["localhost", "127.0.0.1", "192.168.", "10.", "172.16-31."],
            "audit_events": ["AUTHZ_ACCESS_DENIED", "DATA_ACCESS_PERSONAL", "REQUEST_BLOCKED"],
            "users": ["system"],
        },
    }

    agent = GRIDSecurityAssessmentAgent(config)

    # Check command line arguments
    if len(sys.argv) > 1:
        flow_name = sys.argv[1]
        agent.run_flow(flow_name)
    else:
        print("\n🔒 GRID SECURITY ASSESSMENT AGENT - v1.0")
        print("----------------------------------------")
        print("Available security flows:")
        for flow in config["flows"]:
            print(f"  - {flow['name']}: {flow['description']}")
        print("\nUsage: python security/assessment_agent.py <flow_name>")
        print("Example: python security/assessment_agent.py comprehensive_assessment\n")


if __name__ == "__main__":
    main()
