"""
Network Access Monitoring Dashboard
====================================
Real-time monitoring and analysis of network access attempts.
Provides CLI interface to view blocked/allowed requests and manage whitelist.
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Install 'rich' for better UI: pip install rich")

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("⚠️  Install 'pyyaml' for config management: pip install pyyaml")

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  Install 'psutil' for connection monitoring: pip install psutil")


class NetworkMonitor:
    """Network access monitoring and management."""

    def __init__(self):
        self.base_path = Path(__file__).parent
        self.config_path = self.base_path / "network_access_control.yaml"
        self.audit_log_path = self.base_path / "logs" / "audit.log"
        self.console = Console() if RICH_AVAILABLE else None

    def load_config(self) -> dict:
        """Load network access control configuration."""
        if not YAML_AVAILABLE or not self.config_path.exists():
            return {}

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def save_config(self, config: dict):
        """Save network access control configuration."""
        if not YAML_AVAILABLE:
            print("❌ pyyaml not installed, cannot save config")
            return

        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    def get_audit_events(
        self, limit: int = 100, event_type: str | None = None
    ) -> list[dict]:
        """Read audit log events."""
        if not self.audit_log_path.exists():
            return []

        events = []
        try:
            with open(self.audit_log_path) as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if event_type is None or event.get("event_type") == event_type:
                            events.append(event)
        except Exception as e:
            print(f"Error reading audit log: {e}")

        return events[-limit:]

    def get_blocked_requests(self, limit: int = 50) -> list[dict]:
        """Get recent blocked requests."""
        return self.get_audit_events(limit=limit, event_type="REQUEST_BLOCKED")

    def get_allowed_requests(self, limit: int = 50) -> list[dict]:
        """Get recent allowed requests."""
        return self.get_audit_events(limit=limit, event_type="REQUEST_ALLOWED")

    def get_data_leaks(self) -> list[dict]:
        """Get detected data leak attempts."""
        return self.get_audit_events(limit=1000, event_type="DATA_LEAK_BLOCKED")

    def get_statistics(self) -> dict:
        """Calculate statistics from audit log."""
        all_events = self.get_audit_events(limit=10000)

        stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "allowed_requests": 0,
            "data_leaks_detected": 0,
            "unique_domains_blocked": set(),
            "unique_domains_allowed": set(),
            "top_blocked_domains": {},
            "top_blocked_callers": {},
        }

        for event in all_events:
            event_type = event.get("event_type")
            details = event.get("details", {})

            if event_type == "REQUEST_BLOCKED":
                stats["blocked_requests"] += 1
                stats["total_requests"] += 1
                domain = details.get("domain", "unknown")
                stats["unique_domains_blocked"].add(domain)
                stats["top_blocked_domains"][domain] = (
                    stats["top_blocked_domains"].get(domain, 0) + 1
                )

                caller = details.get("caller", "unknown")
                stats["top_blocked_callers"][caller] = (
                    stats["top_blocked_callers"].get(caller, 0) + 1
                )

            elif event_type == "REQUEST_ALLOWED":
                stats["allowed_requests"] += 1
                stats["total_requests"] += 1
                domain = details.get("domain", "unknown")
                stats["unique_domains_allowed"].add(domain)

            elif event_type == "DATA_LEAK_BLOCKED":
                stats["data_leaks_detected"] += 1

        stats["unique_domains_blocked"] = len(stats["unique_domains_blocked"])
        stats["unique_domains_allowed"] = len(stats["unique_domains_allowed"])

        # Sort top domains
        stats["top_blocked_domains"] = dict(
            sorted(
                stats["top_blocked_domains"].items(), key=lambda x: x[1], reverse=True
            )[:10]
        )
        stats["top_blocked_callers"] = dict(
            sorted(
                stats["top_blocked_callers"].items(), key=lambda x: x[1], reverse=True
            )[:10]
        )

        return stats

    def print_dashboard(self):
        """Print monitoring dashboard."""
        if not RICH_AVAILABLE:
            self._print_simple_dashboard()
            return

        stats = self.get_statistics()
        config = self.load_config()
        blocked = self.get_blocked_requests(limit=10)
        allowed = self.get_allowed_requests(limit=10)
        leaks = self.get_data_leaks()

        # Create layout
        console = self.console
        console.clear()

        # Header
        console.print(
            Panel.fit(
                "[bold red]🔒 NETWORK ACCESS CONTROL MONITOR[/bold red]\n"
                f"[yellow]Mode: {config.get('mode', 'unknown').upper()} | "
                f"Policy: {config.get('default_policy', 'unknown').upper()}[/yellow]",
                border_style="red",
            )
        )

        # Statistics
        stats_table = Table(
            title="📊 Statistics", show_header=True, header_style="bold magenta"
        )
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green", justify="right")

        stats_table.add_row("Total Requests", str(stats["total_requests"]))
        stats_table.add_row("✅ Allowed", str(stats["allowed_requests"]))
        stats_table.add_row("🚫 Blocked", str(stats["blocked_requests"]))
        stats_table.add_row("🚨 Data Leaks", str(stats["data_leaks_detected"]))
        stats_table.add_row(
            "Unique Domains (Blocked)", str(stats["unique_domains_blocked"])
        )
        stats_table.add_row(
            "Unique Domains (Allowed)", str(stats["unique_domains_allowed"])
        )

        console.print(stats_table)
        console.print()

        # Recent blocked requests
        if blocked:
            blocked_table = Table(title="🚫 Recent Blocked Requests", show_header=True)
            blocked_table.add_column("Time", style="dim")
            blocked_table.add_column("Method", style="yellow")
            blocked_table.add_column("Domain", style="red")
            blocked_table.add_column("Reason", style="cyan")

            for req in blocked[-10:]:
                details = req.get("details", {})
                timestamp = req.get("timestamp", "")[:19]
                method = details.get("method", "?")
                domain = details.get("domain", "unknown")[:40]
                reason = details.get("reason", "unknown")[:50]
                blocked_table.add_row(timestamp, method, domain, reason)

            console.print(blocked_table)
            console.print()

        # Top blocked domains
        if stats["top_blocked_domains"]:
            top_domains_table = Table(title="🎯 Top Blocked Domains", show_header=True)
            top_domains_table.add_column("Domain", style="red")
            top_domains_table.add_column("Count", style="yellow", justify="right")

            for domain, count in list(stats["top_blocked_domains"].items())[:10]:
                top_domains_table.add_row(domain[:50], str(count))

            console.print(top_domains_table)
            console.print()

        # Top blocked callers
        if stats["top_blocked_callers"]:
            callers_table = Table(title="📞 Top Blocked Callers", show_header=True)
            callers_table.add_column("Caller", style="cyan")
            callers_table.add_column("Count", style="yellow", justify="right")

            for caller, count in list(stats["top_blocked_callers"].items())[:10]:
                callers_table.add_row(caller[:60], str(count))

            console.print(callers_table)
            console.print()

        # Data leaks
        if leaks:
            console.print(
                Panel.fit(
                    f"[bold red]🚨 {len(leaks)} DATA LEAK ATTEMPTS DETECTED![/bold red]",
                    border_style="red",
                )
            )
            console.print()

        # Config summary
        global_config = config.get("global", {})
        emergency = config.get("emergency", {})

        config_text = Text()
        config_text.append("⚙️  Configuration:\n", style="bold")
        config_text.append(
            f"  Network Enabled: {global_config.get('network_enabled', False)}\n"
        )
        config_text.append(f"  Kill Switch: {emergency.get('kill_switch', False)}\n")
        config_text.append(
            f"  Localhost Only: {emergency.get('localhost_only', True)}\n"
        )

        console.print(Panel(config_text, border_style="blue"))

    def _print_simple_dashboard(self):
        """Print simple text dashboard without rich."""
        stats = self.get_statistics()
        blocked = self.get_blocked_requests(limit=10)
        config = self.load_config()

        print("=" * 80)
        print("🔒 NETWORK ACCESS CONTROL MONITOR")
        print("=" * 80)
        print(
            f"Mode: {config.get('mode', 'unknown').upper()} | Policy: {config.get('default_policy', 'unknown').upper()}"
        )
        print()

        print("📊 STATISTICS:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  ✅ Allowed: {stats['allowed_requests']}")
        print(f"  🚫 Blocked: {stats['blocked_requests']}")
        print(f"  🚨 Data Leaks: {stats['data_leaks_detected']}")
        print()

        if blocked:
            print("🚫 RECENT BLOCKED REQUESTS:")
            for req in blocked[-10:]:
                details = req.get("details", {})
                timestamp = req.get("timestamp", "")[:19]
                method = details.get("method", "?")
                domain = details.get("domain", "unknown")
                print(f"  [{timestamp}] {method} {domain}")
            print()

        if stats["top_blocked_domains"]:
            print("🎯 TOP BLOCKED DOMAINS:")
            for domain, count in list(stats["top_blocked_domains"].items())[:5]:
                print(f"  {domain}: {count}")
            print()

        print("=" * 80)

    def whitelist_domain(self, domain: str, description: str = ""):
        """Add domain to whitelist."""
        config = self.load_config()

        if "whitelist" not in config:
            config["whitelist"] = {"rules": []}

        # Check if already whitelisted
        for rule in config["whitelist"]["rules"]:
            if rule.get("domain") == domain:
                print(f"⚠️  Domain {domain} is already whitelisted")
                return

        # Add to whitelist
        rule = {
            "domain": domain,
            "protocol": "https",
            "description": description
            or f"Added via monitor at {datetime.utcnow().isoformat()}",
            "added_by": "monitor",
            "added_date": datetime.utcnow().isoformat(),
        }

        config["whitelist"]["rules"].append(rule)
        self.save_config(config)

        print(f"✅ Added {domain} to whitelist")

    def remove_from_whitelist(self, domain: str):
        """Remove domain from whitelist."""
        config = self.load_config()

        if "whitelist" not in config:
            print("❌ No whitelist found")
            return

        original_count = len(config["whitelist"]["rules"])
        config["whitelist"]["rules"] = [
            rule
            for rule in config["whitelist"]["rules"]
            if rule.get("domain") != domain
        ]

        if len(config["whitelist"]["rules"]) < original_count:
            self.save_config(config)
            print(f"✅ Removed {domain} from whitelist")
        else:
            print(f"⚠️  Domain {domain} not found in whitelist")

    def show_whitelist(self):
        """Display current whitelist."""
        config = self.load_config()
        rules = config.get("whitelist", {}).get("rules", [])

        if not rules:
            print("📝 Whitelist is empty")
            return

        print("📝 WHITELISTED DOMAINS:")
        for i, rule in enumerate(rules, 1):
            domain = rule.get("domain", "unknown")
            description = rule.get("description", "")
            added_date = rule.get("added_date", "")[:10]
            print(f"  {i}. {domain}")
            print(f"     Description: {description}")
            print(f"     Added: {added_date}")
            print()

    def enable_network(self):
        """Enable global network access."""
        config = self.load_config()
        if "global" not in config:
            config["global"] = {}
        config["global"]["network_enabled"] = True
        self.save_config(config)
        print("✅ Global network access ENABLED")

    def disable_network(self):
        """Disable global network access."""
        config = self.load_config()
        if "global" not in config:
            config["global"] = {}
        config["global"]["network_enabled"] = False
        self.save_config(config)
        print("🚫 Global network access DISABLED")

    def detect_anomalies(self, hours: int = 24) -> dict[str, Any]:
        """Detect network access anomalies in the last N hours."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=hours)
        all_events = self.get_audit_events(limit=10000)

        # Filter events within time window
        recent_events = [
            event for event in all_events
            if datetime.fromisoformat(event['timestamp']) > cutoff
        ]

        anomalies = {
            'time_window_hours': hours,
            'total_events': len(recent_events),
            'alerts': [],
            'blocked_rate': 0,
            'unusual_patterns': []
        }

        if not recent_events:
            return anomalies

        # Calculate blocked request rate
        blocked_events = [e for e in recent_events if e.get('event_type') == 'REQUEST_BLOCKED']
        anomalies['blocked_rate'] = len(blocked_events) / hours  # per hour

        # Alert thresholds
        if anomalies['blocked_rate'] > 10:  # More than 10 blocked requests per hour
            anomalies['alerts'].append({
                'level': 'HIGH',
                'message': f'High blocked request rate: {anomalies["blocked_rate"]:.1f} per hour',
                'recommendation': 'Review network access patterns and potential attack'
            })

        # Check for unusual domains
        blocked_domains = {}
        for event in blocked_events:
            domain = event.get('details', {}).get('domain', 'unknown')
            blocked_domains[domain] = blocked_domains.get(domain, 0) + 1

        for domain, count in blocked_domains.items():
            if count > 5:  # Same domain blocked more than 5 times
                anomalies['alerts'].append({
                    'level': 'MEDIUM',
                    'message': f'Domain {domain} blocked {count} times in {hours} hours',
                    'recommendation': 'Check if legitimate traffic or persistent attack'
                })

        # Check for rapid successive blocks
        timestamps = [datetime.fromisoformat(e['timestamp']) for e in blocked_events]
        if len(timestamps) > 1:
            intervals = [(timestamps[i+1] - timestamps[i]).seconds for i in range(len(timestamps)-1)]
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            if avg_interval < 60 and len(blocked_events) > 3:  # Less than 1 min between blocks
                anomalies['alerts'].append({
                    'level': 'HIGH',
                    'message': f'Rapid blocking pattern detected: {len(blocked_events)} blocks in short succession',
                    'recommendation': 'Potential automated attack or misconfiguration'
                })

        # Check for connection anomalies
        connection_anomalies = self.detect_connection_anomalies()
        anomalies['connection_anomalies'] = connection_anomalies
        if connection_anomalies:
            anomalies['alerts'].append({
                'level': 'MEDIUM',
                'message': f'Connection anomalies detected: {len(connection_anomalies)} issues',
                'details': connection_anomalies,
                'recommendation': 'Review active network connections for unauthorized access'
            })

        return anomalies

    def detect_connection_anomalies(self) -> list[str]:
        """Detect anomalies in active network connections using psutil."""
        if not PSUTIL_AVAILABLE:
            return ["psutil not available for connection monitoring"]

        try:
            connections = psutil.net_connections()
            anomalies = []
            standard_ports = {21, 22, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 8080, 8443}

            for conn in connections:
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    ip, port = conn.raddr
                    # Flag non-standard ports
                    if port not in standard_ports and port > 1024:  # Allow privileged ports but flag high non-standard
                        anomalies.append(f"Non-standard port connection: {ip}:{port}")
                    # Flag connections to private IPs (potential internal scanning)
                    if ip.startswith(('192.168.', '10.', '172.')):
                        anomalies.append(f"Private network connection: {ip}:{port}")
                    # Flag localhost connections that might indicate SSRF
                    if ip in ('127.0.0.1', '::1', 'localhost'):
                        anomalies.append(f"Localhost connection: {ip}:{port}")

            return anomalies
        except Exception as e:
            return [f"Error scanning connections: {str(e)}"]

    def log_alert(self, alert: dict[str, str]):
        """Log security alert to alerts.log."""
        alert_path = self.base_path / "logs" / "alerts.log"
        alert_path.parent.mkdir(exist_ok=True)

        alert_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': alert['level'],
            'message': alert['message'],
            'recommendation': alert['recommendation']
        }

        with open(alert_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(alert_entry) + '\n')

    def generate_forensic_report(self, hours: int = 24) -> str:
        """Generate comprehensive forensic report."""
        anomalies = self.detect_anomalies(hours)
        stats = self.get_statistics()
        blocked = self.get_blocked_requests(limit=100)
        allowed = self.get_allowed_requests(limit=100)

        report = []
        report.append("# Network Forensic Analysis Report")
        report.append(f"**Generated:** {datetime.now().isoformat()}")
        report.append(f"**Analysis Window:** {hours} hours")
        report.append("")

        # Summary
        report.append("## Summary")
        report.append(f"- Total events analyzed: {anomalies['total_events']}")
        report.append(f"- Blocked requests: {len([e for e in blocked if datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(hours=hours)])}")
        report.append(".1f")
        report.append("")

        # Alerts
        if anomalies['alerts']:
            report.append("## Security Alerts")
            for alert in anomalies['alerts']:
                report.append(f"- **{alert['level']}**: {alert['message']}")
                report.append(f"  *Recommendation:* {alert['recommendation']}")
            report.append("")
        else:
            report.append("## Security Alerts")
            report.append("No anomalies detected.")
            report.append("")

        # Statistics
        report.append("## Statistics")
        report.append(f"- Total requests: {stats['total_requests']}")
        report.append(f"- Blocked: {stats['blocked_requests']}")
        report.append(f"- Allowed: {stats['allowed_requests']}")
        report.append(f"- Data leaks detected: {stats['data_leaks_detected']}")
        report.append("")

        # Top blocked domains
        if stats['top_blocked_domains']:
            report.append("## Top Blocked Domains")
            for domain, count in list(stats['top_blocked_domains'].items())[:10]:
                report.append(f"- {domain}: {count}")
            report.append("")

        # Recent blocked requests
        if blocked:
            report.append("## Recent Blocked Requests")
            for req in blocked[-10:]:
                details = req.get('details', {})
                timestamp = req.get('timestamp', '')[:19]
                method = details.get('method', '?')
                domain = details.get('domain', 'unknown')
                reason = details.get('reason', 'unknown')
                report.append(f"- {timestamp}: {method} {domain} ({reason})")
            report.append("")

        return "\n".join(report)


