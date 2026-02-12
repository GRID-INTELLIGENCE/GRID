"""
Network Access Monitoring Dashboard
====================================
Real-time monitoring and analysis of network access attempts.
Provides CLI interface to view blocked/allowed requests and manage whitelist.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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


class NetworkMonitor:
    """Network access monitoring and management."""

    def __init__(self):
        self.base_path = Path(__file__).parent
        self.config_path = self.base_path / "network_access_control.yaml"
        self.audit_log_path = self.base_path / "logs" / "audit.log"
        self.console = Console() if RICH_AVAILABLE else None

    def load_config(self) -> Dict:
        """Load network access control configuration."""
        if not YAML_AVAILABLE or not self.config_path.exists():
            return {}

        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def save_config(self, config: Dict):
        """Save network access control configuration."""
        if not YAML_AVAILABLE:
            print("❌ pyyaml not installed, cannot save config")
            return

        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    def get_audit_events(
        self, limit: int = 100, event_type: Optional[str] = None
    ) -> List[Dict]:
        """Read audit log events."""
        if not self.audit_log_path.exists():
            return []

        events = []
        try:
            with open(self.audit_log_path, "r") as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if event_type is None or event.get("event_type") == event_type:
                            events.append(event)
        except Exception as e:
            print(f"Error reading audit log: {e}")

        return events[-limit:]

    def get_blocked_requests(self, limit: int = 50) -> List[Dict]:
        """Get recent blocked requests."""
        return self.get_audit_events(limit=limit, event_type="REQUEST_BLOCKED")

    def get_allowed_requests(self, limit: int = 50) -> List[Dict]:
        """Get recent allowed requests."""
        return self.get_audit_events(limit=limit, event_type="REQUEST_ALLOWED")

    def get_data_leaks(self) -> List[Dict]:
        """Get detected data leak attempts."""
        return self.get_audit_events(limit=1000, event_type="DATA_LEAK_BLOCKED")

    def get_statistics(self) -> Dict:
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

    def toggle_kill_switch(self, enable: bool):
        """Toggle emergency kill switch."""
        config = self.load_config()
        if "emergency" not in config:
            config["emergency"] = {}
        config["emergency"]["kill_switch"] = enable
        self.save_config(config)

        if enable:
            print("🚨 EMERGENCY KILL SWITCH ACTIVATED - ALL NETWORK ACCESS BLOCKED")
        else:
            print("✅ Emergency kill switch deactivated")


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

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
