"""Confidence source types for the cognitive layer."""

from enum import StrEnum


class ConfidenceSource(StrEnum):
    MEASURED = "measured"
    CALIBRATED = "calibrated"
    DEFAULT = "default"
    ASSUMED = "assumed"
    PROPAGATED = "propagated"
