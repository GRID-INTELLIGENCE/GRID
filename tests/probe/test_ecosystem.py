"""Tests for the ecosystem bridge — probe integration with echoes and seeds."""

from __future__ import annotations

import pytest

from grid.probe.ecosystem import (
    AuditEvent,
    AuditStatus,
    EcosystemBridge,
    EcosystemSnapshot,
    EnforcementState,
    EscalationLevel,
    HealthTier,
    LineAuditResult,
    LumosVerdict,
    Precedent,
    RepoHealth,
)

# ── Fixtures ──


@pytest.fixture
def sample_audit_events() -> list[dict]:
    return [
        {
            "source": "grid-server",
            "tool": "validate_envelope",
            "status": "success",
            "timestamp": "2026-04-09T06:00:00.000Z",
            "durationMs": 12.5,
            "metadata": {"envelopePath": "/path/to/envelope.json"},
        },
        {
            "source": "seeds-server",
            "tool": "ecosystem_scan",
            "status": "success",
            "timestamp": "2026-04-09T06:01:00.000Z",
            "durationMs": 0,
            "metadata": {"overallScore": 88},
        },
        {
            "source": "grid-server",
            "tool": "validate_envelope",
            "status": "failure",
            "timestamp": "2026-04-09T06:02:00.000Z",
            "metadata": {"checksFailed": ["trusted_source"]},
        },
        {
            "source": "maintain-server",
            "tool": "cleanup_execute",
            "status": "error",
            "timestamp": "2026-04-09T06:03:00.000Z",
        },
    ]


@pytest.fixture
def sample_enforcement() -> dict:
    return {
        "status": "normal",
        "totalActive": 4,
        "byLevel": {
            "observed": 4,
            "flagged": 0,
            "restricted": 0,
            "blocked": 0,
        },
        "recentPrecedents": [
            {
                "id": "prec-001",
                "source": "maintain-server",
                "tool": "audit_throughput_probe",
                "category": "tool_failure",
                "occurrences": 1,
                "level": "observed",
                "lastSeen": "2026-03-29T00:14:54.534Z",
            },
            {
                "id": "prec-002",
                "source": "grid-server",
                "tool": "validate_envelope",
                "category": "integrity_error",
                "occurrences": 1,
                "level": "observed",
                "lastSeen": "2026-03-28T20:16:51.128Z",
            },
        ],
    }


@pytest.fixture
def sample_ecosystem() -> dict:
    return {
        "summary": {
            "overallScore": 88,
            "totalRepos": 8,
            "active": 7,
            "stale": 1,
            "totalIssues": 3,
        },
        "repos": [
            {
                "name": "GRID",
                "healthScore": 90,
                "branch": "main",
                "uncommitted": 11,
                "lastCommit": "48 minutes ago",
                "issues": ["11 uncommitted changes"],
                "stack": "Python 3.13+, FastAPI",
            },
            {
                "name": "afloat",
                "healthScore": 100,
                "branch": "hogsmade",
                "uncommitted": 0,
                "lastCommit": "47 minutes ago",
                "issues": [],
                "stack": "TypeScript, Next.js",
            },
            {
                "name": "upwork-cli",
                "healthScore": 35,
                "branch": "",
                "uncommitted": 0,
                "lastCommit": "",
                "issues": ["No git repository found"],
                "stack": "unknown",
            },
        ],
    }


@pytest.fixture
def sample_line_audit_clean() -> dict:
    return {
        "clean": True,
        "errorCount": 0,
        "warningCount": 0,
        "fixableCount": 0,
        "fixedCount": 0,
        "summary": "Line is clean. 6 rules, 0 findings.",
        "findings": [],
    }


@pytest.fixture
def sample_line_audit_dirty() -> dict:
    return {
        "clean": False,
        "errorCount": 3,
        "warningCount": 2,
        "fixableCount": 2,
        "fixedCount": 0,
        "summary": "3 errors, 2 warnings, 2 fixable",
        "findings": [
            {"rule": "specifier-consistency", "severity": "error", "file": "src/server.ts"},
        ],
    }


@pytest.fixture
def bridge() -> EcosystemBridge:
    return EcosystemBridge()


# ── AuditEvent Tests ──


