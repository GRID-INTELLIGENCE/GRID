"""Tests for domain tracking functionality."""

from __future__ import annotations

from datetime import datetime

import pytest

from grid.awareness.context import Context
from grid.awareness.domain_tracking import (
    DomainEvolution,
    DomainSnapshot,
    DomainTracker,
    TechnologyDomainTracker,
)
from grid.essence.core_state import EssentialState


class TestDomainSnapshot:
    """Test DomainSnapshot."""

    def test_snapshot_creation(self):
        """Test creating a domain snapshot."""
        snapshot = DomainSnapshot(
            timestamp=datetime.now(),
            domain="technology",
            metrics={"adoption_rate": 0.75, "innovation_index": 0.82},
            patterns=["transformer_architecture", "distributed_systems"],
            structural_changes={"new_platform": "databricks"},
        )

        assert snapshot.domain == "technology"
        assert snapshot.metrics["adoption_rate"] == 0.75
        assert len(snapshot.patterns) == 2
        assert "new_platform" in snapshot.structural_changes

    def test_snapshot_to_dict(self):
        """Test snapshot serialization."""
        snapshot = DomainSnapshot(
            timestamp=datetime.now(),
            domain="technology",
            metrics={"adoption_rate": 0.75},
            patterns=["pattern1"],
            structural_changes={},
        )

        data = snapshot.to_dict()
        assert data["domain"] == "technology"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)


class TestDomainEvolution:
    """Test DomainEvolution."""

    def test_evolution_creation(self):
        """Test creating domain evolution."""
        evolution = DomainEvolution(domain="technology")
        assert evolution.domain == "technology"
        assert len(evolution.snapshots) == 0

    def test_add_snapshot(self):
        """Test adding snapshots to evolution."""
        evolution = DomainEvolution(domain="technology")

        snapshot1 = DomainSnapshot(
            timestamp=datetime.now(),
            domain="technology",
            metrics={"adoption_rate": 0.5},
            patterns=["pattern1"],
            structural_changes={},
        )

        snapshot2 = DomainSnapshot(
            timestamp=datetime.now(),
            domain="technology",
            metrics={"adoption_rate": 0.75},
            patterns=["pattern1", "pattern2"],
            structural_changes={},
        )

        evolution.add_snapshot(snapshot1)
        evolution.add_snapshot(snapshot2)

        assert len(evolution.snapshots) == 2
        assert "adoption_rate" in evolution.trend_indicators
        assert evolution.trend_indicators["adoption_rate"] == 0.25

    def test_detect_structural_shift(self):
        """Test structural shift detection."""
        evolution = DomainEvolution(domain="technology")

        snapshot1 = DomainSnapshot(
            timestamp=datetime.now(),
            domain="technology",
            metrics={},
            patterns=["pattern1"],
            structural_changes={},
        )

        snapshot2 = DomainSnapshot(
            timestamp=datetime.now(),
            domain="technology",
            metrics={},
            patterns=["pattern1", "pattern2", "pattern3"],
            structural_changes={"shift": "major"},
        )

        evolution.add_snapshot(snapshot1)
        evolution.add_snapshot(snapshot2)

        # Should detect shift due to new patterns and structural changes
        assert evolution.detect_structural_shift(threshold=0.3)


class TestDomainTracker:
    """Test DomainTracker."""

    def test_track_domain(self):
        """Test tracking domain changes."""
        tracker = DomainTracker()

        snapshot = tracker.track_domain(
            domain="technology",
            metrics={"adoption_rate": 0.75},
            patterns=["transformer", "distributed"],
            structural_changes={"platform": "databricks"},
        )

        assert snapshot.domain == "technology"
        assert "technology" in tracker.domains
        assert len(tracker.domains["technology"].snapshots) == 1

    def test_get_domain_evolution(self):
        """Test retrieving domain evolution."""
        tracker = DomainTracker()
        tracker.track_domain(
            domain="technology",
            metrics={"adoption_rate": 0.75},
            patterns=["pattern1"],
            structural_changes={},
        )

        evolution = tracker.get_domain_evolution("technology")
        assert evolution is not None
        assert evolution.domain == "technology"

    def test_detect_emerging_structures(self):
        """Test detecting emerging structures."""
        tracker = DomainTracker()

        # First snapshot
        tracker.track_domain(
            domain="technology",
            metrics={},
            patterns=["pattern1"],
            structural_changes={},
        )

        # Second snapshot with new patterns
        tracker.track_domain(
            domain="technology",
            metrics={},
            patterns=["pattern1", "pattern2", "pattern3"],
            structural_changes={"shift": "major"},
        )

        emerging = tracker.detect_emerging_structures("technology")
        assert len(emerging) > 0
        assert any(e["type"] == "new_patterns" for e in emerging)


