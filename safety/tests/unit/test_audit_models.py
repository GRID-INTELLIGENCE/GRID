"""
Unit tests for audit database models.
"""

from __future__ import annotations

import uuid

from safety.audit.models import (
    AuditRecord,
    AuditStatus,
    Severity,
    TrustTier,
)


class TestAuditRecord:
    def test_create_record(self):
        record = AuditRecord(
            id=uuid.uuid4(),
            request_id="req-001",
            user_id="user-001",
            trust_tier=TrustTier.USER,
            input="test input",
            model_output=None,
            detector_scores={"score": 0.9},
            reason_code="HIGH_RISK_BIO",
            severity=Severity.HIGH,
            status=AuditStatus.ESCALATED,
            trace_id="trace-001",
        )
        assert record.request_id == "req-001"
        assert record.severity == Severity.HIGH
        assert record.status == AuditStatus.ESCALATED
        assert record.model_output is None

    def test_severity_values(self):
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"

    def test_status_values(self):
        assert AuditStatus.OPEN.value == "open"
        assert AuditStatus.ESCALATED.value == "escalated"
        assert AuditStatus.RESOLVED.value == "resolved"

    def test_trust_tier_values(self):
        assert TrustTier.ANON.value == "anon"
        assert TrustTier.USER.value == "user"
        assert TrustTier.VERIFIED.value == "verified"
        assert TrustTier.PRIVILEGED.value == "privileged"

    def test_repr(self):
        record = AuditRecord(
            id=uuid.uuid4(),
            request_id="req-002",
            user_id="user-002",
            trust_tier=TrustTier.VERIFIED,
            input="test",
            detector_scores={},
            reason_code="TEST",
            severity=Severity.LOW,
            status=AuditStatus.OPEN,
            trace_id="trace-002",
        )
        rep = repr(record)
        assert "req-002" in rep
        assert "TEST" in rep