def main():
    """Main CLI interface."""
    monitor = NetworkMonitor()

    if len(sys.argv) < 2:
        print("Network Access Control Monitor")
        print()
        print("Usage:")
        print(
            "  python monitor_network.py dashboard          - Show monitoring dashboard"
        )
        print("  python monitor_network.py blocked            - Show blocked requests")
        print("  python monitor_network.py allowed            - Show allowed requests")
        print(
            "  python monitor_network.py leaks              - Show data leak attempts"
        )
        print("  python monitor_network.py stats              - Show statistics")
        print("  python monitor_network.py whitelist          - Show whitelist")
        print(
            "  python monitor_network.py add <domain>       - Add domain to whitelist"
        )
        print("  python monitor_network.py remove <domain>    - Remove from whitelist")
        print("  python monitor_network.py enable             - Enable network access")
        print("  python monitor_network.py disable            - Disable network access")
        print(
            "  python monitor_network.py killswitch on/off  - Toggle emergency kill switch"
        )
        print("  python monitor_network.py anomalies [hours]  - Detect anomalies (default 24h)")
        print("  python monitor_network.py alerts             - Show recent alerts")
        print("  python monitor_network.py forensic [hours]   - Generate forensic report (default 24h)")
        print()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "dashboard":
        monitor.print_dashboard()

    elif command == "blocked":
        blocked = monitor.get_blocked_requests(limit=50)
        print(f"🚫 BLOCKED REQUESTS ({len(blocked)}):")
        print()
        for req in blocked:
            details = req.get("details", {})
            timestamp = req.get("timestamp", "")
            method = details.get("method", "?")
            url = details.get("url", "unknown")
            reason = details.get("reason", "unknown")
            print(f"[{timestamp}]")
            print(f"  {method} {url}")
            print(f"  Reason: {reason}")
            print()

    elif command == "allowed":
        allowed = monitor.get_allowed_requests(limit=50)
        print(f"✅ ALLOWED REQUESTS ({len(allowed)}):")
        print()
        for req in allowed:
            details = req.get("details", {})
            timestamp = req.get("timestamp", "")
            method = details.get("method", "?")
            url = details.get("url", "unknown")
            reason = details.get("reason", "unknown")
            print(f"[{timestamp}]")
            print(f"  {method} {url}")
            print(f"  Reason: {reason}")
            print()

    elif command == "leaks":
        leaks = monitor.get_data_leaks()
        print(f"🚨 DATA LEAK ATTEMPTS DETECTED ({len(leaks)}):")
        print()
        for leak in leaks:
            details = leak.get("details", {})
            timestamp = leak.get("timestamp", "")
            url = details.get("url", "unknown")
            print(f"[{timestamp}]")
            print(f"  URL: {url}")
            print()

    elif command == "stats":
        stats = monitor.get_statistics()
        print("📊 STATISTICS:")
        print()
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Allowed: {stats['allowed_requests']}")
        print(f"Blocked: {stats['blocked_requests']}")
        print(f"Data Leaks: {stats['data_leaks_detected']}")
        print(f"Unique Domains Blocked: {stats['unique_domains_blocked']}")
        print(f"Unique Domains Allowed: {stats['unique_domains_allowed']}")
        print()

        if stats["top_blocked_domains"]:
            print("Top Blocked Domains:")
            for domain, count in stats["top_blocked_domains"].items():
                print(f"  {domain}: {count}")
            print()

        if stats["top_blocked_callers"]:
            print("Top Blocked Callers:")
            for caller, count in stats["top_blocked_callers"].items():
                print(f"  {caller}: {count}")

    elif command == "whitelist":
        monitor.show_whitelist()

    elif command == "add":
        if len(sys.argv) < 3:
            print("❌ Usage: python monitor_network.py add <domain>")
            sys.exit(1)
        domain = sys.argv[2]
        description = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        monitor.whitelist_domain(domain, description)

    elif command == "remove":
        if len(sys.argv) < 3:
            print("❌ Usage: python monitor_network.py remove <domain>")
            sys.exit(1)
        domain = sys.argv[2]
        monitor.remove_from_whitelist(domain)

    elif command == "enable":
        monitor.enable_network()

    elif command == "disable":
        monitor.disable_network()

    elif command == "killswitch":
        if len(sys.argv) < 3:
            print("❌ Usage: python monitor_network.py killswitch on/off")
            sys.exit(1)
        enable = sys.argv[2].lower() in ["on", "true", "1", "yes"]
        monitor.toggle_kill_switch(enable)

    elif command == "anomalies":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        anomalies = monitor.detect_anomalies(hours)
        print(f"🔍 ANOMALY DETECTION (last {hours} hours):")
        print()
        print(f"Total events: {anomalies['total_events']}")
        print(".1f")
        print()

        if anomalies['alerts']:
            print("🚨 ALERTS DETECTED:")
            for alert in anomalies['alerts']:
                print(f"  [{alert['level']}] {alert['message']}")
                print(f"  💡 {alert['recommendation']}")
                print()
        else:
            print("✅ No anomalies detected.")

    elif command == "alerts":
        alert_path = monitor.base_path / "logs" / "alerts.log"
        if not alert_path.exists():
            print("📝 No alerts logged yet.")
            return

        print("🚨 RECENT ALERTS:")
        print()
        try:
            with open(alert_path, encoding='utf-8') as f:
                alerts = [json.loads(line) for line in f if line.strip()]
                for alert in alerts[-10:]:  # Show last 10
                    print(f"[{alert['timestamp'][:19]}] [{alert['level']}] {alert['message']}")
                    print(f"  💡 {alert['recommendation']}")
                    print()
        except Exception as e:
            print(f"Error reading alerts: {e}")

    elif command == "forensic":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        report = monitor.generate_forensic_report(hours)
        report_file = monitor.base_path / "logs" / f"forensic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📋 Forensic report saved to: {report_file}")
        print()
        print("Report Summary:")
        lines = report.split('\n')[:20]  # First 20 lines
        for line in lines:
            print(line)

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
