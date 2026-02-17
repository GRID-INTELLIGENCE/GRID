"""Domain-specific tracking for context evolution.

This module extends grid.awareness.context with domain-specific tracking
capabilities for the Embedded Agentic Knowledge System.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DomainSnapshot:
    """Snapshot of domain state at a point in time."""

    timestamp: datetime
    domain: str
    metrics: dict[str, Any]
    patterns: list[str]
    structural_changes: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "domain": self.domain,
            "metrics": self.metrics,
            "patterns": self.patterns,
            "structural_changes": self.structural_changes,
        }


@dataclass
class DomainEvolution:
    """Tracks evolution of a domain over time."""

    domain: str
    snapshots: list[DomainSnapshot] = field(default_factory=list)
    trend_indicators: dict[str, float] = field(default_factory=dict)
    structural_shifts: list[dict[str, Any]] = field(default_factory=list)

    def add_snapshot(self, snapshot: DomainSnapshot) -> None:
        """Add a new snapshot to the evolution history."""
        self.snapshots.append(snapshot)
        self._update_trends()

    def _update_trends(self) -> None:
        """Update trend indicators based on recent snapshots."""
        if len(self.snapshots) < 2:
            return

        # Calculate trends for numeric metrics
        recent = self.snapshots[-2:]
        for metric_key in recent[0].metrics:
            if isinstance(recent[0].metrics[metric_key], (int, float)):
                if metric_key in recent[1].metrics:
                    change = recent[1].metrics[metric_key] - recent[0].metrics[metric_key]
                    self.trend_indicators[metric_key] = change

    def get_latest_snapshot(self) -> DomainSnapshot | None:
        """Get the most recent snapshot."""
        return self.snapshots[-1] if self.snapshots else None

    def detect_structural_shift(self, threshold: float = 0.3) -> bool:
        """Detect if there's been a significant structural shift."""
        if len(self.snapshots) < 2:
            return False

        latest = self.snapshots[-1]
        previous = self.snapshots[-2]

        # Check for significant changes in patterns
        pattern_change = len(set(latest.patterns) - set(previous.patterns)) / max(len(set(previous.patterns)), 1)

        # Check for significant changes in structural changes
        structural_change = len(latest.structural_changes) > 0

        return pattern_change > threshold or structural_change


class DomainTracker:
    """Tracks domain-specific changes and evolution."""

    def __init__(self) -> None:
        self.domains: dict[str, DomainEvolution] = {}

    def track_domain(
        self,
        domain: str,
        metrics: dict[str, Any],
        patterns: list[str],
        structural_changes: dict[str, Any] | None = None,
    ) -> DomainSnapshot:
        """Track changes in a specific domain.

        Args:
            domain: Domain name (e.g., "technology", "job_market", "healthcare")
            metrics: Domain-specific metrics (e.g., {"adoption_rate": 0.75, "innovation_index": 0.82})
            patterns: List of detected patterns in the domain
            structural_changes: Optional structural changes detected

        Returns:
            DomainSnapshot of the current state
        """
        if domain not in self.domains:
            self.domains[domain] = DomainEvolution(domain=domain)

        snapshot = DomainSnapshot(
            timestamp=datetime.now(),
            domain=domain,
            metrics=metrics,
            patterns=patterns,
            structural_changes=structural_changes or {},
        )

        self.domains[domain].add_snapshot(snapshot)

        logger.info(
            f"Tracked domain '{domain}': {len(patterns)} patterns, {len(structural_changes or {})} structural changes"
        )

        return snapshot

    def get_domain_evolution(self, domain: str) -> DomainEvolution | None:
        """Get evolution history for a domain."""
        return self.domains.get(domain)

    def detect_emerging_structures(self, domain: str) -> list[dict[str, Any]]:
        """Detect emerging structures in a domain.

        Args:
            domain: Domain name

        Returns:
            List of emerging structures detected
        """
        evolution = self.domains.get(domain)
        if not evolution or len(evolution.snapshots) < 2:
            return []

        emerging: list[dict[str, Any]] = []
        latest = evolution.snapshots[-1]

        # Detect new patterns
        if len(evolution.snapshots) >= 2:
            previous_patterns = set(evolution.snapshots[-2].patterns)
            new_patterns = set(latest.patterns) - previous_patterns
            if new_patterns:
                emerging.append(
                    {
                        "type": "new_patterns",
                        "patterns": list(new_patterns),
                        "timestamp": latest.timestamp.isoformat(),
                    }
                )

        # Detect structural shifts
        if evolution.detect_structural_shift():
            emerging.append(
                {
                    "type": "structural_shift",
                    "changes": latest.structural_changes,
                    "timestamp": latest.timestamp.isoformat(),
                }
            )

        return emerging

    def get_all_domains(self) -> list[str]:
        """Get list of all tracked domains."""
        return list(self.domains.keys())


class TechnologyDomainTracker:
    """Specialized tracker for technology domain.

    This is a prototype implementation for Phase 1 of the Embedded Agentic
    Knowledge System, focusing on technology domain tracking.
    """

    def __init__(self) -> None:
        self.base_tracker = DomainTracker()

    def track_technology_metrics(
        self,
        platform_adoption: float,
        infrastructure_capability: float,
        innovation_index: float,
        patterns: list[str],
        structural_changes: dict[str, Any] | None = None,
    ) -> DomainSnapshot:
        """Track technology domain metrics.

        Args:
            platform_adoption: Adoption rate of platforms (0.0-1.0)
            infrastructure_capability: Infrastructure capability index (0.0-1.0)
            innovation_index: Innovation index (0.0-1.0)
            patterns: List of technology patterns detected
            structural_changes: Optional structural changes (e.g., new platforms, shifts)

        Returns:
            DomainSnapshot of technology domain state
        """
        metrics = {
            "platform_adoption": platform_adoption,
            "infrastructure_capability": infrastructure_capability,
            "innovation_index": innovation_index,
        }

        return self.base_tracker.track_domain(
            domain="technology",
            metrics=metrics,
            patterns=patterns,
            structural_changes=structural_changes,
        )

    def get_technology_evolution(self) -> DomainEvolution | None:
        """Get technology domain evolution."""
        return self.base_tracker.get_domain_evolution("technology")

    def detect_technology_shifts(self) -> list[dict[str, Any]]:
        """Detect emerging technology structures."""
        return self.base_tracker.detect_emerging_structures("technology")
