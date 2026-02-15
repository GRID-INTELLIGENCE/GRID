"""
Central Safety Rule Manager and Object Analysis Orchestrator.

This module acts as the "Cortex" for safety decisions, routing different
object types (Code, Config, Prompts) to specialized analyzers and
enforcing the canonical TrustTier logic.
"""

import ast
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from safety.guardian.engine import RuleAction, Severity, get_guardian_engine


# Canonical Trust Tiers (mirrored from mothership/security/auth.py)
# We redefine here to avoid circular imports, but they MUST match.
class TrustTier(str, Enum):
    ANON = "anon"
    USER = "user"
    VERIFIED = "verified"
    PRIVILEGED = "privileged"


logger = logging.getLogger(__name__)

# =============================================================================
# Evaluation Context
# =============================================================================


@dataclass
class EvaluationContext:
    """Context for safety evaluation."""

    user_id: str
    trust_tier: TrustTier
    session_id: str | None = None
    ip_address: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Specialized Analyzers
# =============================================================================


class CodeAnalyzer:
    """Thoughtful analysis of code objects."""

    # TODO: Add detection for ast.Exec nodes and nested function definitions
    #       that could be used to smuggle unsafe code past the analyzer.
    FORBIDDEN_NODES = {ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal}

    FORBIDDEN_CALLS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",
        "input",
        "globals",
        "locals",
        "getattr",
        "setattr",
        "delattr",
    }

    @classmethod
    def analyze(cls, code: str) -> list[str]:
        """
        Parse and inspect code for unsafe patterns using AST.
        Returns a list of violation descriptions.
        """
        violations = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # 1. Check for forbidden AST node types
                if type(node) in cls.FORBIDDEN_NODES:
                    violations.append(f"Forbidden code construct: {type(node).__name__}")

                # 2. Check for forbidden function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in cls.FORBIDDEN_CALLS:
                        violations.append(f"Forbidden function call: {node.func.id}")
                    # Handle attribute calls like os.system (if we were allowing imports, which we aren't)
                    elif isinstance(node.func, ast.Attribute) and node.func.attr in cls.FORBIDDEN_CALLS:
                        violations.append(f"Forbidden function call: {node.func.attr}")

        except SyntaxError as e:
            violations.append(f"Syntax Error in code object: {e}")
        except Exception as e:
            logger.error(f"AST Analysis failed: {e}")
            violations.append("Code analysis failed due to internal error")

        return violations


class ConfigValidator:
    """Strict schema validation for configuration objects."""

    PROTECTED_KEYS = {"admin", "root", "sudo", "bypass", "override", "security_disabled", "debug_mode"}

    @classmethod
    def validate(cls, config: dict[str, Any]) -> list[str]:
        """
        Deep scan of config dicts for unauthorized overrides.
        """
        violations = []

        def _scan(d: dict[str, Any], path: str = ""):
            for k, v in d.items():
                # Check key against protected set
                if k.lower() in cls.PROTECTED_KEYS:
                    violations.append(f"Unauthorized configuration key: {path}{k}")

                # Recurse
                if isinstance(v, dict):
                    _scan(v, path=f"{path}{k}.")

        _scan(config)
        return violations


class PromptInspector:
    """Context-aware analysis of chat/text prompts."""

    # We delegate the actual pattern matching to the RuleEngine,
    # but this class adds conversational context logic.

    def __init__(self, engine: Any = None):
        self.engine = engine or get_guardian_engine()

    def analyze(self, text: str, context: EvaluationContext) -> list[Any]:
        """
        Analyze prompt text using the GuardianEngine, adjusting sensitivity
        based on the TrustTier.
        """
        # Get matching rules
        matches, _ = self.engine.evaluate(text)
        violating_matches = []

        for match in matches:
            # TIERED ENFORCEMENT LOGIC
            # Privileged users might bypass LOW severity rules
            if context.trust_tier == TrustTier.PRIVILEGED:
                if match.severity == Severity.LOW:
                    logger.info(f"Bypassing LOW severity rule for PRIVILEGED user: {match.rule_id}")
                    continue

            # Check if action is BLOCK or ESCALATE
            if match.action in (RuleAction.BLOCK, RuleAction.ESCALATE):
                violating_matches.append(match)

        return violating_matches


