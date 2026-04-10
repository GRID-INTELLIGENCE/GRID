"""Ecosystem bridge — connects probe to echoes-server and seeds-server pipelines.

The probe's governance analysis (Phase 2) produces internal findings about
GRID-main's middleware, auth, gating, and security entities. The ecosystem
bridge ingests *external* signals from the two parallel MCP processes:

1. **Echoes Enforcement Pipeline** — audit trail events, precedent tracking,
   escalation state. Provides behavioral enforcement data.
2. **Seeds Ecosystem Scan Pipeline** — repo health scores, uncommitted change
   counts, structural health. Provides structural health data.

The bridge normalizes these into probe-compatible models so the lumos
orchestrator can compute PATH scores across all three data sources.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default paths matching ecosystem conventions
_DEFAULT_AUDIT_PATH = Path.home() / ".echoes" / "audit.ndjson"
_DEFAULT_SNAPSHOTS_DIR = Path.home() / ".seeds-server" / "snapshots"
_DEFAULT_PRECEDENTS_PATH = Path.home() / ".echoes" / "precedents" / "precedent-store.json"


# ── Enums ──


class EscalationLevel(StrEnum):
    """Echoes precedent escalation level."""

    OBSERVED = "observed"
    FLAGGED = "flagged"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class AuditStatus(StrEnum):
    """Status of an audit event from echoes."""

    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    DRY_RUN = "dry_run"
    ERROR = "error"


class HealthTier(StrEnum):
    """Repository health classification from seeds."""

    EXCELLENT = "excellent"  # 90-100
    HEALTHY = "healthy"  # 70-89
    DEGRADED = "degraded"  # 50-69
    FAILING = "failing"  # 0-49


class LumosVerdict(StrEnum):
    """Lumos fast-lane verdict from combined signals."""

    FAST_CLEAR = "FAST_CLEAR"  # 65-100 — proceed normally
    WATCH = "WATCH"  # 50-64  — proceed with monitoring
    ACT = "ACT"  # 35-49  — targeted remediation
    URGENT = "URGENT"  # 0-34   — stop and fix


# ── Data Models ──


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Normalized audit event from echoes-server."""

    source: str
    tool: str
    status: AuditStatus
    timestamp: str
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "tool": self.tool,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class Precedent:
    """Normalized precedent from echoes enforcement."""

    id: str
    source: str
    tool: str
    category: str
    occurrences: int
    level: EscalationLevel
    last_seen: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "tool": self.tool,
            "category": self.category,
            "occurrences": self.occurrences,
            "level": self.level.value,
            "last_seen": self.last_seen,
        }


@dataclass(frozen=True, slots=True)
class RepoHealth:
    """Normalized repo health from seeds-server."""

    name: str
    health_score: int
    branch: str
    uncommitted: int
    last_commit: str
    issues: tuple[str, ...] = ()
    stack: str = ""

    @property
    def tier(self) -> HealthTier:
        if self.health_score >= 90:
            return HealthTier.EXCELLENT
        if self.health_score >= 70:
            return HealthTier.HEALTHY
        if self.health_score >= 50:
            return HealthTier.DEGRADED
        return HealthTier.FAILING

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "health_score": self.health_score,
            "branch": self.branch,
            "uncommitted": self.uncommitted,
            "last_commit": self.last_commit,
            "issues": list(self.issues),
            "tier": self.tier.value,
            "stack": self.stack,
        }


@dataclass(frozen=True, slots=True)
class EnforcementState:
    """Normalized enforcement status from echoes."""

    status: str  # "normal", "elevated", "critical"
    total_active: int
    by_level: dict[str, int]
    precedents: tuple[Precedent, ...]

    @property
    def has_blocks(self) -> bool:
        return self.by_level.get("blocked", 0) > 0

    @property
    def has_restrictions(self) -> bool:
        return self.by_level.get("restricted", 0) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "total_active": self.total_active,
            "by_level": self.by_level,
            "has_blocks": self.has_blocks,
            "has_restrictions": self.has_restrictions,
            "precedents": [p.to_dict() for p in self.precedents],
        }


@dataclass(frozen=True, slots=True)
class EcosystemSnapshot:
    """Normalized ecosystem scan from seeds-server."""

    overall_score: int
    total_repos: int
    active_repos: int
    stale_repos: int
    repos: tuple[RepoHealth, ...]
    scanned_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "total_repos": self.total_repos,
            "active_repos": self.active_repos,
            "stale_repos": self.stale_repos,
            "repos": [r.to_dict() for r in self.repos],
            "scanned_at": self.scanned_at,
        }


