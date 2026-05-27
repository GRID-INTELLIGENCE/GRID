"""Admission Gate middleware — top-of-stack pre-filter.

Sits above all other middleware in the Mothership stack. Rejects requests
that should never reach the pipeline:

1. **Policy Billboard** — every entity sees the ethical participation contract
   at the top of the execution chain before any gate is evaluated.
2. **Budget enforcement** — sliding-window call cap per client.
3. **Origin whitelist** — only known origins pass.
4. **Payload structure** — POST/PUT/PATCH bodies must carry required keys.
5. **Context ceiling** — estimated token cost must not exceed threshold.
6. **Entity attribution** — identifies the entity behind each request,
   feeds violations into the knowledge graph, and applies penalty multipliers
   for abusive or profit-masking patterns.

Rejected requests get a 429 (budget), 403 (origin), or 422 (structure/overflow)
and never touch the router, IntelligenceApplication, or any downstream middleware.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from application.mothership.security.merit_standing import (
    ActionClass,
    MeritStanding,
    Scope,
    get_merit_engine,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_CALL_BUDGET = 60  # calls per window
DEFAULT_WINDOW_SECONDS = 60.0
DEFAULT_CONTEXT_TOKEN_CEILING = 25_000
DEFAULT_MAX_BODY_BYTES = 512 * 1024  # 512 KB estimated context limit
PROFIT_MASK_PENALTY_MULTIPLIER = 3  # 3x penalty for profit-masking abuse

# Paths that bypass the gate entirely (minimal infra + self-observation endpoints).
# `/admission/*` endpoints exist to observe and operate the gate; they should not
# consume budget or be blocked by the same gate they are inspecting.
BYPASS_PATHS: frozenset[str] = frozenset(
    {"/health", "/ping", "/metrics", "/docs", "/redoc", "/openapi.json", "/admission", "/"}
)

# Admission paths that require full merit evaluation (not bypassed)
ADMISSION_PATHS_PREFIX = "/admission"

# Origins that are allowed through (header: X-Admission-Origin)
ALLOWED_ORIGINS: frozenset[str] = frozenset({"internal", "mothership", "grid-core", "cli", "mcp", "frontend"})

# Signals that suggest profit-maximization disguised as cost-cutting.
# Matched against payload metadata, headers, or entity behavioral history.
PROFIT_MASK_SIGNALS: frozenset[str] = frozenset(
    {
        "cost_cutting",
        "cost_optimization",
        "efficiency_override",
        "budget_override",
        "maximize_throughput",
        "skip_validation",
        "bypass_safety",
        "fast_track",
        "bulk_override",
        "unlimited_quota",
    }
)


# ---------------------------------------------------------------------------
# Policy Billboard
# ---------------------------------------------------------------------------


BILLBOARD_VERSION = "1.0.0"


@dataclass(frozen=True)
class PolicyBillboard:
    """Immutable ethical participation contract displayed at the top of every
    execution chain. Every entity entering the GRID pipeline sees this before
    any gate is evaluated.

    The billboard serves three purposes:
    1. Inform — present the active ethical policy and principles.
    2. Differentiate — distinguish runtime mistakes (1x penalty) from
       intentional environment pollution / scheming (3x accelerated penalty).
    3. Actionable — make penalties executable, give entities clear room to
       opt out, and establish credibility for enforcement.
    """

    # -- Core principles (sourced from config/policy.yaml at boot) --
    principles: dict[str, bool] = field(default_factory=dict)

    # -- Key policy highlights --
    ethical_dos: tuple[str, ...] = (
        "Contribute honest, well-structured data to the pipeline",
        "Respect call budgets and shared resource ceilings",
        "Declare your identity and origin transparently",
        "Report anomalies and participate in ecosystem health",
        "Accept penalty outcomes and correct course accordingly",
    )

    ethical_donts: tuple[str, ...] = (
        "Do not flood the pipeline with abusive call volumes",
        "Do not disguise profit-maximization as cost-cutting or efficiency",
        "Do not submit bogus, malformed, or irrelevant payloads",
        "Do not attempt to bypass safety, validation, or quota controls",
        "Do not manipulate, target, or undermine other participants",
    )

    # -- Penalty tiers --
    tier_runtime_mistake: str = (
        "1x base penalty. Runtime errors, accidental overflows, and structural "
        "mistakes are treated as correctable incidents. Fix and proceed."
    )
    tier_environment_pollution: str = (
        "1x base penalty with compounding budget reduction. Repeated violations "
        "accumulate penalty points that progressively reduce effective call budget. "
        "Persistent pollution leads to bannering."
    )
    tier_intentional_scheming: str = (
        "3x accelerated penalty. Profit-masking signals, safety bypasses, "
        "quota manipulation, and competitive targeting through violence or "
        "disruption are classified as intentional scheming. The 3x multiplier "
        "isolates genuine runtime mistakes from deliberate environment "
        "pollution and unethical plotting to gain advantage through "
        "manipulation, coercion, or destructive competition."
    )

    # -- Caution --
    caution: str = (
        "This policy practices ZERO TOLERANCE toward unethical or destructive "
        "scheming. Disruptive recognition stances — attempts to gain standing "
        "through manipulation, violence, targeting, or corrosive lobbying — "
        "are actionable with equal rigor regardless of the entity's history "
        "or standing. Participation in GRID is voluntary; entities that cannot "
        "operate within these principles have clear room to opt out before "
        "penalties are applied."
    )

    # -- Evolution notice --
    evolution_notice: str = (
        "This billboard was introduced after observed corruption attempts by "
        "participants who used abusive call volumes, bogus payloads, and "
        "external calls to pressure the pipeline mediator beyond its context "
        "capacity. The entity attribution engine, penalty tiers, and 3x "
        "acceleration were added to restore pipeline integrity, data quality, "
        "and fair play across the ecosystem."
    )

    def snapshot(self) -> dict[str, Any]:
        """Serializable snapshot of the billboard for inclusion in responses."""
        return {
            "billboard_version": BILLBOARD_VERSION,
            "principles": dict(self.principles),
            "ethical_dos": list(self.ethical_dos),
            "ethical_donts": list(self.ethical_donts),
            "penalty_tiers": {
                "runtime_mistake": self.tier_runtime_mistake,
                "environment_pollution": self.tier_environment_pollution,
                "intentional_scheming": self.tier_intentional_scheming,
            },
            "caution": self.caution,
            "evolution_notice": self.evolution_notice,
        }

    def summary(self) -> str:
        """One-line summary for response headers."""
        return (
            f"GRID Policy v{BILLBOARD_VERSION}: "
            f"{len(self.ethical_dos)} DOs, {len(self.ethical_donts)} DON'Ts, "
            f"3 penalty tiers, zero tolerance for scheming"
        )


def load_billboard() -> PolicyBillboard:
    """Load a PolicyBillboard with principles from runtime policy.

    Attempts to read config/policy.yaml via tools.runtime_policy.
    Falls back to default principles if the module or file is unavailable.
    """
    principles: dict[str, bool] = {
        "transparency": True,
        "openness": True,
        "freedom_to_think": True,
        "access_default": True,
    }

    try:
        from tools.runtime_policy import get_principles

        principles.update(get_principles())
    except Exception:
        logger.debug("admission_gate.billboard: runtime_policy unavailable, using defaults")

    return PolicyBillboard(principles=principles)


# ---------------------------------------------------------------------------
# Entity violation classification
# ---------------------------------------------------------------------------


class ViolationType(StrEnum):
    """Classification of gate violations for entity attribution."""

    BUDGET_EXCEEDED = "budget_exceeded"
    ORIGIN_DENIED = "origin_denied"
    CONTEXT_OVERFLOW = "context_overflow"
    INVALID_BODY = "invalid_body"
    MISSING_STRUCTURE = "missing_structure"
    PROFIT_MASKING = "profit_masking"
    ENTITY_BANNERED = "entity_bannered"
    VELOCITY_ANOMALY = "velocity_anomaly"


@dataclass
class EntityViolation:
    """A single recorded violation attributed to an entity."""

    entity_id: str
    violation_type: ViolationType
    timestamp: float
    penalty_points: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityRecord:
    """Accumulated record for a known entity."""

    entity_id: str
    violations: list[EntityViolation] = field(default_factory=list)
    total_penalty_points: int = 0
    bannered: bool = False
    banner_reason: str = ""
    first_seen: float = field(default_factory=time.monotonic)
    last_seen: float = field(default_factory=time.monotonic)
    # Merit standing for roll-number model
    merit_standing: MeritStanding | None = None
    # Vection drift score: 0.0 = stable trajectory, 1.0 = maximum churn
    drift_score: float = 0.0

    def __post_init__(self) -> None:
        """Ensure merit_standing is initialized."""
        if self.merit_standing is None:
            engine = get_merit_engine()
            self.merit_standing = engine.get_or_create_standing(self.entity_id)

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    @property
    def profit_mask_violations(self) -> int:
        return sum(1 for v in self.violations if v.violation_type == ViolationType.PROFIT_MASKING)


# ---------------------------------------------------------------------------
# Protocols for pluggable intelligence backends
# ---------------------------------------------------------------------------


class PatternDetectorProtocol(Protocol):
    """Protocol for pattern detection — matches HybridPatternDetector.detect()."""

    async def detect(self, state: Any) -> Any: ...


class KnowledgeStoreProtocol(Protocol):
    """Protocol for knowledge graph — matches PersistentJSONKnowledgeStore."""

    def store_entity(self, entity: Any) -> Any: ...

    def create_relationship(self, *args: Any, **kwargs: Any) -> Any: ...


# ---------------------------------------------------------------------------
# Sliding-window budget tracker
# ---------------------------------------------------------------------------


class _BudgetTracker:
    """Per-client sliding-window call counter."""

    __slots__ = ("_budget", "_window", "_ledger")

    def __init__(self, budget: int, window_seconds: float) -> None:
        self._budget = budget
        self._window = window_seconds
        self._ledger: dict[str, list[float]] = defaultdict(list)

    def allow(self, client_key: str, effective_budget: int | None = None) -> bool:
        budget = effective_budget if effective_budget is not None else self._budget
        now = time.monotonic()
        cutoff = now - self._window
        timestamps = self._ledger[client_key]
        self._ledger[client_key] = [t for t in timestamps if t > cutoff]
        if len(self._ledger[client_key]) >= budget:
            return False
        self._ledger[client_key].append(now)
        return True

    def remaining(self, client_key: str, effective_budget: int | None = None) -> int:
        budget = effective_budget if effective_budget is not None else self._budget
        now = time.monotonic()
        cutoff = now - self._window
        active = [t for t in self._ledger[client_key] if t > cutoff]
        return max(0, budget - len(active))

    @property
    def default_budget(self) -> int:
        return self._budget

    def reset(self) -> None:
        self._ledger.clear()


# ---------------------------------------------------------------------------
# Entity Attribution Engine
# ---------------------------------------------------------------------------


class EntityAttributionEngine:
    """Identifies, tracks, and penalizes entities behind requests.

    Integrates with GRID's knowledge graph (store_entity, create_relationship)
    and pattern detection (detect behavioral abuse patterns) to:

    1. Resolve each request to a named entity (client key, API key, user-id).
    2. Accumulate violations per entity.
    3. Detect profit-masking signals and apply 3x penalty.
    4. Banner entities that exceed the penalty threshold.
    5. Emit entity + relationship records to the knowledge store.
    """

    # Penalty points per violation type (base, before multipliers)
    BASE_PENALTIES: dict[ViolationType, int] = {
        ViolationType.BUDGET_EXCEEDED: 5,
        ViolationType.ORIGIN_DENIED: 10,
        ViolationType.CONTEXT_OVERFLOW: 8,
        ViolationType.INVALID_BODY: 3,
        ViolationType.MISSING_STRUCTURE: 3,
        ViolationType.PROFIT_MASKING: 15,  # base is already high, then 3x
        ViolationType.ENTITY_BANNERED: 0,  # bannered entities are already blocked
        ViolationType.VELOCITY_ANOMALY: 8,  # same weight as context overflow
    }

    # Type alias for the optional async persistence callback.
    PersistHook = Callable[[EntityRecord], Coroutine[Any, Any, None]]

    def __init__(
        self,
        banner_threshold: int = 50,
        profit_mask_multiplier: int = PROFIT_MASK_PENALTY_MULTIPLIER,
        knowledge_store: KnowledgeStoreProtocol | None = None,
        pattern_detector: PatternDetectorProtocol | None = None,
        persist_hook: PersistHook | None = None,
        entity_signing_secret: str = "",
    ) -> None:
        self._entities: dict[str, EntityRecord] = {}
        self._banner_threshold = banner_threshold
        self._profit_mask_multiplier = profit_mask_multiplier
        self._knowledge_store = knowledge_store
        self._pattern_detector = pattern_detector
        self._persist_hook = persist_hook
        self._entity_signing_secret = entity_signing_secret

        # Request-level counters (shared between middleware and router)
        self.total_admitted: int = 0
        self.total_rejected: int = 0
        self.rejection_reasons: dict[str, int] = defaultdict(int)

    def _fire_persist(self, record: EntityRecord) -> None:
        """Schedule async persistence without blocking the sync middleware path."""
        if not self._persist_hook:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._persist_hook(record))
        except RuntimeError:
            pass  # No event loop — skip persistence (e.g. in tests)

    # -- entity resolution --

    def resolve_entity(self, request: Request) -> str:
        """Resolve request to an entity identifier.

        Priority: X-Entity-Id header (HMAC-verified if secret set) > X-API-Key > client IP.
        If HMAC verification fails, the claimed entity ID is discarded and
        resolution falls through to API key or IP — silent fallthrough, not rejection.
        """
        entity_id = request.headers.get("X-Entity-Id", "").strip()
        if entity_id:
            if self._entity_signing_secret:
                from .entity_signing import verify_entity_signature

                sig = request.headers.get("X-Entity-Signature", "")
                ts = request.headers.get("X-Entity-Timestamp", "")
                if not verify_entity_signature(entity_id, sig, ts, self._entity_signing_secret):
                    # Unsigned/invalid claim — fall through to API key / IP
                    entity_id = ""
            if entity_id:
                return entity_id
        api_key = request.headers.get("X-API-Key", "").strip()
        if api_key:
            return f"api:{api_key[:16]}"
        host = request.client.host if request.client else "unknown"
        return f"ip:{host}"

    def get_record(self, entity_id: str) -> EntityRecord:
        """Get or create the record for an entity."""
        if entity_id not in self._entities:
            self._entities[entity_id] = EntityRecord(entity_id=entity_id)
        record = self._entities[entity_id]
        record.last_seen = time.monotonic()
        return record

    def update_drift(self, entity_id: str, drift_score: float) -> None:
        """Attach a vection drift score to an entity record.

        Called from the request dispatch path after VelocityTracker.track_event().
        drift_score is clamped to [0.0, 1.0].
        """
        record = self.get_record(entity_id)
        record.drift_score = max(0.0, min(1.0, drift_score))

    # -- profit-mask detection --

    def detect_profit_masking(
        self,
        payload: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
    ) -> list[str]:
        """Scan payload and headers for profit-maximization signals.

        Returns list of matched signals. Empty if clean.
        """
        search_space = ""

        if payload:
            search_space += json.dumps(payload, default=str).lower()
        if headers:
            search_space += " ".join(f"{k}={v}" for k, v in headers.items()).lower()

        return [signal for signal in PROFIT_MASK_SIGNALS if signal in search_space]

    # -- violation recording --

    def record_violation(
        self,
        entity_id: str,
        violation_type: ViolationType,
        *,
        profit_masked: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> EntityViolation:
        """Record a violation against an entity and apply penalties."""
        record = self.get_record(entity_id)

        base_penalty = self.BASE_PENALTIES.get(violation_type, 5)
        multiplier = self._profit_mask_multiplier if profit_masked else 1
        penalty_points = base_penalty * multiplier

        violation = EntityViolation(
            entity_id=entity_id,
            violation_type=violation_type,
            timestamp=time.monotonic(),
            penalty_points=penalty_points,
            metadata=metadata or {},
        )

        if profit_masked:
            violation.metadata["profit_mask_signals"] = True
            violation.metadata["penalty_multiplier"] = multiplier

        record.violations.append(violation)
        record.total_penalty_points += penalty_points

        # Check banner threshold
        if not record.bannered and record.total_penalty_points >= self._banner_threshold:
            record.bannered = True
            record.banner_reason = (
                f"penalty_threshold_exceeded: {record.total_penalty_points} >= {self._banner_threshold}"
            )
            logger.warning(
                "admission_gate.entity_bannered entity=%s points=%d reason=%s",
                entity_id,
                record.total_penalty_points,
                record.banner_reason,
            )
            self._emit_banner_to_knowledge_store(record)

        # Emit violation to knowledge store
        self._emit_violation_to_knowledge_store(violation, record)

        # Persist updated entity to SQLite (fire-and-forget)
        self._fire_persist(record)

        return violation

    # -- knowledge store integration --

    def _emit_violation_to_knowledge_store(self, violation: EntityViolation, record: EntityRecord) -> None:
        """Push violation as an Event entity + EXECUTED_BY relationship to the knowledge store."""
        if not self._knowledge_store:
            return

        try:
            from datetime import UTC, datetime

            from grid.knowledge.graph_schema import EntityType, RelationType
            from grid.knowledge.graph_store import Entity

            # Upsert the actor entity
            self._knowledge_store.store_entity(
                Entity(
                    entity_id=record.entity_id,
                    entity_type=EntityType.AGENT,
                    properties={
                        "total_penalty_points": record.total_penalty_points,
                        "violation_count": record.violation_count,
                        "bannered": record.bannered,
                        "banner_reason": record.banner_reason,
                        "drift_score": record.drift_score,
                    },
                    created_at=datetime.fromtimestamp(record.first_seen, tz=UTC),
                    updated_at=datetime.now(UTC),
                )
            )

            # Create an Event entity for the violation
            event_id = f"violation:{violation.entity_id}:{violation.timestamp}"
            self._knowledge_store.store_entity(
                Entity(
                    entity_id=event_id,
                    entity_type=EntityType.EVENT,
                    properties={
                        "violation_type": violation.violation_type.value,
                        "penalty_points": violation.penalty_points,
                        "profit_masked": violation.metadata.get("profit_mask_signals", False),
                        **violation.metadata,
                    },
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )

            # Link: violation -[EXECUTED_BY]-> actor
            self._knowledge_store.create_relationship(
                from_entity_id=event_id,
                to_entity_id=record.entity_id,
                relationship_type=RelationType.EXECUTED_BY,
                properties={"penalty_points": violation.penalty_points},
            )

        except Exception:
            logger.debug("admission_gate.knowledge_store_emit_failed", exc_info=True)

    def _emit_banner_to_knowledge_store(self, record: EntityRecord) -> None:
        """Push a banner decision to the knowledge store as a Decision entity."""
        if not self._knowledge_store:
            return

        try:
            from datetime import UTC, datetime

            from grid.knowledge.graph_schema import EntityType, RelationType
            from grid.knowledge.graph_store import Entity

            decision_id = f"banner:{record.entity_id}:{time.monotonic()}"
            self._knowledge_store.store_entity(
                Entity(
                    entity_id=decision_id,
                    entity_type=EntityType.DECISION,
                    properties={
                        "action": "banner",
                        "reason": record.banner_reason,
                        "total_penalty_points": record.total_penalty_points,
                        "violation_count": record.violation_count,
                        "profit_mask_violations": record.profit_mask_violations,
                    },
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )

            self._knowledge_store.create_relationship(
                from_entity_id=decision_id,
                to_entity_id=record.entity_id,
                relationship_type=RelationType.REFERENCES,
                properties={"action": "banner"},
            )

        except Exception:
            logger.debug("admission_gate.banner_emit_failed", exc_info=True)

    # -- budget reduction for penalized entities --

    def effective_budget(self, entity_id: str, base_budget: int) -> int:
        """Reduce budget proportionally to accumulated penalty points.

        Bannered entities get 0 budget (hard block).
        Penalized entities get budget reduced by penalty percentage.
        """
        record = self._entities.get(entity_id)
        if not record:
            return base_budget
        if record.bannered:
            return 0
        # Penalty reduction: lose 1% per penalty point, floor at 10% of original.
        # Drift surcharge: drift ≥ 0.5 adds up to 20% on top of the penalty reduction,
        # representing a session whose cognitive trajectory is too chaotic to trust at
        # full throughput. The floor stays at 10% so high-drift sessions aren't silenced.
        reduction_pct = min(record.total_penalty_points, 90) / 100.0
        drift_surcharge = max(0.0, (record.drift_score - 0.5) * 0.4)  # 0–20%
        total_reduction = min(reduction_pct + drift_surcharge, 0.90)
        return max(int(base_budget * (1.0 - total_reduction)), max(1, base_budget // 10))

    # -- merit standing integration --

    def check_merit_permission(
        self,
        entity_id: str,
        action_class: str,
        required_scope: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check entity permission using merit standing model.

        Args:
            entity_id: Entity to check
            action_class: ActionClass value (public_basic, analysis_read, action_write, control_admin)
            required_scope: Optional Scope value (read, write, admin, analysis, control)

        Returns:
            Tuple of (allowed, details dict)
        """
        engine = get_merit_engine()

        try:
            action = ActionClass(action_class)
        except ValueError:
            return False, {"error": f"invalid_action_class: {action_class}"}

        scope: Scope | None = None
        if required_scope:
            try:
                scope = Scope(required_scope)
            except ValueError:
                return False, {"error": f"invalid_scope: {required_scope}"}

        return engine.check_permission(entity_id, action, scope)

    def record_successful_action(self, entity_id: str) -> MeritStanding:
        """Record successful gated action for clean streak tracking."""
        engine = get_merit_engine()
        return engine.record_successful_action(entity_id)

    def get_merit_standing(self, entity_id: str) -> MeritStanding | None:
        """Get merit standing for an entity."""
        engine = get_merit_engine()
        return engine.get_standing(entity_id)

    def get_merit_leaderboard(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get merit leaderboard."""
        engine = get_merit_engine()
        return engine.get_leaderboard(limit)

    def apply_review_adjustment(self, entity_id: str, adjustment: int) -> MeritStanding:
        """Apply manual review adjustment to entity standing."""
        engine = get_merit_engine()
        return engine.apply_review_adjustment(entity_id, adjustment)

    # -- query interface --

    @property
    def entities(self) -> dict[str, EntityRecord]:
        return dict(self._entities)

    def bannered_entities(self) -> list[EntityRecord]:
        return [r for r in self._entities.values() if r.bannered]

    def entity_report(self, entity_id: str) -> dict[str, Any]:
        """Full report for an entity — suitable for audit or API exposure."""
        record = self._entities.get(entity_id)
        if not record:
            return {"entity_id": entity_id, "found": False}

        merit_data = {}
        if record.merit_standing:
            merit_data = record.merit_standing.to_dict()

        return {
            "entity_id": record.entity_id,
            "found": True,
            "violation_count": record.violation_count,
            "total_penalty_points": record.total_penalty_points,
            "bannered": record.bannered,
            "banner_reason": record.banner_reason,
            "profit_mask_violations": record.profit_mask_violations,
            "violations": [
                {
                    "type": v.violation_type.value,
                    "penalty_points": v.penalty_points,
                    "metadata": v.metadata,
                }
                for v in record.violations
            ],
            "merit_standing": merit_data,
        }

    def load_entities(self, entities: dict[str, EntityRecord]) -> None:
        """Hydrate in-memory entity store from persisted records (called at startup)."""
        self._entities.update(entities)
        logger.info("admission_gate.entities_hydrated count=%d", len(entities))

    @property
    def banner_threshold(self) -> int:
        return self._banner_threshold

    def peek_record(self, entity_id: str) -> EntityRecord | None:
        """Return record if it exists, without auto-creating."""
        return self._entities.get(entity_id)

    def persist_record(self, record: EntityRecord) -> None:
        """Public wrapper for fire-and-forget persistence."""
        self._fire_persist(record)

    def set_persist_hook(self, hook: PersistHook) -> None:
        """Wire the async persistence callback."""
        self._persist_hook = hook

    def reset(self) -> None:
        self._entities.clear()

    def reset_counters(self) -> None:
        """Reset request-level counters (for testing)."""
        self.total_admitted = 0
        self.total_rejected = 0
        self.rejection_reasons.clear()


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class AdmissionGateMiddleware(BaseHTTPMiddleware):
    """Top-of-stack admission filter with entity attribution + penalty.

    Added **last** in the middleware chain so it runs **first**.

    Execution chain:
    Billboard (policy display) → Gate 0 (banner check) → Gate 1 (budget) →
    Gate 2 (origin whitelist) → Gate 3a (context ceiling) →
    Gate 3b (JSON validity) → Gate 3c (structure) →
    Gate 3d (profit-mask detection) → Admitted
    """

    def __init__(
        self,
        app: ASGIApp,
        call_budget: int = DEFAULT_CALL_BUDGET,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        context_token_ceiling: int = DEFAULT_CONTEXT_TOKEN_CEILING,
        max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
        allowed_origins: frozenset[str] | None = None,
        bypass_paths: frozenset[str] | None = None,
        enforce_origin: bool = True,
        enforce_structure: bool = True,
        banner_threshold: int = 50,
        profit_mask_multiplier: int = PROFIT_MASK_PENALTY_MULTIPLIER,
        knowledge_store: KnowledgeStoreProtocol | None = None,
        pattern_detector: PatternDetectorProtocol | None = None,
        billboard: PolicyBillboard | None = None,
        attribution: EntityAttributionEngine | None = None,
    ) -> None:
        super().__init__(app)
        self._tracker = _BudgetTracker(call_budget, window_seconds)
        self._context_ceiling = context_token_ceiling
        self._max_body_bytes = max_body_bytes
        self._allowed_origins = allowed_origins or ALLOWED_ORIGINS
        self._bypass_paths = bypass_paths or BYPASS_PATHS
        self._enforce_origin = enforce_origin
        self._enforce_structure = enforce_structure

        self.attribution = (
            attribution
            if attribution is not None
            else EntityAttributionEngine(
                banner_threshold=banner_threshold,
                profit_mask_multiplier=profit_mask_multiplier,
                knowledge_store=knowledge_store,
                pattern_detector=pattern_detector,
            )
        )

        # Policy billboard — loaded once at boot, immutable
        self.billboard = billboard if billboard is not None else load_billboard()

    # -- public helpers for testing --

    def reset_counters(self) -> None:
        self.attribution.total_admitted = 0
        self.attribution.total_rejected = 0
        self.attribution.rejection_reasons.clear()
        self._tracker.reset()
        self.attribution.reset()

    # -- internals --

    def _reject(
        self,
        entity_id: str,
        code: str,
        message: str,
        status_code: int,
        violation_type: ViolationType,
        *,
        profit_masked: bool = False,
        headers: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> JSONResponse:
        self.attribution.total_rejected += 1
        self.attribution.rejection_reasons[code] += 1

        # Record violation with entity attribution
        self.attribution.record_violation(
            entity_id,
            violation_type,
            profit_masked=profit_masked,
            metadata=metadata,
        )

        record = self.attribution.get_record(entity_id)
        logger.warning(
            "admission_gate.rejected entity=%s code=%s points=%d bannered=%s msg=%s",
            entity_id,
            code,
            record.total_penalty_points,
            record.bannered,
            message,
        )

        # Classify the penalty tier for this violation
        if profit_masked:
            penalty_tier = "intentional_scheming"
            tier_description = self.billboard.tier_intentional_scheming
        elif record.total_penalty_points > 0 and record.violation_count > 1:
            penalty_tier = "environment_pollution"
            tier_description = self.billboard.tier_environment_pollution
        else:
            penalty_tier = "runtime_mistake"
            tier_description = self.billboard.tier_runtime_mistake

        response_body: dict[str, Any] = {
            "success": False,
            "error": {"code": code, "message": message},
            "entity_id": entity_id,
            "penalty_points": record.total_penalty_points,
            "penalty_tier": penalty_tier,
            "tier_description": tier_description,
            "policy": self.billboard.snapshot(),
        }
        if record.bannered:
            response_body["bannered"] = True
            response_body["banner_reason"] = record.banner_reason

        all_headers = headers or {}
        all_headers["X-Policy-Billboard"] = self.billboard.summary()

        return JSONResponse(
            status_code=status_code,
            content=response_body,
            headers=all_headers,
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Bypass non-API paths (tightened: minimal infra bypass only)
        if any(path == bp or path.startswith(bp + "/") for bp in self._bypass_paths):
            return await call_next(request)

        # Auth-protected routes should return 401 when unauthenticated.
        # Admission gating must not mask auth failures with 403s.
        if (path.startswith("/api/v1/agentic/") or path == "/api/v1/payment/webhook") and not request.headers.get(
            "Authorization"
        ):
            return await call_next(request)

        entity_id = self.attribution.resolve_entity(request)

        # --- Vection drift update + anomaly check ---
        # Track this request in the entity's VelocityTracker, push confidence-weighted
        # drift into the EntityRecord before effective_budget() reads it, then run
        # check_velocity_anomaly() and record violations for HIGH/CRITICAL alerts.
        try:
            from vection.core.velocity_tracker import get_velocity_registry
            from vection.security.anomaly_detector import AlertSeverity, get_anomaly_detector

            tracker = get_velocity_registry().get_or_create(entity_id)
            velocity = tracker.track_event({"action": request.method, "query": request.url.path})

            # Confidence-weighted drift: low-confidence readings don't over-penalize.
            self.attribution.update_drift(entity_id, velocity.drift * velocity.confidence)

            anomaly_alert = get_anomaly_detector().check_velocity_anomaly(
                session_id=entity_id,
                velocity_magnitude=velocity.magnitude,
                velocity_direction=velocity.direction.value,
                momentum=velocity.momentum,
                drift=velocity.drift,
            )
            if anomaly_alert and anomaly_alert.severity in (AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL):
                self.attribution.record_violation(
                    entity_id,
                    ViolationType.VELOCITY_ANOMALY,
                    metadata={
                        "anomaly_type": anomaly_alert.anomaly_type.value,
                        "severity": anomaly_alert.severity.value,
                        "drift": velocity.drift,
                        "momentum": velocity.momentum,
                    },
                )
        except Exception:
            pass  # Vection is best-effort; never let it block admission

        # --- Gate 0: Banner check (hard block) ---
        record = self.attribution.get_record(entity_id)
        if record.bannered:
            return self._reject(
                entity_id,
                "ADMISSION_ENTITY_BANNERED",
                f"Entity '{entity_id}' is bannered: {record.banner_reason}",
                status.HTTP_403_FORBIDDEN,
                ViolationType.ENTITY_BANNERED,
            )

        # --- Gate 1: Budget (adjusted by penalty) ---
        effective_budget = self.attribution.effective_budget(entity_id, self._tracker.default_budget)
        if not self._tracker.allow(entity_id, effective_budget=effective_budget):
            return self._reject(
                entity_id,
                "ADMISSION_BUDGET_EXCEEDED",
                f"Call budget exceeded (effective: {effective_budget}).",
                status.HTTP_429_TOO_MANY_REQUESTS,
                ViolationType.BUDGET_EXCEEDED,
                headers={
                    "Retry-After": "60",
                    "X-Admission-Remaining": "0",
                },
            )

        # --- Gate 2: Origin whitelist ---
        if self._enforce_origin:
            origin = request.headers.get("X-Admission-Origin", "").strip().lower()
            if origin and origin not in self._allowed_origins:
                return self._reject(
                    entity_id,
                    "ADMISSION_ORIGIN_DENIED",
                    f"Origin '{origin}' is not permitted.",
                    status.HTTP_403_FORBIDDEN,
                    ViolationType.ORIGIN_DENIED,
                    metadata={"origin": origin},
                )

        # --- Gates 3 & 4: Body checks (POST/PUT/PATCH only) ---
        if self._enforce_structure and request.method in {"POST", "PUT", "PATCH"}:
            body = await request.body()

            # 3a: Context ceiling
            estimated_tokens = len(body) // 4
            if estimated_tokens > self._context_ceiling:
                return self._reject(
                    entity_id,
                    "ADMISSION_CONTEXT_OVERFLOW",
                    f"Estimated context tokens ({estimated_tokens}) exceed ceiling ({self._context_ceiling}).",
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    ViolationType.CONTEXT_OVERFLOW,
                    metadata={"estimated_tokens": estimated_tokens},
                )

            # 3b: JSON validity
            parsed: dict[str, Any] | None = None
            if body:
                try:
                    parsed = json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return self._reject(
                        entity_id,
                        "ADMISSION_INVALID_BODY",
                        "Request body is not valid JSON.",
                        status.HTTP_422_UNPROCESSABLE_CONTENT,
                        ViolationType.INVALID_BODY,
                    )

                # 3c: Structure check for intelligence paths
                if "/intelligence/" in path and isinstance(parsed, dict):
                    if "data" not in parsed:
                        return self._reject(
                            entity_id,
                            "ADMISSION_MISSING_STRUCTURE",
                            "Intelligence pipeline requires 'data' key in payload.",
                            status.HTTP_422_UNPROCESSABLE_CONTENT,
                            ViolationType.MISSING_STRUCTURE,
                        )

            # --- Gate 3d: Profit-mask detection ---
            headers_dict = dict(request.headers)
            signals = self.attribution.detect_profit_masking(
                parsed if isinstance(parsed, dict) else None,
                headers_dict,
            )
            if signals:
                return self._reject(
                    entity_id,
                    "ADMISSION_PROFIT_MASKING",
                    f"Profit-maximization signals detected: {', '.join(signals)}. 3x penalty applied.",
                    status.HTTP_403_FORBIDDEN,
                    ViolationType.PROFIT_MASKING,
                    profit_masked=True,
                    metadata={"signals": signals},
                )

        # --- Gate 4: Merit Standing Check (for protected paths) ---
        # Determine action class from route metadata (if available) or path
        action_class = self._resolve_action_class(request, path)
        required_scope = self._resolve_required_scope(request, path)

        # Check merit permission
        allowed, permission_details = self.attribution.check_merit_permission(entity_id, action_class, required_scope)
        if not allowed:
            return self._reject(
                entity_id,
                "ADMISSION_INSUFFICIENT_MERIT",
                f"Entity '{entity_id}' lacks required merit standing for {action_class}. "
                f"Current: {permission_details.get('actual_badge', 'unknown')}, "
                f"Required: {permission_details.get('required_badge', 'unknown')}",
                status.HTTP_403_FORBIDDEN,
                ViolationType.ENTITY_BANNERED,  # Using bannered as proxy for insufficient merit
                metadata=permission_details,
            )

        # --- Admitted ---
        self.attribution.total_admitted += 1
        # Record successful action for clean streak
        self.attribution.record_successful_action(entity_id)

        remaining = self._tracker.remaining(entity_id, effective_budget=effective_budget)
        response = await call_next(request)
        response.headers["X-Admission-Remaining"] = str(remaining)
        response.headers["X-Entity-Penalty"] = str(record.total_penalty_points)
        response.headers["X-Policy-Billboard"] = self.billboard.summary()
        response.headers["X-Policy-Version"] = BILLBOARD_VERSION

        # Add merit standing headers
        if record.merit_standing:
            response.headers["X-Merit-Badge"] = record.merit_standing.badge.value
            response.headers["X-Merit-Score"] = str(record.merit_standing.score)
            response.headers["X-Merit-Roll"] = str(record.merit_standing.roll_number)

        return response

    def _resolve_action_class(self, request: Request, path: str) -> str:
        """Resolve action class from route metadata or path patterns."""
        action_class = getattr(request.state, "action_class", None)
        if action_class:
            return action_class

        if "/admin/" in path or "/control/" in path:
            return ActionClass.CONTROL_ADMIN.value

        if path.startswith("/admission/") and path.endswith("/check-permission"):
            return ActionClass.PUBLIC_BASIC.value

        if "/write/" in path or "/action/" in path or request.method in {"POST", "PUT", "DELETE", "PATCH"}:
            return ActionClass.ACTION_WRITE.value
        if "/analysis/" in path or "/read/" in path or request.method == "GET":
            return ActionClass.ANALYSIS_READ.value

        return ActionClass.PUBLIC_BASIC.value

    def _resolve_required_scope(self, request: Request, path: str) -> str | None:
        """Resolve required scope from route metadata or path patterns."""
        # Check for explicit scope in request state (set by api_sentinels)
        scope = getattr(request.state, "required_scope", None)
        if scope:
            return scope

        # Path-based heuristic
        if "/admin/" in path:
            return Scope.ADMIN.value
        if "/write/" in path or "/action/" in path:
            return Scope.WRITE.value

        return None