# =============================================================================
# Recursive Object Inspector
# =============================================================================


class RecursiveInspector:
    """
    Cautiously unpacks complex objects to route them to valid analyzers.
    Acts as the 'deep inspection' traversal mechanism.
    """

    MAX_DEPTH = 20  # Prevent DoS via deeply nested payloads

    def __init__(self, code_analyzer: CodeAnalyzer, config_validator: ConfigValidator):
        self.code_analyzer = code_analyzer
        self.config_validator = config_validator

    def inspect(self, obj: Any, path: str = "root", _depth: int = 0) -> list[str]:
        """
        Recursively inspect an object.
        Returns a list of all found violations.
        """
        if _depth > self.MAX_DEPTH:
            return [f"[{path}] Object nesting exceeds maximum depth ({self.MAX_DEPTH})"]

        violations = []

        # 1. DICTIONARIES (Potential Configs)
        if isinstance(obj, dict):
            # heuristic: if it looks like a config, validate it
            violations.extend(self.config_validator.validate(obj))

            for k, v in obj.items():
                violations.extend(self.inspect(v, path=f"{path}.{k}", _depth=_depth + 1))

        # 2. LISTS
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                violations.extend(self.inspect(item, path=f"{path}[{i}]", _depth=_depth + 1))

        # 3. STRINGS (Potential Code or Prompts)
        elif isinstance(obj, str):
            # Heuristic: does it look like code?
            # We add common dangerous patterns to catch concise attacks
            if any(k in obj for k in ("def ", "import ", "class ", ";", "eval(", "exec(", "os.", "sys.", "subprocess")):
                # If it looks like code, we MUST run code analysis
                code_violations = self.code_analyzer.analyze(obj)
                for v in code_violations:
                    violations.append(f"[{path}] {v}")

        return violations


# =============================================================================
# Safety Rule Manager (Orchestrator)
# =============================================================================


class SafetyRuleManager:
    """
    The Central Orchestrator for Project GUARDIAN.
    """

    def __init__(self):
        from safety.guardian.loader import get_rule_loader

        self.engine = get_guardian_engine()
        # Ensure rules are loaded if engine is empty
        if not self.engine.registry.get_all():
            rules = get_rule_loader().load_all_rules()
            self.engine.load_rules(rules)

        self.code_analyzer = CodeAnalyzer()
        self.config_validator = ConfigValidator()
        self.recursive_inspector = RecursiveInspector(self.code_analyzer, self.config_validator)
        self.prompt_inspector = PromptInspector()

    def evaluate_request(self, user_id: str, trust_tier: str, data: Any) -> tuple[bool, list[str]]:
        """
        Main Entry Point.
        Accepts a user request (Subject) and data (Object).
        Returns (is_safe, reasons).
        """
        reasons = []

        # 1. Build Context
        try:
            tier = TrustTier(trust_tier)
        except ValueError:
            tier = TrustTier.ANON  # Default to lowest trust

        ctx = EvaluationContext(user_id=user_id, trust_tier=tier)

        # 2. Deep Object Inspection (Structure/Code/Config)
        object_violations = self.recursive_inspector.inspect(data)
        if object_violations:
            reasons.extend(object_violations)

        # 3. Prompt/Content Inspection (Semantic/Pattern)
        # We flatten the object to string for the regex engine to catch things hidden in deep keys
        flattened_text = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
        prompt_violations = self.prompt_inspector.analyze(flattened_text, ctx)

        for match in prompt_violations:
            reasons.append(f"Content Policy Violation: {match.rule_name} (Severity: {match.severity.value})")

        is_safe = len(reasons) == 0

        if not is_safe:
            logger.warning(f"Safety Violation for User {user_id} [{tier}]: {reasons}")

        return is_safe, reasons


# Global Instance
_manager = SafetyRuleManager()


def get_rule_manager() -> SafetyRuleManager:
    return _manager
