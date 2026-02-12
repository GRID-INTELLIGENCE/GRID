#!/usr/bin/env python3
"""
Server Denylist Manager
Machine-readable server categorization and denylist enforcement system
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


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
    port: Optional[int] = None
    dependencies: List[str] = None
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
    name: Optional[str] = None
    pattern: Optional[str] = None
    match_attributes: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None
    notes: Optional[str] = None


class ServerDenylistManager:
    """Manages server denylisting with attribute-based rules"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.inventory = self._load_inventory()
        self.rules = self._load_rules()

    def _load_config(self) -> Dict:
        """Load denylist configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _load_inventory(self) -> List[ServerAttributes]:
        """Load server inventory"""
        inventory = []
        for server_data in self.config.get('serverInventory', []):
            inventory.append(ServerAttributes(
                name=server_data['name'],
                category=server_data['category'],
                command=server_data['command'],
                requires_network=server_data.get('requiresNetwork', False),
                requires_database=server_data.get('requiresDatabase', False),
                port=server_data.get('port'),
                dependencies=server_data.get('dependencies', []),
                resource_profile=server_data.get('resourceProfile', 'medium'),
                priority=server_data.get('priority', 5)
            ))
        return inventory

    def _load_rules(self) -> List[DenylistRule]:
        """Load denylist rules"""
        rules = []
        for rule_data in self.config.get('denylistRules', []):
            rules.append(DenylistRule(
                name=rule_data.get('name'),
                reason=rule_data['reason'],
                scope=rule_data['scope'],
                enabled=rule_data['enabled'],
                pattern=rule_data.get('pattern'),
                match_attributes=rule_data.get('matchAttributes'),
                expires_at=rule_data.get('expiresAt'),
                notes=rule_data.get('notes')
            ))
        return rules

    def _matches_pattern(self, server_name: str, pattern: Optional[str]) -> bool:
        """Check if server name matches pattern"""
        if not pattern:
            return False
        try:
            return bool(re.match(pattern, server_name))
        except re.error:
            return False

    def _matches_attributes(self, server: ServerAttributes, match_attrs: Optional[Dict]) -> bool:
        """Check if server matches attribute criteria"""
        if not match_attrs:
            return False

        # Check category match
        if 'category' in match_attrs:
            if server.category not in match_attrs['category']:
                return False

        # Check command pattern
        if 'commandPattern' in match_attrs:
            try:
                if not re.match(match_attrs['commandPattern'], server.command):
                    return False
            except re.error:
                pass

        # Check port range
        if 'portRange' in match_attrs and server.port:
            port_range = match_attrs['portRange']
            if not (port_range.get('min', 0) <= server.port <= port_range.get('max', 65535)):
                return False

        # Check network requirement
        if 'requiresNetwork' in match_attrs:
            if server.requires_network != match_attrs['requiresNetwork']:
                return False

        # Check resource profile
        if 'resourceProfile' in match_attrs:
            if server.resource_profile not in match_attrs['resourceProfile']:
                return False

        return True

    def is_denied(self, server_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if a server is denied
        Returns: (is_denied, reason)
        """
        server = self.get_server(server_name)
        if not server:
            return False, None

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check name match
            if rule.name and server_name == rule.name:
                return True, rule.reason

            # Check pattern match
            if self._matches_pattern(server_name, rule.pattern):
                if self._matches_attributes(server, rule.match_attributes):
                    return True, rule.reason

            # Check attribute match only
            if self._matches_attributes(server, rule.match_attributes):
                return True, rule.reason

        return False, None

    def get_server(self, name: str) -> Optional[ServerAttributes]:
        """Get server from inventory"""
        for server in self.inventory:
            if server.name == name:
                return server
        return None

    def get_denied_servers(self) -> List[tuple[str, str]]:
        """Get all denied servers with reasons"""
        denied = []
        for server in self.inventory:
            is_denied, reason = self.is_denied(server.name)
            if is_denied:
                denied.append((server.name, reason))
        return denied

    def get_allowed_servers(self) -> List[str]:
        """Get all allowed servers"""
        allowed = []
        for server in self.inventory:
            is_denied, _ = self.is_denied(server.name)
            if not is_denied:
                allowed.append(server.name)
        return allowed

    def apply_to_mcp_config(self, mcp_config_path: str, output_path: Optional[str] = None):
        """Apply denylist to MCP configuration"""
        mcp_path = Path(mcp_config_path)
        if not mcp_path.exists():
            raise FileNotFoundError(f"MCP config not found: {mcp_config_path}")

        with open(mcp_path, 'r') as f:
            mcp_config = json.load(f)

        # Disable denied servers
        for server in mcp_config.get('servers', []):
            server_name = server.get('name')
            is_denied, reason = self.is_denied(server_name)
            
            if is_denied:
                server['enabled'] = False
                server['_denylist_reason'] = reason
                print(f"✗ Disabled: {server_name} (Reason: {reason})")
            else:
                print(f"✓ Allowed: {server_name}")

        # Write output
        output = Path(output_path) if output_path else mcp_path
        with open(output, 'w') as f:
            json.dump(mcp_config, f, indent=2)

        print(f"\n✓ Applied denylist to: {output}")

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
            report.append(f"\n✗ {name}")
            report.append(f"  Reason: {reason}")
            report.append(f"  Category: {server.category}")
            report.append(f"  Command: {server.command}")
            report.append(f"  Port: {server.port}")
            report.append(f"  Resource Profile: {server.resource_profile}")

        report.append("\n" + "-" * 80)
        report.append("ALLOWED SERVERS")
        report.append("-" * 80)
        for name in allowed:
            server = self.get_server(name)
            report.append(f"\n✓ {name}")
            report.append(f"  Category: {server.category}")
            report.append(f"  Priority: {server.priority}")
            report.append(f"  Port: {server.port}")

        report.append("\n" + "=" * 80)
        return "\n".join(report)


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Server Denylist Manager")
    parser.add_argument('--config', required=True, help='Path to denylist config')
    parser.add_argument('--mcp-config', help='Path to MCP config to update')
    parser.add_argument('--output', help='Output path for modified MCP config')
    parser.add_argument('--report', action='store_true', help='Generate report')
    parser.add_argument('--check', help='Check if specific server is denied')

    args = parser.parse_args()

    manager = ServerDenylistManager(args.config)

    if args.report:
        print(manager.generate_report())

    if args.check:
        is_denied, reason = manager.is_denied(args.check)
        if is_denied:
            print(f"✗ {args.check} is DENIED")
            print(f"  Reason: {reason}")
        else:
            print(f"✓ {args.check} is ALLOWED")

    if args.mcp_config:
        manager.apply_to_mcp_config(args.mcp_config, args.output)


if __name__ == '__main__':
    main()
