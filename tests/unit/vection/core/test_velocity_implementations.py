"""Tests for the three VelocityTracker implementations that replaced stubs.

Covers _calculate_drift(), _calculate_momentum(), and _calculate_confidence()
in isolation, plus invariants that must hold between them.
"""

from __future__ import annotations

import pytest

from vection.core.velocity_tracker import VelocityTracker


def _tracker_with_directions(directions: list[str]) -> VelocityTracker:
    """Build a tracker whose direction_sequence matches the given list."""
    tracker = VelocityTracker(session_id="test", history_size=100, direction_history_size=100)
    for d in directions:
        tracker.direction_sequence.append(d)
        # Also append a fake history snapshot so confidence counts events
        tracker.history.append(object())  # type: ignore[arg-type]
    return tracker


# ---------------------------------------------------------------------------
# _calculate_drift
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDriftCalculation:
    def test_empty_sequence_returns_zero(self) -> None:
        tracker = VelocityTracker(session_id="t")
        assert tracker._calculate_drift() == 0.0

    def test_single_entry_returns_zero(self) -> None:
        tracker = _tracker_with_directions(["A"])
        assert tracker._calculate_drift() == 0.0

    def test_stable_sequence_returns_zero(self) -> None:
        tracker = _tracker_with_directions(["A"] * 10)
        assert tracker._calculate_drift() == 0.0

    def test_fully_alternating_returns_one(self) -> None:
        tracker = _tracker_with_directions(["A", "B"] * 5)
        assert tracker._calculate_drift() == pytest.approx(1.0)

    def test_half_alternating(self) -> None:
        # [A, A, B, B, A, A] → 2 changes out of 5 pairs → 0.4
        tracker = _tracker_with_directions(["A", "A", "B", "B", "A", "A"])
        assert tracker._calculate_drift() == pytest.approx(2 / 5)

    def test_drift_bounded_zero_to_one(self) -> None:
        for seq in [["X"] * 20, ["X", "Y"] * 10, ["X", "Y", "Z"] * 7]:
            tracker = _tracker_with_directions(seq)
            d = tracker._calculate_drift()
            assert 0.0 <= d <= 1.0


# ---------------------------------------------------------------------------
# _calculate_momentum
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMomentumCalculation:
    def test_empty_sequence_returns_half(self) -> None:
        tracker = VelocityTracker(session_id="t")
        assert tracker._calculate_momentum() == 0.5

    def test_single_entry_returns_half(self) -> None:
        tracker = _tracker_with_directions(["A"])
        assert tracker._calculate_momentum() == 0.5

    def test_stable_sequence_returns_one(self) -> None:
        tracker = _tracker_with_directions(["A"] * 10)
        assert tracker._calculate_momentum() == pytest.approx(1.0)

    def test_fully_alternating_returns_zero(self) -> None:
        tracker = _tracker_with_directions(["A", "B"] * 5)
        assert tracker._calculate_momentum() == pytest.approx(0.0)

    def test_momentum_bounded_zero_to_one(self) -> None:
        for seq in [["X"] * 20, ["X", "Y"] * 10, ["X", "Y", "Z"] * 7]:
            tracker = _tracker_with_directions(seq)
            m = tracker._calculate_momentum()
            assert 0.0 <= m <= 1.0


# ---------------------------------------------------------------------------
# _calculate_confidence
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfidenceCalculation:
    def test_zero_history_returns_zero(self) -> None:
        tracker = VelocityTracker(session_id="t")
        assert tracker._calculate_confidence() == pytest.approx(0.0)

    def test_ten_events_returns_half(self) -> None:
        tracker = _tracker_with_directions([])
        for _ in range(10):
            tracker.history.append(object())  # type: ignore[arg-type]
        assert tracker._calculate_confidence() == pytest.approx(0.5)

    def test_twenty_events_returns_one(self) -> None:
        tracker = _tracker_with_directions([])
        for _ in range(20):
            tracker.history.append(object())  # type: ignore[arg-type]
        assert tracker._calculate_confidence() == pytest.approx(1.0)

    def test_saturates_at_one(self) -> None:
        tracker = _tracker_with_directions([])
        for _ in range(100):
            tracker.history.append(object())  # type: ignore[arg-type]
        assert tracker._calculate_confidence() == pytest.approx(1.0)

    def test_confidence_grows_monotonically(self) -> None:
        tracker = VelocityTracker(session_id="t")
        previous = -1.0
        for _ in range(25):
            tracker.history.append(object())  # type: ignore[arg-type]
            c = tracker._calculate_confidence()
            assert c >= previous
            previous = c


# ---------------------------------------------------------------------------
# Complementarity invariant
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMomentumDriftComplementarity:
    """For any deterministic sequence, momentum + drift must equal exactly 1.0.

    Rationale: a consecutive pair is either the same direction (counts toward
    momentum) or different (counts toward drift).  Both denominators are
    identical (len(seq) - 1), so the two rates always sum to 1.
    """

    @pytest.mark.parametrize(
        "seq",
        [
            ["A"] * 10,
            ["A", "B"] * 5,
            ["A", "B", "C", "A", "B"] * 2,
            ["X", "X", "Y", "X", "Z", "X"] * 3,
        ],
    )
    def test_momentum_plus_drift_equals_one(self, seq: list[str]) -> None:
        tracker = _tracker_with_directions(seq)
        total = tracker._calculate_momentum() + tracker._calculate_drift()
        assert total == pytest.approx(1.0)
