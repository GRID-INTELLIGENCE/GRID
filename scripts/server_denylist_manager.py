#!/usr/bin/env python3
"""
Server Denylist Manager
Machine-readable server categorization and denylist enforcement system
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class DenylistReason(Enum):
    RESOURCE_INTENSIVE = "resource-intensive"
    NETWORK_DEPENDENT = "network-dependent"
    STARTUP_FAILURE = "startup-failure"
    MISSING_DEPENDENCIES = "missing-dependencies"
    SECURITY_CONCERN = "security-concern"
    DEPRECATED = "deprecated"
    REDUNDANT = "redundant"
    DEVELOPMENT_ONLY = "development-only"
    USER_DISABLED = "user-disabled"


class ServerCategory(Enum):
    WEB_BASED = "web-based"
    DATABASE = "database"
    MCP_SERVER = "mcp-server"
    RAG_SYSTEM = "rag-system"
    AGENTIC_WORKFLOW = "agentic-workflow"
    DEVELOPMENT_TOOLS = "development-tools"
    MEMORY_STORAGE = "memory-storage"
    API_GATEWAY = "api-gateway"
    BACKGROUND_SERVICE = "background-service"


@dataclass
class ServerAttributes:
    name: str
    category: str
    command: str
    requires_network: bool = False
    requires_database: bool = False
    port: int | None = None
    dependencies: list[str] | None = None
    resource_profile: str = "medium"
    priority: int = 5

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class DenylistRule:
    reason: str
    scope: str
    enabled: bool
    name: str | None = None
    pattern: str | None = None
    match_attributes: dict[str, Any] | None = None
    expires_at: str | None = None
    notes: str | None = None


class ServerDenylistManager:
    """Manages server denylisting with attribute-based rules"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.inventory = self._load_inventory()
        self.rules = self._load_rules()

    def _load_config(self) -> dict:
        """Load denylist configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path) as f:
            return json.load(f)

    def _load_inventory(self) -> list[ServerAttributes]:
        """Load server inventory"""
        inventory = []
        for server_data in self.config.get("serverInventory", []):
            inventory.append(
                ServerAttributes(
                    name=server_data["name"],
                    category=server_data["category"],
                    command=server_data["command"],
                    requires_network=server_data.get("requiresNetwork", False),
                    requires_database=server_data.get("requiresDatabase", False),
                    port=server_data.get("port"),
                    dependencies=server_data.get("dependencies", []),
                    resource_profile=server_data.get("resourceProfile", "medium"),
                    priority=server_data.get("priority", 5),
                )
            )
        return inventory

    def _load_rules(self) -> list[DenylistRule]:
        """Load denylist rules"""
        rules = []
        for rule_data in self.config.get("denylistRules", []):
            rules.append(
                DenylistRule(
                    name=rule_data.get("name"),
                    reason=rule_data["reason"],
                    scope=rule_data["scope"],
                    enabled=rule_data["enabled"],
                    pattern=rule_data.get("pattern"),
                    match_attributes=rule_data.get("matchAttributes"),
                    expires_at=rule_data.get("expiresAt"),
                    notes=rule_data.get("notes"),
                )
            )
        return rules

    def _matches_pattern(self, server_name: str, pattern: str | None) -> bool:
        """Check if server name matches pattern"""
        if not pattern:
            return False
        try:
            return bool(re.match(pattern, server_name))
        except re.error:
            return False

    def _normalize_list(self, value: Any) -> list[str]:
        """Normalize a value to a list of strings"""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)]

    def _matches_attributes(self, server: ServerAttributes, match_attrs: dict | None) -> bool:
        """Check if server matches attribute criteria"""
        if not match_attrs:
            return False

        # Check category match
        if "category" in match_attrs:
            if server.category not in match_attrs["category"]:
                return False

        # Check command pattern
        if "commandPattern" in match_attrs:
            try:
                if not re.match(match_attrs["commandPattern"], server.command):
                    return False
            except re.error:
                pass

        # Check port range
        if "portRange" in match_attrs and server.port:
            port_range = match_attrs["portRange"]
            if not (port_range.get("min", 0) <= server.port <= port_range.get("max", 65535)):
                return False

        # Check network requirement
        if "requiresNetwork" in match_attrs:
            if server.requires_network != match_attrs["requiresNetwork"]:
                return False

        # Check resource profile
        if "resourceProfile" in match_attrs:
            profiles = self._normalize_list(match_attrs["resourceProfile"])
            if server.resource_profile not in profiles:
                return False

        return True

    def _evaluate_rules(self, server: ServerAttributes) -> tuple[bool, str | None, str | None]:
        for rule in self.rules:
            if not rule.enabled:
                continue

            if self._matches_pattern(server.name, rule.pattern):
                if rule.match_attributes:
                    if self._matches_attributes(server, rule.match_attributes):
                        return True, rule.reason, rule.name or "unnamed-rule"
                else:
                    return True, rule.reason, rule.name or "unnamed-rule"

            if self._matches_attributes(server, rule.match_attributes):
                return True, rule.reason, rule.name or "unnamed-rule"

        return False, None, None

    def _build_server_from_entry(self, entry: dict[str, Any]) -> ServerAttributes | None:
        name = entry.get("name")
        if not name:
            return None

        inventory = self.get_server(name)
        if inventory:
            server = ServerAttributes(
                name=inventory.name,
                category=inventory.category,
                command=inventory.command,
                requires_network=inventory.requires_network,
                requires_database=inventory.requires_database,
                port=inventory.port,
                dependencies=list(inventory.dependencies or []),
                resource_profile=inventory.resource_profile,
                priority=inventory.priority,
            )
        else:
            server = ServerAttributes(
                name=name,
                category="mcp-server",
                command=entry.get("command", ""),
                requires_network=entry.get("requiresNetwork", False),
                requires_database=entry.get("requiresDatabase", False),
                port=entry.get("port"),
                dependencies=entry.get("dependencies", []),
                resource_profile=entry.get("resourceProfile", "medium"),
                priority=entry.get("priority", 5),
            )

        if entry.get("command"):
            server.command = entry["command"]
        if "requiresNetwork" in entry:
            server.requires_network = entry["requiresNetwork"]
        if "requiresDatabase" in entry:
            server.requires_database = entry["requiresDatabase"]
        if "resourceProfile" in entry:
            server.resource_profile = entry["resourceProfile"]
        if "port" in entry:
            server.port = entry["port"]

        if not server.category:
            server.category = "mcp-server"

        return server

    def is_denied(self, server_name: str) -> tuple[bool, str | None]:
        """
        Check if a server is denied
        Returns: (is_denied, reason)
        """
        server = self.get_server(server_name)
        if not server:
            return False, None

        is_denied, reason, _rule_name = self._evaluate_rules(server)
        return is_denied, reason

    def is_denied_server(self, server: ServerAttributes) -> tuple[bool, str | None, str | None]:
        return self._evaluate_rules(server)

    def get_mcp_violations(self, mcp_config_path: str) -> list[dict[str, str]]:
        mcp_path = Path(mcp_config_path)
        if not mcp_path.exists():
            raise FileNotFoundError(f"MCP config not found: {mcp_config_path}")

        with open(mcp_path) as f:
            mcp_config = json.load(f)

        violations: list[dict[str, str]] = []

        for entry in mcp_config.get("servers", []):
            enabled = entry.get("enabled", True)
            if not enabled:
                continue

            server = self._build_server_from_entry(entry)
            if not server:
                continue

            # For MCP validation, assume category of "mcp-server"
            server.category = "mcp-server"

            is_denied, reason, rule_name = self.is_denied_server(server)
            if is_denied:
                violations.append(
                    {
                        "server_name": server.name,
                        "reason": reason or "unknown",
                        "rule_name": rule_name or "unnamed-rule",
                    }
                )

        return violations

    def get_server(self, name: str) -> ServerAttributes | None:
        """Get server from inventory"""
        for server in self.inventory:
            if server.name == name:
                return server
        return None

    def get_denied_servers(self) -> list[tuple[str, str]]:
        """Get all denied servers with reasons"""
        denied = []
        for server in self.inventory:
            is_denied, reason = self.is_denied(server.name)
            if is_denied:
                denied.append((server.name, reason))
        return denied

    def get_allowed_servers(self) -> list[str]:
        """Get all allowed servers"""
        allowed = []
        for server in self.inventory:
            is_denied, _ = self.is_denied(server.name)
            if not is_denied:
                allowed.append(server.name)
        return allowed

    def _normalize_mcp_servers(self, mcp_config: Any) -> list[dict[str, Any]]:
        """Normalize MCP server entries from multiple schema variants"""
        servers: list[dict[str, Any]] = []

        def coerce_server_list(raw_servers: Any) -> list[dict[str, Any]]:
            if isinstance(raw_servers, list):
                return [dict(server) for server in raw_servers if isinstance(server, dict)]
            if isinstance(raw_servers, dict):
                normalized = []
                for name, server in raw_servers.items():
                    if isinstance(server, dict):
                        entry = dict(server)
                        entry.setdefault("name", name)
                        normalized.append(entry)
                return normalized
            return []

        if isinstance(mcp_config, dict):
            if "servers" in mcp_config:
                servers.extend(coerce_server_list(mcp_config.get("servers")))
            if "mcpServers" in mcp_config:
                servers.extend(coerce_server_list(mcp_config.get("mcpServers")))
        elif isinstance(mcp_config, list):
            servers.extend(coerce_server_list(mcp_config))

        return servers

    def validate_mcp_config(
        self, mcp_config_path: str, total_deny: bool = False
    ) -> tuple[list[dict[str, str]], list[str]]:
        """Validate MCP config against denylist rules without modifying files

        Args:
            mcp_config_path: Path to MCP configuration file
            total_deny: If True, treat ALL MCP servers as denied (total-deny scope)
        """
        mcp_path = Path(mcp_config_path)
        if not mcp_path.exists():
            raise FileNotFoundError(f"MCP config not found: {mcp_config_path}")

        with open(mcp_path) as f:
            mcp_config = json.load(f)

        violations: list[dict[str, str]] = []
        unknown_servers: list[str] = []

        for entry in self._normalize_mcp_servers(mcp_config):
            server_name = entry.get("name")
            if not server_name:
                continue

            enabled = entry.get("enabled", True)
            if not enabled:
                continue

            # Total-deny mode: ALL enabled MCP servers are violations
            if total_deny:
                violations.append(
                    {
                        "name": server_name,
                        "reason": "total-deny-scope",
                        "config_path": str(mcp_config_path),
                    }
                )
                continue

            server = self._build_server_from_entry(entry)
            if not server:
                continue

            is_denied, reason, _rule_name = self.is_denied_server(server)
            if is_denied:
                violations.append({"name": server.name, "reason": reason or "unknown"})
            elif not self.get_server(server.name):
                unknown_servers.append(server.name)

        return violations, unknown_servers

    def apply_to_mcp_config(self, mcp_config_path: str, output_path: str | None = None):
        """Apply denylist to MCP configuration"""
        mcp_path = Path(mcp_config_path)
        if not mcp_path.exists():
            raise FileNotFoundError(f"MCP config not found: {mcp_config_path}")

        with open(mcp_path) as f:
            mcp_config = json.load(f)

        # Disable denied servers (evaluate with MCP entry overrides when present)
        for entry in mcp_config.get("servers", []):
            server_name = entry.get("name")
            server = self._build_server_from_entry(entry) if server_name else None
            if not server:
                continue

            is_denied, reason, _rule_name = self.is_denied_server(server)

            if is_denied:
                entry["enabled"] = False
                entry["_denylist_reason"] = reason
                print(f"âœ— Disabled: {server_name} (Reason: {reason})")
            else:
                print(f"âœ“ Allowed: {server_name}")

        # Write output
        output = Path(output_path) if output_path else mcp_path
        with open(output, "w") as f:
            json.dump(mcp_config, f, indent=2)

        print(f"\nâœ“ Applied denylist to: {output}")

    def generate_report(self) -> str:
        """Generate denylist report"""
        denied = self.get_denied_servers()
        allowed = self.get_allowed_servers()

        report = []
        report.append("=" * 80)
        report.append("SERVER DENYLIST REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal Servers: {len(self.inventory)}")
        report.append(f"Denied: {len(denied)}")
        report.append(f"Allowed: {len(allowed)}")

        report.append("\n" + "-" * 80)
        report.append("DENIED SERVERS")
        report.append("-" * 80)
        for name, reason in denied:
            server = self.get_server(name)
            report.append(f"\nâœ— {name}")
            report.append(f"  Reason: {reason}")
            if server:
                report.append(f"  Category: {server.category}")
                report.append(f"  Command: {server.command}")
                report.append(f"  Port: {server.port}")
                report.append(f"  Resource Profile: {server.resource_profile}")
            else:
                report.append("  (Server not in inventory)")

        report.append("\n" + "-" * 80)
        report.append("ALLOWED SERVERS")
        report.append("-" * 80)
        for name in allowed:
            server = self.get_server(name)
            report.append(f"\nâœ“ {name}")
            if server:
                report.append(f"  Category: {server.category}")
                report.append(f"  Priority: {server.priority}")
                report.append(f"  Port: {server.port}")
            else:
                report.append("  (Server not in inventory)")

        report.append("\n" + "=" * 80)
        return "\n".join(report)


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Server Denylist Manager")
    parser.add_argument("--config", required=True, help="Path to denylist config")
    parser.add_argument("--mcp-config", help="Path to MCP config to update")
    parser.add_argument("--validate-config", help="Path to MCP config to validate (read-only)")
    parser.add_argument(
        "--total-deny",
        action="store_true",
        help="Total-deny mode: treat ALL enabled MCP servers as violations",
    )
    parser.add_argument("--output", help="Output path for modified MCP config")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--check", help="Check if specific server is denied")

    args = parser.parse_args()

    manager = ServerDenylistManager(args.config)

    if args.report:
        print(manager.generate_report())

    if args.check:
        is_denied, reason = manager.is_denied(args.check)
        if is_denied:
            print(f"âœ— {args.check} is DENIED")
            print(f"  Reason: {reason}")
        else:
            print(f"âœ“ {args.check} is ALLOWED")

    if args.validate_config:
        violations, unknown_servers = manager.validate_mcp_config(args.validate_config, total_deny=args.total_deny)
        if violations:
            mode_label = "TOTAL-DENY" if args.total_deny else "DENYLIST"
            print(f"[X] {mode_label} VIOLATION: Enabled servers in MCP config:")
            for violation in violations:
                reason = violation.get("reason", "unknown")
                print(f"  - {violation['name']} (Reason: {reason})")
            if unknown_servers:
                print("\n[!] Servers not found in inventory:")
                for name in sorted(set(unknown_servers)):
                    print(f"  - {name}")
            raise SystemExit(1)
        else:
            print("[OK] MCP config validated: no violations")
            if unknown_servers:
                print("\n[!] Servers not found in inventory:")
                for name in sorted(set(unknown_servers)):
                    print(f"  - {name}")

    if args.mcp_config:
        manager.apply_to_mcp_config(args.mcp_config, args.output)


if __name__ == "__main__":
    main()