class TestAuditEvent:
    def test_create_from_valid_data(self):
        event = AuditEvent(
            source="grid-server",
            tool="validate_envelope",
            status=AuditStatus.SUCCESS,
            timestamp="2026-04-09T06:00:00Z",
        )
        assert event.source == "grid-server"
        assert event.status == AuditStatus.SUCCESS

    def test_to_dict(self):
        event = AuditEvent(
            source="test",
            tool="tool",
            status=AuditStatus.FAILURE,
            timestamp="2026-01-01T00:00:00Z",
            duration_ms=42.0,
        )
        d = event.to_dict()
        assert d["source"] == "test"
        assert d["status"] == "failure"
        assert d["duration_ms"] == 42.0

    def test_status_enum_values(self):
        assert AuditStatus.SUCCESS == "success"
        assert AuditStatus.FAILURE == "failure"
        assert AuditStatus.BLOCKED == "blocked"
        assert AuditStatus.DRY_RUN == "dry_run"
        assert AuditStatus.ERROR == "error"


# ── Precedent Tests ──


class TestPrecedent:
    def test_create(self):
        p = Precedent(
            id="prec-001",
            source="grid-server",
            tool="validate_envelope",
            category="integrity_error",
            occurrences=3,
            level=EscalationLevel.FLAGGED,
            last_seen="2026-04-09T06:00:00Z",
        )
        assert p.level == EscalationLevel.FLAGGED
        assert p.occurrences == 3

    def test_to_dict(self):
        p = Precedent(
            id="prec-x",
            source="s",
            tool="t",
            category="c",
            occurrences=1,
            level=EscalationLevel.BLOCKED,
            last_seen="ts",
        )
        d = p.to_dict()
        assert d["level"] == "blocked"
        assert d["id"] == "prec-x"


# ── RepoHealth Tests ──


class TestRepoHealth:
    def test_tier_excellent(self):
        r = RepoHealth("GRID", 95, "main", 0, "1h ago")
        assert r.tier == HealthTier.EXCELLENT

    def test_tier_healthy(self):
        r = RepoHealth("hogsmade", 75, "hogsmade", 12, "30m ago")
        assert r.tier == HealthTier.HEALTHY

    def test_tier_degraded(self):
        r = RepoHealth("test", 55, "main", 0, "1d ago")
        assert r.tier == HealthTier.DEGRADED

    def test_tier_failing(self):
        r = RepoHealth("upwork-cli", 35, "", 0, "")
        assert r.tier == HealthTier.FAILING

    def test_to_dict_includes_tier(self):
        r = RepoHealth("GRID", 90, "main", 0, "1h ago")
        d = r.to_dict()
        assert d["tier"] == "excellent"
        assert d["name"] == "GRID"


# ── EnforcementState Tests ──


class TestEnforcementState:
    def test_no_blocks(self):
        state = EnforcementState(
            status="normal",
            total_active=2,
            by_level={"observed": 2, "blocked": 0},
            precedents=(),
        )
        assert not state.has_blocks
        assert not state.has_restrictions

    def test_has_blocks(self):
        state = EnforcementState(
            status="elevated",
            total_active=1,
            by_level={"blocked": 1},
            precedents=(),
        )
        assert state.has_blocks

    def test_has_restrictions(self):
        state = EnforcementState(
            status="elevated",
            total_active=1,
            by_level={"restricted": 1},
            precedents=(),
        )
        assert state.has_restrictions


# ── LineAuditResult Tests ──


class TestLineAuditResult:
    def test_clean_result(self, sample_line_audit_clean):
        result = LineAuditResult(
            clean=True,
            error_count=0,
            warning_count=0,
            fixable_count=0,
            fixed_count=0,
            summary="Clean",
        )
        assert result.clean
        assert result.error_count == 0

    def test_dirty_result(self):
        result = LineAuditResult(
            clean=False,
            error_count=3,
            warning_count=2,
            fixable_count=2,
            fixed_count=0,
            summary="3 errors",
        )
        assert not result.clean
        assert result.error_count == 3


# ── LumosVerdict Tests ──


class TestLumosVerdict:
    def test_values(self):
        assert LumosVerdict.FAST_CLEAR == "FAST_CLEAR"
        assert LumosVerdict.WATCH == "WATCH"
        assert LumosVerdict.ACT == "ACT"
        assert LumosVerdict.URGENT == "URGENT"


# ── EcosystemBridge Tests ──