class TestTechnologyDomainTracker:
    """Test TechnologyDomainTracker."""

    def test_track_technology_metrics(self):
        """Test tracking technology domain metrics."""
        tracker = TechnologyDomainTracker()

        snapshot = tracker.track_technology_metrics(
            platform_adoption=0.75,
            infrastructure_capability=0.82,
            innovation_index=0.68,
            patterns=["transformer", "distributed"],
            structural_changes={"platform": "databricks"},
        )

        assert snapshot.domain == "technology"
        assert snapshot.metrics["platform_adoption"] == 0.75
        assert snapshot.metrics["infrastructure_capability"] == 0.82

    def test_get_technology_evolution(self):
        """Test retrieving technology evolution."""
        tracker = TechnologyDomainTracker()
        tracker.track_technology_metrics(
            platform_adoption=0.75,
            infrastructure_capability=0.82,
            innovation_index=0.68,
            patterns=["pattern1"],
            structural_changes={},
        )

        evolution = tracker.get_technology_evolution()
        assert evolution is not None
        assert evolution.domain == "technology"

    def test_detect_technology_shifts(self):
        """Test detecting technology shifts."""
        tracker = TechnologyDomainTracker()

        tracker.track_technology_metrics(
            platform_adoption=0.5,
            infrastructure_capability=0.6,
            innovation_index=0.5,
            patterns=["pattern1"],
            structural_changes={},
        )

        tracker.track_technology_metrics(
            platform_adoption=0.8,
            infrastructure_capability=0.9,
            innovation_index=0.85,
            patterns=["pattern1", "pattern2", "pattern3"],
            structural_changes={"shift": "major"},
        )

        shifts = tracker.detect_technology_shifts()
        assert len(shifts) > 0


class TestContextDomainTracking:
    """Test Context integration with domain tracking."""

    @pytest.mark.asyncio
    async def test_context_with_domain_tracking(self):
        """Test Context with domain tracking enabled."""
        context = Context(
            temporal_depth=1.0,
            spatial_field={},
            relational_web={},
            quantum_signature="test",
        )

        # Enable domain tracking
        context = context.enable_domain_tracking("technology", "technology")

        assert context.active_domain == "technology"
        assert context.domain_tracker is not None

        # Create state with domain metrics
        state = EssentialState(
            pattern_signature="test_sig",
            quantum_state={
                "patterns": ["transformer", "distributed"],
                "domain_metrics": {
                    "platform_adoption": 0.75,
                    "infrastructure_capability": 0.82,
                },
            },
            context_depth=1.0,
            coherence_factor=0.5,
        )

        # Evolve context
        evolved = await context.evolve(state)

        # Check domain evolution
        evolution = evolved.get_domain_evolution()
        assert evolution is not None
        assert len(evolution.snapshots) > 0

    @pytest.mark.asyncio
    async def test_detect_emerging_structures(self):
        """Test detecting emerging structures in context."""
        context = Context(
            temporal_depth=1.0,
            spatial_field={},
            relational_web={},
            quantum_signature="test",
        ).enable_domain_tracking("technology", "technology")

        # First evolution with initial metrics
        state1 = EssentialState(
            pattern_signature="sig1",
            quantum_state={
                "patterns": ["pattern1"],
                "domain_metrics": {
                    "platform_adoption": 0.5,
                    "infrastructure_capability": 0.6,
                    "innovation_index": 0.5,
                },
            },
            context_depth=1.0,
            coherence_factor=0.5,
        )
        context = await context.evolve(state1)

        # Second evolution with new patterns and structural changes
        state2 = EssentialState(
            pattern_signature="sig2",
            quantum_state={
                "patterns": ["pattern1", "pattern2", "pattern3"],
                "domain_metrics": {
                    "platform_adoption": 0.8,
                    "infrastructure_capability": 0.9,
                    "innovation_index": 0.85,
                },
                "structural_changes": {"shift": "major"},
            },
            context_depth=1.1,
            coherence_factor=0.6,
        )
        context = await context.evolve(state2)

        # Detect emerging structures
        emerging = context.detect_emerging_structures()
        assert len(emerging) > 0
