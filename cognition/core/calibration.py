"""Calibration provider interface for confidence-emitting components."""

from __future__ import annotations

from abc import ABC, abstractmethod


class CalibrationProvider(ABC):
    """Any component that emits confidence values should implement this."""

    @abstractmethod
    def record_outcome(self, predicted: float, actual: bool) -> None:
        """Record a predicted confidence and whether the outcome was correct."""
        ...

    @abstractmethod
    def calibration_score(self) -> float | None:
        """Return Brier score, or None if insufficient data (< 5 outcomes)."""
        ...

    @abstractmethod
    def confidence_source(self) -> str:
        """Return the source label for this component's confidence values."""
        ...
