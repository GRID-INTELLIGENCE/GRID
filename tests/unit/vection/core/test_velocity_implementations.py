"""Tests for the three VelocityTracker implementations that replaced stubs.

Covers _calculate_drift(), _calculate_momentum(), and _calculate_confidence()
in isolation, plus invariants that must hold between them.
"""

from __future__ import annotations

import pytest

from vection.core.velocity_tracker import VelocityTracker
from vection.schemas.velocity_vector import DirectionCategory, categorize_direction


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


# ---------------------------------------------------------------------------
# Canonical direction categorization
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCategorizeDirection:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            # HTTP read/probe methods → EXPLORATION
            ("GET", DirectionCategory.EXPLORATION),
            ("HEAD", DirectionCategory.EXPLORATION),
            ("OPTIONS", DirectionCategory.EXPLORATION),
            # HTTP write methods → EXECUTION
            ("POST", DirectionCategory.EXECUTION),
            ("PUT", DirectionCategory.EXECUTION),
            ("PATCH", DirectionCategory.EXECUTION),
            ("DELETE", DirectionCategory.EXECUTION),
            # Semantic verbs
            ("analyze the failure", DirectionCategory.INVESTIGATION),
            ("debug", DirectionCategory.INVESTIGATION),
            ("explore options", DirectionCategory.EXPLORATION),
            ("build the project", DirectionCategory.EXECUTION),
            ("merge the branches", DirectionCategory.SYNTHESIS),
            ("review the diff", DirectionCategory.REFLECTION),
            ("switch context", DirectionCategory.TRANSITION),
        ],
    )
    def test_known_inputs(self, text: str, expected: DirectionCategory) -> None:
        assert categorize_direction(text) == expected

    def test_unknown_returns_unknown(self) -> None:
        assert categorize_direction("zxqwv") == DirectionCategory.UNKNOWN

    def test_empty_returns_unknown(self) -> None:
        assert categorize_direction("") == DirectionCategory.UNKNOWN

    def test_case_insensitive(self) -> None:
        assert categorize_direction("AnAlYzE") == DirectionCategory.INVESTIGATION

    def test_token_match_not_substring(self) -> None:
        # "budget" contains the substring "get" but is not the token "get"
        assert categorize_direction("budget") == DirectionCategory.UNKNOWN
        # "remove" contains "move" but token matching protects against it
        assert categorize_direction("remove") == DirectionCategory.UNKNOWN

    def test_most_specific_wins(self) -> None:
        # "analyze" (INVESTIGATION) precedes "get" (EXPLORATION) in priority order
        assert categorize_direction("get and analyze") == DirectionCategory.INVESTIGATION

    def test_http_method_with_path(self) -> None:
        # Mirrors the admission gate's "{method} {path}" style direction strings
        assert categorize_direction("DELETE /api/v1/users/42") == DirectionCategory.EXECUTION


@pytest.mark.unit
class TestTrackerUsesCanonicalCategorization:
    """The tracker's HTTP-style events should now produce meaningful categories
    instead of UNKNOWN (the regression that motivated this enrichment)."""

    def test_http_get_events_categorized(self) -> None:
        tracker = VelocityTracker(session_id="t")
        velocity = tracker.track_event({"action": "GET", "query": "/api/health"})
        assert velocity.direction == DirectionCategory.EXPLORATION

    def test_http_post_events_categorized(self) -> None:
        tracker = VelocityTracker(session_id="t")
        velocity = tracker.track_event({"action": "POST", "query": "/api/orders"})
        assert velocity.direction == DirectionCategory.EXECUTION
