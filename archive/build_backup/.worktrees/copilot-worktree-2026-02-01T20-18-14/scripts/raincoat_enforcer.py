#!/usr/bin/env python3
"""
Raincoat Stability Enforcer
Monitors and enforces stability profiles against VS Code settings patterns
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

class RaincoatEnforcer:
    def __init__(self, profile_path: str = "config/stability_profile.json"):
        self.profile_path = Path(profile_path)
        self.profile = self._load_profile()
        
    def _load_profile(self) -> Dict:
        if not self.profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {self.profile_path}")
        with open(self.profile_path, 'r') as f:
            return json.load(f)

    def generate_vscode_settings(self) -> str:
        """Generates the recommended VS Code settings block based on the profile"""
        gov = self.profile.get("governance", {})
        mcp = gov.get("mcp_systems", {})
        term = gov.get("terminal_safety", {})
        ai = gov.get("ai_assistance", {})
        prefs = self.profile.get("workflow_preferences", {})

        # Construct the settings object
        settings = {
            # Stability Core
            "chat.mcp.autostart": mcp.get("autostart_policy", "never"),
            "chat.mcp.gallery.enabled": mcp.get("gallery_enabled", True),
            
            # Workflow
            "chat.viewSessions.orientation": prefs.get("view_orientation", "stacked"),
            "chat.useAgentSkills": ai.get("agent_skills", True),
            "chat.restoreLastPanelSession": ai.get("restore_sessions", True),
            "claudeCode.preferredLocation": ai.get("preferred_location", "panel"),
            "terminal.integrated.fontFamily": prefs.get("font_family", "monospace"),
            
            # Terminal Safety (Raincoat Layer)
            "chat.tools.terminal.autoApprove": self._build_terminal_rules(term)
        }
        
        return json.dumps(settings, indent=2)

    def _build_terminal_rules(self, term_config: Dict) -> Dict:
        """Builds the explicit terminal auto-approve list"""
        rules = {}
        
        # Safe Read-Only Commands (Base Layer)
        safe_commands = [
            "ls", "pwd", "echo", "cat", "head", "tail", "grep", "findstr",
            "wc", "tr", "cut", "which", "basename", "dirname", "realpath",
            "stat", "file", "du", "df", "date", "sort", "tree"
        ]
        
        for cmd in safe_commands:
            rules[cmd] = True
            
        # Explicit Blocks (Raincoat Layer)
        blocked = term_config.get("blocked_commands", [])
        for cmd in blocked:
            rules[cmd] = False
            
        return rules

    def validate_settings(self, user_settings_path: str) -> List[str]:
        """Validates a user settings file against the profile"""
        violations = []
        # Implementation would go here to check actual files
        # For now we just define the interface
        return violations

def main():
    enforcer = RaincoatEnforcer()
    print("// RAINCOAT STABILITY CONFIGURATION")
    print("// Generated based on active stability profile")
    print(enforcer.generate_vscode_settings())

if __name__ == "__main__":
    main()
