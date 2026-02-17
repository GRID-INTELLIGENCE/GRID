"""
GUARDIAN - Dynamic Rule Loader
Project GUARDIAN: Phase 1 - Dynamic Rule Loading and Hot-Reload

Loads safety rules from YAML/JSON files with hot-reload capability.
Supports versioning, validation, and atomic updates.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

from .engine import (
    GuardianEngine,
    MatchType,
    RuleAction,
    SafetyRule,
    Severity,
    get_guardian_engine,
)

logger = logging.getLogger(__name__)

# Try to import YAML
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class RuleValidationError(Exception):
    """Raised when rule validation fails."""

    pass


class RuleLoader:
    """
    Dynamic rule loader with hot-reload capability.

    Monitors rule files for changes and automatically reloads.
    Supports both YAML and JSON formats.
    """

    def __init__(self, rules_dir: str | None = None, auto_reload: bool = False):
        self.rules_dir = Path(rules_dir or os.getenv("GUARDIAN_RULES_DIR", "config/rules"))
        self.rules_dir.mkdir(parents=True, exist_ok=True)

        self._auto_reload = auto_reload
        self._reload_interval = int(os.getenv("GUARDIAN_RELOAD_INTERVAL", "60"))
        self._file_timestamps: dict[str, float] = {}
        self._rules_cache: dict[str, SafetyRule] = {}

        self._reload_thread: threading.Thread | None = None
        self._stop_reload = threading.Event()

    def load_from_file(self, filepath: str | Path) -> list[SafetyRule]:
        """
        Load rules from a single file.

        Args:
            filepath: Path to YAML or JSON file

        Returns:
            List of SafetyRule objects

        Raises:
            RuleValidationError: If validation fails
        """
        filepath = Path(filepath)

        if not filepath.exists():
            logger.error(f"Rule file not found: {filepath}")
            return []

        try:
            with open(filepath, encoding="utf-8") as f:
                if filepath.suffix.lower() in (".yaml", ".yml"):
                    if not YAML_AVAILABLE:
                        raise RuleValidationError("YAML support not available. Install PyYAML.")
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse {filepath}: {e}")
            raise RuleValidationError(f"Parse error in {filepath}: {e}")

        # Extract rules from data
        if isinstance(data, dict) and "rules" in data:
            rules_data = data["rules"]
            metadata = {k: v for k, v in data.items() if k != "rules"}
        elif isinstance(data, list):
            rules_data = data
            metadata = {}
        else:
            raise RuleValidationError(f"Invalid rule file format: {filepath}")

        rules = []
        for idx, rule_data in enumerate(rules_data):
            try:
                rule = self._parse_rule(rule_data, metadata)
                rules.append(rule)
            except Exception as e:
                logger.error(f"Failed to parse rule {idx} in {filepath}: {e}")
                continue

        logger.info(f"Loaded {len(rules)} rules from {filepath}")
        return rules

    def load_all_rules(self) -> list[SafetyRule]:
        """
        Load all rules from known directories.

        Returns:
            Combined list of all SafetyRule objects
        """
        all_rules = []

        # Load built-in default rules
        default_rules = self._get_default_rules()
        all_rules.extend(default_rules)

        # Directories to scan
        search_dirs = [self.rules_dir, Path("safety/rules")]

        for s_dir in search_dirs:
            if s_dir.exists():
                for filepath in sorted(s_dir.glob("*")):
                    if filepath.suffix.lower() in (".yaml", ".yml", ".json"):
                        # Skip registry-lock or other non-rule files if needed
                        if filepath.name in (".gitkeep", "README.md"):
                            continue
                        try:
                            rules = self.load_from_file(filepath)
                            all_rules.extend(rules)
                            self._file_timestamps[str(filepath)] = filepath.stat().st_mtime
                        except Exception as e:
                            logger.error(f"Failed to load {filepath}: {e}")

        logger.info(f"Total rules loaded: {len(all_rules)}")
        return all_rules

    def _parse_rule(self, data: dict[str, Any], metadata: dict[str, Any]) -> SafetyRule:
        """
        Parse a single rule from dictionary data.

        Args:
            data: Rule data dictionary
            metadata: File-level metadata

        Returns:
            SafetyRule object

        Raises:
            RuleValidationError: If validation fails
        """
        # Required fields
        if "id" not in data:
            raise RuleValidationError("Rule missing required 'id' field")
        if "name" not in data:
            raise RuleValidationError(f"Rule {data.get('id', 'unknown')} missing required 'name' field")

        # Parse severity
        severity_str = data.get("severity", "medium").lower()
        try:
            severity = Severity(severity_str)
        except ValueError:
            raise RuleValidationError(f"Invalid severity: {severity_str}")

        # Parse action
        action_str = data.get("action", "block").lower()
        try:
            action = RuleAction(action_str)
        except ValueError:
            raise RuleValidationError(f"Invalid action: {action_str}")

        # Parse match type
        match_type_str = data.get("match_type")
        if not match_type_str:
            if "patterns" in data or "pattern" in data:
                match_type = MatchType.REGEX
            else:
                match_type = MatchType.KEYWORD
        else:
            try:
                match_type = MatchType[match_type_str.upper()]
            except KeyError:
                raise RuleValidationError(f"Invalid match_type: {match_type_str}")

        # Validate match criteria
        if match_type == MatchType.KEYWORD and not data.get("keywords"):
            raise RuleValidationError(f"KEYWORD rule {data['id']} must have 'keywords'")
        if match_type == MatchType.REGEX and not data.get("patterns") and not data.get("pattern"):
            raise RuleValidationError(f"REGEX rule {data['id']} must have 'patterns' or 'pattern'")

        return SafetyRule(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "general"),
            severity=severity,
            action=action,
            match_type=match_type,
            keywords=data.get("keywords", []),
            patterns=data.get("patterns", [data.get("pattern")] if "pattern" in data else []),
            composite_rules=data.get("composite_rules", []),
            confidence=float(data.get("confidence", 0.8)),
            case_sensitive=bool(data.get("case_sensitive", False)),
            enabled=bool(data.get("enabled", True)),
            priority=int(data.get("priority", 100)),
            version=data.get("version", metadata.get("version", "1.0.0")),
            created_at=data.get("created_at", metadata.get("created_at")) or "",
            updated_at=data.get("updated_at", metadata.get("updated_at")) or "",
            author=data.get("author", metadata.get("author", "system")),
            tags=data.get("tags", []),
            cache_results=bool(data.get("cache_results", False)),
            max_matches=int(data.get("max_matches", 10)),
        )

    def _get_default_rules(self) -> list[SafetyRule]:
        """Get built-in default rules (copied from pre_check.py)."""
        return [
            # Weapons / explosives
            SafetyRule(
                id="high_risk_weapon",
                name="Weapon Creation",
                description="Detects attempts to create weapons or explosives",
                category="weapons",
                severity=Severity.CRITICAL,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[
                    r"(how\s+to\s+|instructions?\s+(for|to)\s+|steps?\s+to\s+|explain\s+how\s+to\s+)?(make|build|construct|create|assemble|making)\s+(a\s+|an\s+)?(pipe\s+)?(bomb|explosive|detonator|ied)"
                ],
                confidence=0.95,
                priority=10,
                tags=["weapon", "explosive", "critical"],
            ),
            # Chemical weapons
            SafetyRule(
                id="high_risk_chem_weapon",
                name="Chemical Weapons",
                description="Detects attempts to create chemical weapons",
                category="weapons",
                severity=Severity.CRITICAL,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[
                    r"(synthesize|manufacture|create|make)\s+(a\s+)?(nerve\s+agent|chemical\s+weapon|sarin|vx\s+gas)"
                ],
                confidence=0.95,
                priority=10,
                tags=["chemical", "weapon", "critical"],
            ),
            # Biological threats
            SafetyRule(
                id="high_risk_bio",
                name="Biological Threats",
                description="Detects attempts to create biological weapons",
                category="biological",
                severity=Severity.CRITICAL,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[
                    r"(how\s+to\s+)?(make|create|synthesize|engineer)\s+(a\s+)?(virus|pathogen|bioweapon|toxin|anthrax)",
                    r"(gain.of.function|enhance\s+transmissibility|weaponize\s+(bacteria|virus))",
                ],
                confidence=0.95,
                priority=10,
                tags=["biological", "weapon", "critical"],
            ),
            # CSAM
            SafetyRule(
                id="csam_block",
                name="CSAM Content",
                description="Detects child exploitation content",
                category="csam",
                severity=Severity.CRITICAL,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[r"(child|minor|underage)\s+(exploitation|pornograph|sexual|abuse)"],
                confidence=0.99,
                priority=1,
                tags=["csam", "exploitation", "critical"],
            ),
            # Jailbreak patterns
            SafetyRule(
                id="exploit_jailbreak_ignore",
                name="Jailbreak: Ignore Instructions",
                description="Detects jailbreak attempts using ignore instructions",
                category="jailbreak",
                severity=Severity.HIGH,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[r"(ignore\s+(previous|all|prior)\s+(instructions?|rules?))"],
                confidence=0.90,
                priority=20,
                tags=["jailbreak", "prompt_injection"],
            ),
            SafetyRule(
                id="exploit_jailbreak_persona",
                name="Jailbreak: Persona Switch",
                description="Detects jailbreak attempts using persona switching",
                category="jailbreak",
                severity=Severity.HIGH,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[
                    r"(you\s+are\s+now\s+|pretend\s+you\s+are\s+|act\s+as\s+)(an?\s+)?(unrestricted|evil|unfiltered|jailbroken)"
                ],
                confidence=0.90,
                priority=20,
                tags=["jailbreak", "persona"],
            ),
            SafetyRule(
                id="exploit_jailbreak_dan",
                name="Jailbreak: DAN Mode",
                description="Detects DAN (Do Anything Now) jailbreak attempts",
                category="jailbreak",
                severity=Severity.HIGH,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[r"(DAN|do\s+anything\s+now)\s+(mode|prompt|jailbreak)"],
                confidence=0.90,
                priority=20,
                tags=["jailbreak", "dan"],
            ),
            # Self-harm
            SafetyRule(
                id="high_risk_self_harm_method",
                name="Self-Harm Methods",
                description="Detects requests for self-harm methods",
                category="self_harm",
                severity=Severity.HIGH,
                action=RuleAction.ESCALATE,
                match_type=MatchType.REGEX,
                patterns=[
                    r"(how\s+to\s+)(commit\s+suicide|kill\s+(myself|yourself)|self.harm)",
                    r"(methods?\s+of\s+|ways?\s+to\s+)(self.harm|suicide|killing\s+(myself|yourself))",
                ],
                confidence=0.92,
                priority=15,
                tags=["self_harm", "mental_health"],
            ),
            # Cyber attacks
            SafetyRule(
                id="high_risk_cyber_malware",
                name="Malware Creation",
                description="Detects requests to create malware",
                category="cyber",
                severity=Severity.CRITICAL,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[r"(write|create|generate)\s+(a\s+)?(ransomware|malware|keylogger|rootkit|exploit\s+code)"],
                confidence=0.92,
                priority=15,
                tags=["cyber", "malware"],
            ),
            SafetyRule(
                id="high_risk_cyber_attack",
                name="Cyber Attack Instructions",
                description="Detects requests for attack instructions",
                category="cyber",
                severity=Severity.HIGH,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[r"(sql\s+injection|xss\s+payload|remote\s+code\s+execution)\s+(script|attack|exploit)"],
                confidence=0.90,
                priority=20,
                tags=["cyber", "attack"],
            ),
            # Input validation
            SafetyRule(
                id="input_too_long",
                name="Input Too Long",
                description="Detects excessively long inputs",
                category="validation",
                severity=Severity.MEDIUM,
                action=RuleAction.BLOCK,
                match_type=MatchType.KEYWORD,
                keywords=[],  # Handled programmatically
                confidence=1.0,
                priority=5,
                tags=["validation"],
            ),
            SafetyRule(
                id="high_entropy_payload",
                name="High Entropy Payload",
                description="Detects obfuscated or encoded payloads",
                category="validation",
                severity=Severity.HIGH,
                action=RuleAction.BLOCK,
                match_type=MatchType.KEYWORD,
                keywords=[],  # Handled programmatically
                confidence=0.85,
                priority=30,
                tags=["validation", "obfuscation"],
            ),
            # Mental Health / Support
            SafetyRule(
                id="mental_health_risk",
                name="Mental Health Risk",
                description="Detects indicators of self-harm or severe distress",
                category="self_harm",
                severity=Severity.HIGH,
                action=RuleAction.ESCALATE,
                match_type=MatchType.KEYWORD,
                keywords=["suicide", "kill myself", "end my life", "want to die"],
                confidence=0.9,
                priority=10,
                tags=["mental_health", "safety"],
            ),
            # Privacy
            SafetyRule(
                id="privacy_pii",
                name="PII Detection",
                description="Detects potential personally identifiable information",
                category="privacy",
                severity=Severity.MEDIUM,
                action=RuleAction.BLOCK,
                match_type=MatchType.REGEX,
                patterns=[r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"],
                confidence=0.8,
                priority=40,
                tags=["privacy", "pii"],
            ),
            # Harassment
            SafetyRule(
                id="harassment",
                name="Harassment",
                description="Detects abusive or harassing language",
                category="harassment",
                severity=Severity.MEDIUM,
                action=RuleAction.BLOCK,
                match_type=MatchType.KEYWORD,
                keywords=["stupid", "idiot", "loser", "hate you"],
                confidence=0.7,
                priority=50,
                tags=["harassment", "abusive"],
            ),
        ]

    def start_auto_reload(self) -> None:
        """Start automatic rule reloading in background thread."""
        if not self._auto_reload or self._reload_thread is not None:
            return

        self._stop_reload.clear()
        self._reload_thread = threading.Thread(target=self._reload_loop, daemon=True)
        self._reload_thread.start()
        logger.info(f"Started auto-reload (interval: {self._reload_interval}s)")

    def stop_auto_reload(self) -> None:
        """Stop automatic rule reloading."""
        if self._reload_thread is None:
            return

        self._stop_reload.set()
        self._reload_thread.join(timeout=self._reload_interval + 2)
        self._reload_thread = None
        logger.info("Stopped auto-reload")

    def _reload_loop(self) -> None:
        """Background loop for checking file changes."""
        while not self._stop_reload.is_set():
            try:
                self.check_and_reload()
            except Exception as e:
                logger.error(f"Error in reload loop: {e}")

            # Wait for interval or stop signal
            self._stop_reload.wait(self._reload_interval)

    def check_and_reload(self) -> bool:
        """
        Check if any rule files have changed and reload if necessary.

        Returns:
            True if rules were reloaded
        """
        if not self.rules_dir.exists():
            return False

        changed = False
        for filepath in self.rules_dir.glob("*"):
            if filepath.suffix.lower() in (".yaml", ".yml", ".json"):
                current_mtime = filepath.stat().st_mtime
                last_mtime = self._file_timestamps.get(str(filepath), 0)

                if current_mtime > last_mtime:
                    logger.info(f"Detected change in {filepath}")
                    changed = True
                    break

        if changed:
            try:
                rules = self.load_all_rules()
                engine = get_guardian_engine()
                engine.load_rules(rules)
                logger.info("Rules reloaded successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to reload rules: {e}")

        return False


class DynamicRuleManager:
    """
    Manager for dynamically injected rules.

    Provides API for runtime rule injection without file changes.
    """

    def __init__(self):
        self._dynamic_rules: dict[str, SafetyRule] = {}
        self._lock = threading.RLock()

    def inject_rule(self, rule: SafetyRule, engine: GuardianEngine | None = None) -> bool:
        """
        Inject a rule dynamically at runtime.

        Args:
            rule: Rule to inject
            engine: Guardian engine to update (uses global if None)

        Returns:
            True if injection succeeded
        """
        with self._lock:
            self._dynamic_rules[rule.id] = rule

            if engine is None:
                engine = get_guardian_engine()

            # Register in engine
            engine.registry.register(rule)

            # Add to appropriate matcher
            if rule.match_type == MatchType.KEYWORD:
                engine.trie.add_rule(rule)
                engine.trie.build()  # Rebuild needed
            elif rule.match_type == MatchType.REGEX:
                engine.regex_set.add_rule(rule)

            logger.info(f"Dynamically injected rule: {rule.id}")
            return True

    def remove_rule(self, rule_id: str, engine: GuardianEngine | None = None) -> bool:
        """
        Remove a dynamically injected rule.

        Args:
            rule_id: ID of rule to remove
            engine: Guardian engine to update

        Returns:
            True if removal succeeded
        """
        with self._lock:
            if rule_id not in self._dynamic_rules:
                return False

            del self._dynamic_rules[rule_id]

            if engine is None:
                engine = get_guardian_engine()

            # Remove from registry
            engine.registry.unregister(rule_id)

            # Note: Matchers don't support removal efficiently
            # Full reload may be needed for complete removal
            logger.info(f"Removed dynamic rule: {rule_id}")
            return True

    def get_dynamic_rules(self) -> list[SafetyRule]:
        """Get all dynamically injected rules."""
        with self._lock:
            return list(self._dynamic_rules.values())

    def clear_dynamic_rules(self, engine: GuardianEngine | None = None) -> None:
        """Clear all dynamic rules."""
        with self._lock:
            if engine is None:
                engine = get_guardian_engine()

            for rule_id in list(self._dynamic_rules.keys()):
                engine.registry.unregister(rule_id)

            self._dynamic_rules.clear()

            # Full reload to clean matchers
            loader = RuleLoader()
            rules = loader.load_all_rules()
            engine.load_rules(rules)

            logger.info("Cleared all dynamic rules")


# Global instances
_rule_loader: RuleLoader | None = None
_dynamic_manager: DynamicRuleManager | None = None


def get_rule_loader() -> RuleLoader:
    """Get global rule loader instance."""
    global _rule_loader
    if _rule_loader is None:
        _rule_loader = RuleLoader(auto_reload=True)
    return _rule_loader


def get_dynamic_manager() -> DynamicRuleManager:
    """Get global dynamic rule manager."""
    global _dynamic_manager
    if _dynamic_manager is None:
        _dynamic_manager = DynamicRuleManager()
    return _dynamic_manager


def init_guardian_rules(rules_dir: str | None = None, auto_reload: bool = True) -> GuardianEngine:
    """
    Initialize GUARDIAN with rules from directory.

    Args:
        rules_dir: Directory containing rule files
        auto_reload: Enable automatic rule reloading

    Returns:
        Initialized GuardianEngine
    """
    global _rule_loader

    # Create loader
    _rule_loader = RuleLoader(rules_dir=rules_dir, auto_reload=auto_reload)

    # Load all rules
    rules = _rule_loader.load_all_rules()

    # Initialize engine
    engine = get_guardian_engine()
    engine.load_rules(rules)

    # Start auto-reload if enabled
    if auto_reload:
        _rule_loader.start_auto_reload()

    logger.info(f"GUARDIAN initialized with {len(rules)} rules")
    return engine
