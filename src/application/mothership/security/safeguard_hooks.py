"""
Security Safeguard Hooks for GRID-main.

Implements trigger-bound hook functions and conditional if-then policy engine
derived from CascadeProjects threat model (TM-001..TM-006), security best
practices (SBP-001..SBP-004), and ownership map governance findings.

Each guard class is a self-contained hook that can be registered with the
middleware layer or called directly from application code. The PolicyEngine
evaluates conditional rules at runtime.

Usage:
    from application.mothership.security.safeguard_hooks import (
        PolicyEngine,
        TokenStorageGuard,
        WebSocketAuthHook,
        CORSPolicyGuard,
        SecretHygieneGuard,
        DocsExposureGuard,
    )
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Policy Engine — Conditional If-Then Model
# =============================================================================


class PolicyVerdict(Enum):
    """Outcome of a policy evaluation."""

    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    ESCALATE = "escalate"


@dataclass
class PolicyResult:
    """Result of evaluating a single policy rule."""

    policy_id: str
    verdict: PolicyVerdict
    reason: str
    threat_basis: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "verdict": self.verdict.value,
            "reason": self.reason,
            "threat_basis": self.threat_basis,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class PolicyRule:
    """
    A declarative if-then security policy rule.

    condition_fn: callable returning True if the condition is met
    action: what to do when condition is True
    """

    policy_id: str
    description: str
    threat_basis: str
    condition_fn: Any  # Callable[[dict[str, Any]], bool]
    verdict_on_match: PolicyVerdict
    reason_template: str

    def evaluate(self, context: dict[str, Any]) -> PolicyResult | None:
        """Evaluate this rule against the given context. Returns result only if triggered."""
        try:
            if self.condition_fn(context):
                return PolicyResult(
                    policy_id=self.policy_id,
                    verdict=self.verdict_on_match,
                    reason=self.reason_template.format(**context) if context else self.reason_template,
                    threat_basis=self.threat_basis,
                    metadata={"context_keys": list(context.keys())},
                )
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Policy %s evaluation error: %s", self.policy_id, exc)
            return PolicyResult(
                policy_id=self.policy_id,
                verdict=PolicyVerdict.WARN,
                reason=f"Policy evaluation error: {exc}",
                threat_basis=self.threat_basis,
            )
        return None


class PolicyEngine:
    """
    Runtime policy engine that evaluates conditional if-then rules.

    Rules are registered at startup and evaluated per-request or per-event.
    The engine returns the most restrictive verdict across all triggered rules.
    """

    _VERDICT_PRIORITY = {
        PolicyVerdict.DENY: 4,
        PolicyVerdict.ESCALATE: 3,
        PolicyVerdict.WARN: 2,
        PolicyVerdict.ALLOW: 1,
    }

    def __init__(self) -> None:
        self._rules: list[PolicyRule] = []
        self._evaluation_log: list[PolicyResult] = []
        self._max_log = 5000

    def register(self, rule: PolicyRule) -> None:
        """Register a policy rule."""
        self._rules.append(rule)
        logger.info("Registered policy rule: %s", rule.policy_id)

    def register_many(self, rules: list[PolicyRule]) -> None:
        for rule in rules:
            self.register(rule)

    def evaluate(self, context: dict[str, Any]) -> list[PolicyResult]:
        """Evaluate all rules against context. Returns list of triggered results."""
        triggered: list[PolicyResult] = []
        for rule in self._rules:
            result = rule.evaluate(context)
            if result is not None:
                triggered.append(result)
                self._evaluation_log.append(result)
                if len(self._evaluation_log) > self._max_log:
                    self._evaluation_log = self._evaluation_log[-self._max_log:]
        return triggered

    def evaluate_strict(self, context: dict[str, Any]) -> PolicyResult | None:
        """Evaluate all rules; return the most restrictive triggered result, or None."""
        triggered = self.evaluate(context)
        if not triggered:
            return None
        return max(triggered, key=lambda r: self._VERDICT_PRIORITY.get(r.verdict, 0))

    def get_recent_evaluations(self, limit: int = 50) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._evaluation_log[-limit:]]

    @property
    def rule_count(self) -> int:
        return len(self._rules)


# =============================================================================
# Hook: Token Storage Guard (TM-001, SBP-003)
# =============================================================================


class TokenStorageGuard:
    """
    Enforces secure token handling policies.

    IF token is stored in localStorage → THEN emit deprecation + enforce CSP
    IF token age exceeds MAX_TOKEN_AGE → THEN force re-authentication
    """

    MAX_TOKEN_AGE_SECONDS = int(os.getenv("MAX_TOKEN_AGE_SECONDS", "900"))  # 15 min default
    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "frame-src 'none'"
    )

    @classmethod
    def enforce_csp_headers(cls, response_headers: dict[str, str]) -> dict[str, str]:
        """Apply strict CSP to prevent XSS-based token theft."""
        response_headers["Content-Security-Policy"] = cls.CSP_POLICY
        response_headers["X-Content-Type-Options"] = "nosniff"
        response_headers["X-Frame-Options"] = "DENY"
        return response_headers

    @classmethod
    def validate_token_age(cls, issued_at: float | None) -> PolicyResult:
        """
        IF token age > MAX_TOKEN_AGE_SECONDS THEN force re-auth.
        """
        if issued_at is None:
            return PolicyResult(
                policy_id="P-NET-005",
                verdict=PolicyVerdict.DENY,
                reason="Token missing issued_at claim — cannot verify age",
                threat_basis="TM-001",
            )

        age = time.time() - issued_at
        if age > cls.MAX_TOKEN_AGE_SECONDS:
            return PolicyResult(
                policy_id="P-NET-005",
                verdict=PolicyVerdict.DENY,
                reason=f"Token age {int(age)}s exceeds maximum {cls.MAX_TOKEN_AGE_SECONDS}s",
                threat_basis="TM-001",
                metadata={"token_age_seconds": int(age)},
            )

        return PolicyResult(
            policy_id="P-NET-005",
            verdict=PolicyVerdict.ALLOW,
            reason="Token age within limits",
            threat_basis="TM-001",
            metadata={"token_age_seconds": int(age)},
        )

    @classmethod
    def enforce(cls, token_issued_at: float | None, response_headers: dict[str, str] | None = None) -> PolicyResult:
        """
        Single entry point for auth path: validate token age and optionally apply CSP.

        Returns DENY if token is missing or too old; otherwise ALLOW and mutates
        response_headers with CSP if provided (P-NET-004 / P-NET-005).
        """
        result = cls.validate_token_age(token_issued_at)
        if result.verdict == PolicyVerdict.DENY:
            return result
        if response_headers is not None:
            cls.enforce_csp_headers(response_headers)
        return result

    @classmethod
    def get_policy_rules(cls) -> list[PolicyRule]:
        """Return PolicyRules for registration with the engine."""
        return [
            PolicyRule(
                policy_id="P-NET-004",
                description="Detect localStorage token storage pattern",
                threat_basis="TM-001, SBP-003",
                condition_fn=lambda ctx: ctx.get("token_storage") == "localStorage",
                verdict_on_match=PolicyVerdict.WARN,
                reason_template="Token storage uses localStorage — migrate to HttpOnly cookies or in-memory",
            ),
            PolicyRule(
                policy_id="P-NET-005",
                description="Token age exceeds maximum",
                threat_basis="TM-001",
                condition_fn=lambda ctx: (
                    ctx.get("token_issued_at") is not None
                    and (time.time() - ctx["token_issued_at"]) > cls.MAX_TOKEN_AGE_SECONDS
                ),
                verdict_on_match=PolicyVerdict.DENY,
                reason_template="Token age exceeds maximum — re-authentication required",
            ),
        ]


# =============================================================================
# Hook: WebSocket Auth Hook (TM-002)
# =============================================================================


class WebSocketAuthHook:
    """
    Enforces authentication on WebSocket connections.

    IF WebSocket upgrade AND no valid auth → THEN reject 401
    IF connections from single IP > WS_MAX_PER_IP → THEN throttle
    """

    WS_MAX_PER_IP = int(os.getenv("WS_MAX_PER_IP", "10"))

    _connection_counts: dict[str, int] = {}
    _connection_timestamps: dict[str, list[float]] = {}
    WS_WINDOW_SECONDS = 60

    @classmethod
    def validate_connection(
        cls,
        auth_token: str | None,
        client_ip: str | None,
        path: str = "",
    ) -> PolicyResult:
        """
        IF request targets /ws/ AND no valid auth token → THEN reject.
        IF connections from IP exceed limit → THEN throttle.
        """
        if "/ws/" in path or path.startswith("/ws"):
            if not auth_token:
                return PolicyResult(
                    policy_id="P-NET-001",
                    verdict=PolicyVerdict.DENY,
                    reason="WebSocket connection rejected — no authentication token",
                    threat_basis="TM-002",
                    metadata={"path": path, "client_ip": client_ip},
                )

        if client_ip:
            now = time.time()
            timestamps = cls._connection_timestamps.get(client_ip, [])
            timestamps = [t for t in timestamps if now - t < cls.WS_WINDOW_SECONDS]
            timestamps.append(now)
            cls._connection_timestamps[client_ip] = timestamps

            if len(timestamps) > cls.WS_MAX_PER_IP:
                return PolicyResult(
                    policy_id="P-NET-006",
                    verdict=PolicyVerdict.DENY,
                    reason=f"WebSocket connection throttled — {len(timestamps)} connections from {client_ip} in {cls.WS_WINDOW_SECONDS}s (max {cls.WS_MAX_PER_IP})",
                    threat_basis="TM-002",
                    metadata={"client_ip": client_ip, "connection_count": len(timestamps)},
                )

        return PolicyResult(
            policy_id="P-NET-001",
            verdict=PolicyVerdict.ALLOW,
            reason="WebSocket connection allowed",
            threat_basis="TM-002",
        )

    @classmethod
    def get_policy_rules(cls) -> list[PolicyRule]:
        return [
            PolicyRule(
                policy_id="P-NET-001",
                description="Require auth on WebSocket connections",
                threat_basis="TM-002",
                condition_fn=lambda ctx: (
                    ("/ws/" in ctx.get("path", "") or ctx.get("path", "").startswith("/ws"))
                    and not ctx.get("auth_token")
                ),
                verdict_on_match=PolicyVerdict.DENY,
                reason_template="WebSocket connection rejected — authentication required",
            ),
            PolicyRule(
                policy_id="P-NET-006",
                description="Throttle excessive WebSocket connections per IP",
                threat_basis="TM-002",
                condition_fn=lambda ctx: ctx.get("ws_connection_count", 0) > cls.WS_MAX_PER_IP,
                verdict_on_match=PolicyVerdict.DENY,
                reason_template="WebSocket throttled — connection limit exceeded",
            ),
        ]


# =============================================================================
# Hook: CORS Policy Guard (SBP-002)
# =============================================================================


class CORSPolicyGuard:
    """
    Enforces deny-by-default CORS policy.

    IF CORS origins is ["*"] AND credentials=True → THEN block startup
    """

    KNOWN_SAFE_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @classmethod
    def validate(
        cls,
        origins: list[str],
        allow_credentials: bool,
        environment: str = "development",
    ) -> PolicyResult:
        """
        IF origins is ["*"] AND credentials=True → THEN deny.
        IF production AND origins contains wildcard → THEN deny.
        """
        if "*" in origins and allow_credentials:
            return PolicyResult(
                policy_id="P-NET-002",
                verdict=PolicyVerdict.DENY,
                reason="CORS wildcard origin with credentials is forbidden — configure explicit origin allowlist",
                threat_basis="SBP-002",
                metadata={"origins": origins, "allow_credentials": allow_credentials},
            )

        if environment == "production" and "*" in origins:
            return PolicyResult(
                policy_id="P-NET-002",
                verdict=PolicyVerdict.DENY,
                reason="CORS wildcard origin forbidden in production",
                threat_basis="SBP-002",
                metadata={"origins": origins, "environment": environment},
            )

        return PolicyResult(
            policy_id="P-NET-002",
            verdict=PolicyVerdict.ALLOW,
            reason="CORS policy within acceptable parameters",
            threat_basis="SBP-002",
        )

    @classmethod
    def get_policy_rules(cls) -> list[PolicyRule]:
        return [
            PolicyRule(
                policy_id="P-NET-002",
                description="Block credentialed wildcard CORS",
                threat_basis="SBP-002",
                condition_fn=lambda ctx: (
                    "*" in ctx.get("cors_origins", [])
                    and ctx.get("cors_allow_credentials", False)
                ),
                verdict_on_match=PolicyVerdict.DENY,
                reason_template="Credentialed CORS with wildcard origins is forbidden",
            ),
        ]


# =============================================================================
# Hook: Secret Hygiene Guard (SBP-001)
# =============================================================================


class SecretHygieneGuard:
    """
    Prevents use of known test/weak secrets in non-test environments.

    IF GATE_USER_SECRET matches known test secret → THEN block in production
    """

    KNOWN_TEST_SECRETS = frozenset([
        "test-secret-for-grid-main-2026",
        "grid-main-secret",
        "TransitionGate",
        "test-secret",
        "secret",
        "GRID-main-2026",
    ])

    @classmethod
    def check_secrets(cls, environment: str = "development") -> PolicyResult:
        """
        IF environment is not test AND GATE_USER_SECRET matches known test value → THEN deny.
        """
        gate_secret = os.getenv("GATE_USER_SECRET", "")

        if environment in ("test", "testing"):
            return PolicyResult(
                policy_id="P-INT-006",
                verdict=PolicyVerdict.ALLOW,
                reason="Test environment — secret validation skipped",
                threat_basis="SBP-001",
            )

        if gate_secret in cls.KNOWN_TEST_SECRETS:
            return PolicyResult(
                policy_id="P-INT-006",
                verdict=PolicyVerdict.DENY,
                reason="GATE_USER_SECRET matches a known test secret — rotate immediately",
                threat_basis="SBP-001",
                metadata={"environment": environment},
            )

        if gate_secret and len(gate_secret) < 32:
            return PolicyResult(
                policy_id="P-INT-006",
                verdict=PolicyVerdict.WARN,
                reason=f"GATE_USER_SECRET is only {len(gate_secret)} chars — recommend ≥32",
                threat_basis="SBP-001",
                metadata={"secret_length": len(gate_secret)},
            )

        return PolicyResult(
            policy_id="P-INT-006",
            verdict=PolicyVerdict.ALLOW,
            reason="Secret hygiene check passed",
            threat_basis="SBP-001",
        )

    @classmethod
    def validate_hmac_fingerprint(
        cls,
        secret: str,
        payload_hash: str,
        machine_fingerprint: str,
        nonce: str,
        declared_fingerprint: str,
    ) -> bool:
        """Verify HMAC-SHA256 user fingerprint (same algorithm as GATE envelope)."""
        message = f"{payload_hash}:{machine_fingerprint}:{nonce}"
        expected = hmac.new(
            secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, declared_fingerprint)

    @classmethod
    def get_policy_rules(cls) -> list[PolicyRule]:
        return [
            PolicyRule(
                policy_id="P-INT-006",
                description="Reject known test secrets in non-test environments",
                threat_basis="SBP-001",
                condition_fn=lambda ctx: (
                    ctx.get("environment") not in ("test", "testing")
                    and ctx.get("gate_secret", "") in cls.KNOWN_TEST_SECRETS
                ),
                verdict_on_match=PolicyVerdict.DENY,
                reason_template="Known test secret detected in non-test environment",
            ),
        ]


# =============================================================================
# Hook: Docs Exposure Guard (SBP-004)
# =============================================================================


class DocsExposureGuard:
    """
    Controls API documentation exposure by environment.

    IF production AND docs_url is set → THEN override to None
    """

    @classmethod
    def check(cls, environment: str, docs_url: str | None, redoc_url: str | None) -> PolicyResult:
        """
        IF environment is production AND docs are exposed → THEN deny/override.
        """
        if environment == "production" and (docs_url is not None or redoc_url is not None):
            return PolicyResult(
                policy_id="P-NET-003",
                verdict=PolicyVerdict.DENY,
                reason="API docs must be disabled in production — set docs_url=None, redoc_url=None",
                threat_basis="SBP-004",
                metadata={"docs_url": docs_url, "redoc_url": redoc_url},
            )

        return PolicyResult(
            policy_id="P-NET-003",
            verdict=PolicyVerdict.ALLOW,
            reason="Docs exposure within acceptable parameters",
            threat_basis="SBP-004",
        )

    @classmethod
    def get_safe_docs_config(cls, environment: str) -> dict[str, str | None]:
        """Return safe docs configuration for the given environment."""
        if environment == "production":
            return {"docs_url": None, "redoc_url": None, "openapi_url": None}
        return {"docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}

    @classmethod
    def get_policy_rules(cls) -> list[PolicyRule]:
        return [
            PolicyRule(
                policy_id="P-NET-003",
                description="Disable API docs in production",
                threat_basis="SBP-004",
                condition_fn=lambda ctx: (
                    ctx.get("environment") == "production"
                    and ctx.get("docs_url") is not None
                ),
                verdict_on_match=PolicyVerdict.DENY,
                reason_template="API docs must be disabled in production",
            ),
        ]


# =============================================================================
# Audit Integrity Guard (TM-004)
# =============================================================================


class AuditIntegrityGuard:
    """
    Validates audit entries and snapshots for integrity.

    IF timestamp is future or >24h stale → THEN reject
    IF source not in known servers → THEN reject
    IF health score delta > 40 → THEN flag anomalous
    """

    KNOWN_SOURCES = frozenset([
        "grid-server",
        "lots-server",
        "maintain-server",
        "echoes-server",
        "pulse-server",
        "seeds-server",
        "afloat-server",
        "grid-main",
    ])

    MAX_TIMESTAMP_DRIFT_SECONDS = 86400  # 24 hours
    MAX_SCORE_DELTA = 40

    @classmethod
    def validate_entry(
        cls,
        source: str,
        timestamp: str,
        tool: str | None = None,
    ) -> PolicyResult:
        """
        IF timestamp in future or >24h stale → THEN reject.
        IF source not in known list → THEN reject.
        """
        # Source validation (P-INT-002)
        if source not in cls.KNOWN_SOURCES:
            return PolicyResult(
                policy_id="P-INT-002",
                verdict=PolicyVerdict.DENY,
                reason=f"Audit entry from unknown source '{source}' — rejected",
                threat_basis="TM-004",
                metadata={"source": source, "known_sources": list(cls.KNOWN_SOURCES)},
            )

        # Timestamp validation (P-INT-001)
        try:
            entry_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            now = datetime.now(UTC)
            drift = abs((now - entry_time).total_seconds())

            if entry_time > now:
                return PolicyResult(
                    policy_id="P-INT-001",
                    verdict=PolicyVerdict.DENY,
                    reason=f"Audit entry timestamp is in the future by {int(drift)}s",
                    threat_basis="TM-004",
                    metadata={"timestamp": timestamp, "drift_seconds": int(drift)},
                )

            if drift > cls.MAX_TIMESTAMP_DRIFT_SECONDS:
                return PolicyResult(
                    policy_id="P-INT-001",
                    verdict=PolicyVerdict.DENY,
                    reason=f"Audit entry timestamp is {int(drift)}s stale (max {cls.MAX_TIMESTAMP_DRIFT_SECONDS}s)",
                    threat_basis="TM-004",
                    metadata={"timestamp": timestamp, "drift_seconds": int(drift)},
                )
        except (ValueError, TypeError) as exc:
            return PolicyResult(
                policy_id="P-INT-001",
                verdict=PolicyVerdict.DENY,
                reason=f"Invalid timestamp format: {exc}",
                threat_basis="TM-004",
            )

        return PolicyResult(
            policy_id="P-INT-001",
            verdict=PolicyVerdict.ALLOW,
            reason="Audit entry integrity check passed",
            threat_basis="TM-004",
        )

    @classmethod
    def validate_snapshot_delta(
        cls,
        previous_score: float | None,
        current_score: float,
    ) -> PolicyResult:
        """
        IF health score delta > MAX_SCORE_DELTA → THEN flag anomalous.
        """
        if previous_score is not None:
            delta = abs(current_score - previous_score)
            if delta > cls.MAX_SCORE_DELTA:
                return PolicyResult(
                    policy_id="P-INT-003",
                    verdict=PolicyVerdict.ESCALATE,
                    reason=f"Snapshot score delta {delta:.1f} exceeds threshold {cls.MAX_SCORE_DELTA}",
                    threat_basis="TM-004",
                    metadata={
                        "previous_score": previous_score,
                        "current_score": current_score,
                        "delta": delta,
                    },
                )

        return PolicyResult(
            policy_id="P-INT-003",
            verdict=PolicyVerdict.ALLOW,
            reason="Snapshot delta within acceptable range",
            threat_basis="TM-004",
        )

    @classmethod
    def get_policy_rules(cls) -> list[PolicyRule]:
        return [
            PolicyRule(
                policy_id="P-INT-001",
                description="Reject audit entries with impossible timestamps",
                threat_basis="TM-004",
                condition_fn=lambda ctx: ctx.get("timestamp_drift_seconds", 0) > cls.MAX_TIMESTAMP_DRIFT_SECONDS,
                verdict_on_match=PolicyVerdict.DENY,
                reason_template="Audit entry timestamp exceeds drift threshold",
            ),
            PolicyRule(
                policy_id="P-INT-002",
                description="Reject audit entries from unknown sources",
                threat_basis="TM-004",
                condition_fn=lambda ctx: ctx.get("source") not in cls.KNOWN_SOURCES,
                verdict_on_match=PolicyVerdict.DENY,
                reason_template="Audit entry from unknown source",
            ),
            PolicyRule(
                policy_id="P-INT-003",
                description="Flag anomalous snapshot score deltas",
                threat_basis="TM-004",
                condition_fn=lambda ctx: abs(ctx.get("score_delta", 0)) > cls.MAX_SCORE_DELTA,
                verdict_on_match=PolicyVerdict.ESCALATE,
                reason_template="Snapshot score delta exceeds threshold — manual review required",
            ),
        ]


# =============================================================================
# Factory: Build Default Policy Engine
# =============================================================================


def build_default_engine() -> PolicyEngine:
    """
    Construct a PolicyEngine pre-loaded with all research-derived rules.

    Returns a ready-to-use engine with rules from:
    - TokenStorageGuard (TM-001, SBP-003)
    - WebSocketAuthHook (TM-002)
    - CORSPolicyGuard (SBP-002)
    - SecretHygieneGuard (SBP-001)
    - DocsExposureGuard (SBP-004)
    - AuditIntegrityGuard (TM-004)
    """
    engine = PolicyEngine()
    engine.register_many(TokenStorageGuard.get_policy_rules())
    engine.register_many(WebSocketAuthHook.get_policy_rules())
    engine.register_many(CORSPolicyGuard.get_policy_rules())
    engine.register_many(SecretHygieneGuard.get_policy_rules())
    engine.register_many(DocsExposureGuard.get_policy_rules())
    engine.register_many(AuditIntegrityGuard.get_policy_rules())
    logger.info("Default policy engine built with %d rules", engine.rule_count)
    return engine


# =============================================================================
# Singleton: Global engine instance
# =============================================================================

_default_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    """Get or create the global policy engine singleton."""
    global _default_engine
    if _default_engine is None:
        _default_engine = build_default_engine()
    return _default_engine
