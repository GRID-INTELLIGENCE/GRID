"""Tracks embedded intelligence and decision-making patterns with persistence.

Features:
- In-memory record storage
- Immediate persistence to SQLite (important decisions shouldn't be lost)
- Graceful degradation when inventory unavailable
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .intelligence_inventory import IntelligenceInventory

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    ROUTING = "routing"
    FALLBACK = "fallback"
    ADAPTATION = "adaptation"
    RETRY = "retry"


@dataclass
class IntelligenceRecord:
    skill_id: str
    decision_type: DecisionType
    context: dict[str, Any]
    confidence: float
    rationale: str
    alternatives: list[str]
    outcome: str
    timestamp: float


class IntelligenceTracker:
    """Tracks embedded intelligence and decision-making patterns.

    Uses immediate persistence (not batched) since intelligence decisions
    are less frequent but more important than executions.

    Configuration:
    - GRID_SKILLS_PERSIST_MODE: batch|immediate|off (default: batch)
    """

    _instance: IntelligenceTracker | None = None

    PERSIST_MODE = os.getenv("GRID_SKILLS_PERSIST_MODE", "batch")

    def __init__(self):
        self._records: list[IntelligenceRecord] = []
        self._logger = logging.getLogger(__name__)

        # Lazy inventory connection
        self._inventory: IntelligenceInventory | None = None
        self._inventory_available = True

    @classmethod
    def get_instance(cls) -> IntelligenceTracker:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_inventory(self) -> IntelligenceInventory | None:
        """Lazy load inventory connection."""
        if not self._inventory_available:
            return None

        if self._inventory is None:
            try:
                from .intelligence_inventory import IntelligenceInventory

                self._inventory = IntelligenceInventory.get_instance()
                self._logger.debug("IntelligenceTracker connected to inventory")
            except Exception as e:
                self._logger.warning(f"IntelligenceInventory unavailable: {e}")
                self._inventory_available = False
                return None

        return self._inventory

    def track_decision(
        self,
        skill_id: str,
        decision_type: DecisionType,
        context: dict[str, Any],
        confidence: float,
        rationale: str,
        alternatives: list[str],
        outcome: str,
    ) -> IntelligenceRecord:
        """Track an intelligence decision with immediate persistence."""
        record = IntelligenceRecord(
            skill_id=skill_id,
            decision_type=decision_type,
            context=context,
            confidence=confidence,
            rationale=rationale,
            alternatives=alternatives,
            outcome=outcome,
            timestamp=time.time(),
        )

        # Add to in-memory history
        self._records.append(record)
        self._logger.debug(f"Tracked {decision_type.value} decision for {skill_id} (confidence={confidence})")

        # Persist immediately (intelligence decisions are important)
        if self.PERSIST_MODE != "off":
            self._persist_record(record)

        return record

    def _persist_record(self, record: IntelligenceRecord) -> None:
        """Persist a single intelligence record."""
        inventory = self._get_inventory()
        if inventory:
            try:
                inventory.store_intelligence(record)
                inventory.flush_all()
            except Exception as e:
                self._logger.error(f"Failed to persist intelligence record: {e}")

    def get_intelligence_patterns(self, skill_id: str | None = None) -> dict[str, Any]:
        """Analyze intelligence patterns from memory."""
        records = self._records if not skill_id else [r for r in self._records if r.skill_id == skill_id]

        if not records:
            return {"error": "No intelligence records found"}

        # Calculate metrics
        by_type: dict[str, int] = {}
        for record in records:
            by_type[record.decision_type.value] = by_type.get(record.decision_type.value, 0) + 1

        avg_confidence = sum(r.confidence for r in records) / len(records)
        success_rate = sum(1 for r in records if r.outcome == "success") / len(records)

        return {
            "total_decisions": len(records),
            "by_type": by_type,
            "avg_confidence": avg_confidence,
            "success_rate": success_rate,
            "common_rationale": self._get_common_rationale(records),
        }

    def _get_common_rationale(self, records: list[IntelligenceRecord]) -> list[str]:
        """Get most common rationale patterns."""
        rationale_counts: dict[str, int] = {}
        for record in records:
            rationale = record.rationale.split()[0] if record.rationale else "unknown"
            rationale_counts[rationale] = rationale_counts.get(rationale, 0) + 1

        return [r for r, count in sorted(rationale_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    def get_confidence_trends(self, skill_id: str) -> dict[str, Any]:
        """Get confidence trends over time."""
        records = [r for r in self._records if r.skill_id == skill_id]
        if not records:
            return {"error": "No records for skill"}

        # Group by time periods
        trends: dict[int, list[float]] = {}
        for record in records:
            period = int(record.timestamp / 3600)  # Hourly periods
            trends[period] = trends.get(period, []) + [record.confidence]

        return {
            "periods": list(trends.keys()),
            "avg_confidence": [sum(v) / len(v) for v in trends.values()],
            "min_confidence": [min(v) for v in trends.values()],
            "max_confidence": [max(v) for v in trends.values()],
        }

    def get_recent_decisions(self, skill_id: str | None = None, limit: int = 50) -> list[IntelligenceRecord]:
        """Get recent intelligence decisions."""
        if skill_id:
            return [r for r in self._records if r.skill_id == skill_id][-limit:]
        return self._records[-limit:]
