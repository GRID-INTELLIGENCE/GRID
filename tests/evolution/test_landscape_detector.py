"""Tests for landscape detector functionality."""

from __future__ import annotations

from datetime import datetime

import pytest

from grid.awareness.context import Context
from grid.essence.core_state import EssentialState
from grid.evolution.landscape_detector import (
    LandscapeDetector,
    LandscapeSnapshot,
    NeuralLandscapeAnalyzer,
    StatisticalLandscapeAnalyzer,
    SyntacticLandscapeAnalyzer,
)


class TestLandscapeDetector:
    """Test LandscapeDetector."""

    @pytest.fixture
    def detector(self):
        """Create landscape detector."""
        return LandscapeDetector()

    @pytest.fixture
    def base_state(self):
        """Create base essential state."""
        return EssentialState(
            pattern_signature="test_sig",
            quantum_state={"test": "data", "metric": 0.5},
            context_depth=1.0,
            coherence_factor=0.5,
        )

    @pytest.fixture
    def base_context(self):
        """Create base context."""
        return Context(
            temporal_depth=1.0,
            spatial_field={},
            relational_web={},
            quantum_signature="test_ctx",
        )

    @pytest.mark.asyncio
    async def test_detect_landscape_shifts(self, detector, base_state, base_context):
        """Test detecting landscape shifts."""
        shifts = await detector.detect_landscape_shifts(base_state, base_context)

        assert isinstance(shifts, list)
        # May or may not detect shifts on first call (depends on history)

    @pytest.mark.asyncio
    async def test_multiple_detections(self, detector, base_state, base_context):
        """Test multiple detection calls to build history."""
        # First detection
        await detector.detect_landscape_shifts(base_state, base_context)

        # Second detection with changed state
        state2 = EssentialState(
            pattern_signature="test_sig2",
            quantum_state={"test": "data2", "metric": 0.8},
            context_depth=1.5,
            coherence_factor=0.8,
        )
        shifts2 = await detector.detect_landscape_shifts(state2, base_context)

        assert isinstance(shifts2, list)

    @pytest.mark.asyncio
    async def test_learn_landscape_pattern(self, detector, base_state, base_context):
        """Test learning landscape patterns."""
        await detector.learn_landscape_pattern("test_pattern", base_state, base_context)

        # Should have learned pattern
        assert "test_pattern" in detector.neural.learned_landscapes

    def test_get_recent_shifts(self, detector):
        """Test getting recent shifts."""
        recent = detector.get_recent_shifts(limit=5)
        assert isinstance(recent, list)


class TestStatisticalLandscapeAnalyzer:
    """Test StatisticalLandscapeAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create statistical landscape analyzer."""
        return StatisticalLandscapeAnalyzer(window_size=5)

    def test_add_snapshot(self, analyzer):
        """Test adding snapshots."""
        snapshot = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=["pattern1", "pattern2"],
            structural_features={},
            domain_metrics={"domain1": 0.5},
        )

        analyzer.add_snapshot(snapshot)
        assert len(analyzer.snapshots) == 1

    def test_detect_statistical_shifts(self, analyzer):
        """Test detecting statistical shifts."""
        # Add initial snapshots
        for _i in range(5):
            snapshot = LandscapeSnapshot(
                timestamp=datetime.now(),
                patterns=["pattern1"],
                structural_features={},
                domain_metrics={"domain1": 0.5},
            )
            analyzer.add_snapshot(snapshot)

        # Add changed snapshots
        for _i in range(5):
            snapshot = LandscapeSnapshot(
                timestamp=datetime.now(),
                patterns=["pattern2", "pattern3"],  # Different patterns
                structural_features={},
                domain_metrics={"domain1": 0.8},  # Changed metric
            )
            analyzer.add_snapshot(snapshot)

        shifts = analyzer.detect_statistical_shifts(threshold=0.2)

        assert len(shifts) > 0
        assert any(shift.shift_type in ["pattern_distribution", "metric_change"] for shift in shifts)


class TestSyntacticLandscapeAnalyzer:
    """Test SyntacticLandscapeAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create syntactic landscape analyzer."""
        return SyntacticLandscapeAnalyzer()

    def test_analyze_structure(self, analyzer):
        """Test structure analysis."""
        snapshot = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=["pattern1", "pattern2"],
            structural_features={"depth": 3, "breadth": 5},
            domain_metrics={},
        )

        structure = analyzer.analyze_structure(snapshot)

        assert "pattern_count" in structure
        assert "complexity" in structure
        assert structure["pattern_count"] == 2

    def test_detect_structural_shifts(self, analyzer):
        """Test detecting structural shifts."""
        # First snapshot
        snapshot1 = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=["pattern1"],
            structural_features={"depth": 2},
            domain_metrics={},
        )
        analyzer.analyze_structure(snapshot1)

        # Second snapshot with changes
        snapshot2 = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=["pattern1", "pattern2", "pattern3"],  # More patterns
            structural_features={"depth": 5},  # Deeper structure
            domain_metrics={},
        )
        analyzer.analyze_structure(snapshot2)

        shifts = analyzer.detect_structural_shifts(threshold=0.2)

        assert len(shifts) > 0


class TestNeuralLandscapeAnalyzer:
    """Test NeuralLandscapeAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create neural landscape analyzer."""
        return NeuralLandscapeAnalyzer()

    def test_learn_landscape(self, analyzer):
        """Test learning landscape patterns."""
        snapshot = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=["pattern1"],
            structural_features={"depth": 2},
            domain_metrics={"metric1": 0.5},
        )

        analyzer.learn_landscape(snapshot, "test_label")

        assert "test_label" in analyzer.learned_landscapes

    def test_detect_neural_shifts(self, analyzer):
        """Test detecting neural shifts."""
        # Learn a pattern
        snapshot1 = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=["pattern1"],
            structural_features={"depth": 2},
            domain_metrics={"metric1": 0.5},
        )
        analyzer.learn_landscape(snapshot1, "baseline")

        # Different snapshot
        snapshot2 = LandscapeSnapshot(
            timestamp=datetime.now(),
            patterns=["pattern2", "pattern3"],
            structural_features={"depth": 5},
            domain_metrics={"metric1": 0.9},
        )

        shifts = analyzer.detect_neural_shifts(snapshot2, threshold=0.3)

        assert len(shifts) > 0
        assert any(shift.shift_type == "neural_pattern_divergence" for shift in shifts)