class TestEcosystemBridge:
    def test_ingest_audit_events(self, bridge, sample_audit_events):
        count = bridge.ingest_audit_events(sample_audit_events)
        assert count == 4
        assert len(bridge.audit_events) == 4
        assert bridge.audit_events[0].source == "grid-server"
        assert bridge.audit_events[2].status == AuditStatus.FAILURE

    def test_ingest_audit_skips_malformed(self, bridge):
        bad_events = [
            {"source": "test", "tool": "t", "status": "INVALID_STATUS", "timestamp": "ts"},
        ]
        count = bridge.ingest_audit_events(bad_events)
        assert count == 0

    def test_ingest_enforcement(self, bridge, sample_enforcement):
        state = bridge.ingest_enforcement(sample_enforcement)
        assert state.status == "normal"
        assert state.total_active == 4
        assert len(state.precedents) == 2
        assert state.precedents[0].source == "maintain-server"
        assert not state.has_blocks

    def test_ingest_ecosystem(self, bridge, sample_ecosystem):
        snapshot = bridge.ingest_ecosystem(sample_ecosystem)
        assert snapshot.overall_score == 88
        assert snapshot.total_repos == 8
        assert snapshot.active_repos == 7
        assert len(snapshot.repos) == 3
        assert snapshot.repos[0].name == "GRID"

    def test_ingest_line_audit_clean(self, bridge, sample_line_audit_clean):
        result = bridge.ingest_line_audit(sample_line_audit_clean)
        assert result.clean
        assert result.error_count == 0

    def test_ingest_line_audit_dirty(self, bridge, sample_line_audit_dirty):
        result = bridge.ingest_line_audit(sample_line_audit_dirty)
        assert not result.clean
        assert result.error_count == 3
        assert len(result.findings) == 1

    def test_compute_audit_stats(self, bridge, sample_audit_events):
        bridge.ingest_audit_events(sample_audit_events)
        stats = bridge.compute_audit_stats()
        assert stats["total"] == 4
        assert stats["by_status"]["success"] == 2
        assert stats["by_status"]["failure"] == 1
        assert stats["by_status"]["error"] == 1
        assert stats["fail_rate"] == 0.5  # 2 failures out of 4
        assert stats["by_source"]["grid-server"] == 2

    def test_compute_audit_stats_empty(self, bridge):
        stats = bridge.compute_audit_stats()
        assert stats["total"] == 0
        assert stats["fail_rate"] == 0.0

    def test_get_repo_health_found(self, bridge, sample_ecosystem):
        bridge.ingest_ecosystem(sample_ecosystem)
        repo = bridge.get_repo_health("GRID")
        assert repo is not None
        assert repo.health_score == 90

    def test_get_repo_health_case_insensitive(self, bridge, sample_ecosystem):
        bridge.ingest_ecosystem(sample_ecosystem)
        repo = bridge.get_repo_health("grid")
        assert repo is not None
        assert repo.name == "GRID"

    def test_get_repo_health_not_found(self, bridge, sample_ecosystem):
        bridge.ingest_ecosystem(sample_ecosystem)
        assert bridge.get_repo_health("nonexistent") is None

    def test_get_repo_health_no_ecosystem(self, bridge):
        assert bridge.get_repo_health("GRID") is None

    def test_get_failing_repos(self, bridge, sample_ecosystem):
        bridge.ingest_ecosystem(sample_ecosystem)
        failing = bridge.get_failing_repos()
        assert len(failing) == 1
        assert failing[0].name == "upwork-cli"

    def test_get_failing_repos_empty(self, bridge):
        assert bridge.get_failing_repos() == []

    def test_get_blocked_precedents_none(self, bridge, sample_enforcement):
        bridge.ingest_enforcement(sample_enforcement)
        blocked = bridge.get_blocked_precedents()
        assert len(blocked) == 0

    def test_get_blocked_precedents_with_blocks(self, bridge):
        raw = {
            "status": "elevated",
            "totalActive": 1,
            "byLevel": {"blocked": 1},
            "recentPrecedents": [
                {
                    "id": "prec-b",
                    "source": "test",
                    "tool": "fail",
                    "category": "error",
                    "occurrences": 5,
                    "level": "blocked",
                    "lastSeen": "2026-04-09T00:00:00Z",
                },
            ],
        }
        bridge.ingest_enforcement(raw)
        blocked = bridge.get_blocked_precedents()
        assert len(blocked) == 1
        assert blocked[0].level == EscalationLevel.BLOCKED

    def test_to_dict_full(
        self, bridge, sample_audit_events, sample_enforcement, sample_ecosystem, sample_line_audit_clean
    ):
        bridge.ingest_audit_events(sample_audit_events)
        bridge.ingest_enforcement(sample_enforcement)
        bridge.ingest_ecosystem(sample_ecosystem)
        bridge.ingest_line_audit(sample_line_audit_clean)

        d = bridge.to_dict()
        assert "audit_stats" in d
        assert "enforcement" in d
        assert "ecosystem" in d
        assert "line_audit" in d
        assert d["enforcement"]["status"] == "normal"
        assert d["ecosystem"]["overall_score"] == 88
        assert d["line_audit"]["clean"] is True

    def test_to_dict_empty(self, bridge):
        d = bridge.to_dict()
        assert d["enforcement"] is None
        assert d["ecosystem"] is None
        assert d["line_audit"] is None
        assert d["audit_stats"]["total"] == 0