@dataclass(frozen=True, slots=True)
class LineAuditResult:
    """Normalized result from eligibility-server check_the_line."""

    clean: bool
    error_count: int
    warning_count: int
    fixable_count: int
    fixed_count: int
    summary: str
    findings: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "fixable_count": self.fixable_count,
            "fixed_count": self.fixed_count,
            "summary": self.summary,
            "findings": list(self.findings),
        }


@dataclass(slots=True)
class EcosystemBridge:
    """Bridge between probe internals and ecosystem MCP processes.

    Ingests data from three sources:
    - Echoes audit trail + enforcement state
    - Seeds ecosystem health snapshots
    - Eligibility line audit results

    Normalizes everything into typed models that the lumos orchestrator
    can consume for PATH score computation.
    """

    audit_events: list[AuditEvent] = field(default_factory=list)
    enforcement: EnforcementState | None = None
    ecosystem: EcosystemSnapshot | None = None
    line_audit: LineAuditResult | None = None

    # ── Ingest methods ──

    def ingest_audit_events(self, raw_events: list[dict[str, Any]]) -> int:
        """Parse raw echoes audit events into typed models.

        Args:
            raw_events: List of audit event dicts from echoes-server.

        Returns:
            Number of events ingested.
        """
        count = 0
        for raw in raw_events:
            try:
                event = AuditEvent(
                    source=raw.get("source", "unknown"),
                    tool=raw.get("tool", "unknown"),
                    status=AuditStatus(raw.get("status", "error")),
                    timestamp=raw.get("timestamp", ""),
                    duration_ms=raw.get("durationMs", 0.0),
                    metadata=raw.get("metadata", {}),
                )
                self.audit_events.append(event)
                count += 1
            except (ValueError, KeyError) as exc:
                logger.debug("Skipping malformed audit event: %s", exc)
        return count

    def ingest_enforcement(self, raw: dict[str, Any]) -> EnforcementState:
        """Parse raw echoes enforcement status.

        Args:
            raw: Enforcement status dict from echoes-server.

        Returns:
            Normalized EnforcementState.
        """
        precedents = tuple(
            Precedent(
                id=p.get("id", ""),
                source=p.get("source", ""),
                tool=p.get("tool", ""),
                category=p.get("category", ""),
                occurrences=p.get("occurrences", 0),
                level=EscalationLevel(p.get("level", "observed")),
                last_seen=p.get("lastSeen", ""),
            )
            for p in raw.get("recentPrecedents", [])
        )
        self.enforcement = EnforcementState(
            status=raw.get("status", "unknown"),
            total_active=raw.get("totalActive", 0),
            by_level=raw.get("byLevel", {}),
            precedents=precedents,
        )
        return self.enforcement

    def ingest_ecosystem(self, raw: dict[str, Any]) -> EcosystemSnapshot:
        """Parse raw seeds ecosystem scan.

        Args:
            raw: Ecosystem scan dict from seeds-server.

        Returns:
            Normalized EcosystemSnapshot.
        """
        summary = raw.get("summary", raw)
        repos = tuple(
            RepoHealth(
                name=r.get("name", ""),
                health_score=r.get("healthScore", 0),
                branch=r.get("branch", ""),
                uncommitted=r.get("uncommitted", 0),
                last_commit=r.get("lastCommit", ""),
                issues=tuple(r.get("issues", [])),
                stack=r.get("stack", ""),
            )
            for r in raw.get("repos", [])
        )
        self.ecosystem = EcosystemSnapshot(
            overall_score=summary.get("overallScore", 0),
            total_repos=summary.get("totalRepos", 0),
            active_repos=summary.get("active", summary.get("existing", 0)),
            stale_repos=summary.get("stale", 0),
            repos=repos,
            scanned_at=datetime.now().isoformat(),
        )
        return self.ecosystem

    def ingest_line_audit(self, raw: dict[str, Any]) -> LineAuditResult:
        """Parse raw eligibility-server check_the_line result.

        Args:
            raw: Line audit result dict.

        Returns:
            Normalized LineAuditResult.
        """
        self.line_audit = LineAuditResult(
            clean=raw.get("clean", False),
            error_count=raw.get("errorCount", 0),
            warning_count=raw.get("warningCount", 0),
            fixable_count=raw.get("fixableCount", 0),
            fixed_count=raw.get("fixedCount", 0),
            summary=raw.get("summary", ""),
            findings=tuple(raw.get("findings", [])),
        )
        return self.line_audit

    # ── Aggregation methods ──

    def compute_audit_stats(self) -> dict[str, Any]:
        """Compute aggregate statistics from ingested audit events.

        Returns:
            Dict with counts by status, source, and tool.
        """
        by_status: dict[str, int] = {}
        by_source: dict[str, int] = {}
        by_tool: dict[str, int] = {}
        total_duration = 0.0

        for event in self.audit_events:
            by_status[event.status.value] = by_status.get(event.status.value, 0) + 1
            by_source[event.source] = by_source.get(event.source, 0) + 1
            by_tool[event.tool] = by_tool.get(event.tool, 0) + 1
            total_duration += event.duration_ms

        total = len(self.audit_events)
        fail_count = by_status.get("failure", 0) + by_status.get("error", 0)
        return {
            "total": total,
            "by_status": by_status,
            "by_source": by_source,
            "by_tool": by_tool,
            "fail_rate": round(fail_count / total, 4) if total > 0 else 0.0,
            "avg_duration_ms": round(total_duration / total, 2) if total > 0 else 0.0,
        }

    def get_repo_health(self, name: str) -> RepoHealth | None:
        """Look up a specific repo's health by name.

        Args:
            name: Repository name (e.g. "GRID", "hogsmade").

        Returns:
            RepoHealth if found, None otherwise.
        """
        if self.ecosystem is None:
            return None
        for repo in self.ecosystem.repos:
            if repo.name.lower() == name.lower():
                return repo
        return None

    def get_failing_repos(self) -> list[RepoHealth]:
        """Get repos with health score below 50.

        Returns:
            List of failing RepoHealth entries.
        """
        if self.ecosystem is None:
            return []
        return [r for r in self.ecosystem.repos if r.health_score < 50]

    def get_blocked_precedents(self) -> list[Precedent]:
        """Get precedents at blocked or restricted level.

        Returns:
            List of high-severity Precedent entries.
        """
        if self.enforcement is None:
            return []
        return [
            p for p in self.enforcement.precedents if p.level in (EscalationLevel.BLOCKED, EscalationLevel.RESTRICTED)
        ]

    def to_dict(self) -> dict[str, Any]:
        """Full serialized state of the ecosystem bridge."""
        return {
            "audit_stats": self.compute_audit_stats(),
            "enforcement": self.enforcement.to_dict() if self.enforcement else None,
            "ecosystem": self.ecosystem.to_dict() if self.ecosystem else None,
            "line_audit": self.line_audit.to_dict() if self.line_audit else None,
        }

    # ── File-based ingestion helpers ──

    @staticmethod
    def load_audit_from_ndjson(
        path: Path | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Load recent audit events from the echoes NDJSON file.

        Args:
            path: Path to audit.ndjson. Defaults to ~/.echoes/audit.ndjson.
            limit: Maximum number of recent events to load.

        Returns:
            List of raw audit event dicts.
        """
        audit_path = path or _DEFAULT_AUDIT_PATH
        if not audit_path.exists():
            logger.warning("Audit file not found: %s", audit_path)
            return []

        events: list[dict[str, Any]] = []
        try:
            lines = audit_path.read_text().strip().splitlines()
            for line in lines[-limit:]:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError as exc:
            logger.warning("Failed to read audit file: %s", exc)
        return events

    @staticmethod
    def load_latest_snapshot(
        snapshots_dir: Path | None = None,
    ) -> dict[str, Any] | None:
        """Load the most recent seeds ecosystem snapshot.

        Args:
            snapshots_dir: Directory containing snapshot files.

        Returns:
            Parsed snapshot dict, or None if unavailable.
        """
        snap_dir = snapshots_dir or _DEFAULT_SNAPSHOTS_DIR
        if not snap_dir.exists():
            logger.warning("Snapshots directory not found: %s", snap_dir)
            return None

        files = sorted(snap_dir.glob("snapshot-*.json"))
        if not files:
            logger.warning("No snapshots found in %s", snap_dir)
            return None

        try:
            return json.loads(files[-1].read_text())
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read snapshot: %s", exc)
            return None

    @staticmethod
    def load_precedents(
        path: Path | None = None,
    ) -> dict[str, Any]:
        """Load the precedent store from echoes.

        Args:
            path: Path to precedent-store.json.

        Returns:
            Parsed precedent store dict.
        """
        prec_path = path or _DEFAULT_PRECEDENTS_PATH
        if not prec_path.exists():
            logger.warning("Precedent store not found: %s", prec_path)
            return {}

        try:
            return json.loads(prec_path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read precedent store: %s", exc)
            return {}
