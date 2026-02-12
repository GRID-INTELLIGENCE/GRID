"""
Pattern Dictionary
===================
Recognize patterns - Dictionary pattern.

Reference: Dictionary - Lookup and translate patterns
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Pattern types for recognition."""

    PRICE_SPIKE = "price_spike"
    VOLUME_ANOMALY = "volume_anomaly"
    SENTIMENT_SHIFT = "sentiment_shift"
    TREND_REVERSAL = "trend_reversal"
    MOMENTUM_SURGE = "momentum_surge"


@dataclass
class PatternMatch:
    """Pattern match result."""

    pattern: PatternType
    detected: bool
    confidence: float
    action: str
    metadata: dict[str, Any] | None = None


class PatternDictionary:
    """
    Recognize patterns like a Dictionary.

    Lookup patterns and translate to actions.
    """

    def __init__(self) -> None:
        """Initialize pattern dictionary."""
        self.patterns = {
            PatternType.PRICE_SPIKE: {
                "threshold": 0.10,
                "action": "alert",
                "description": "Price increased by >10%",
            },
            PatternType.VOLUME_ANOMALY: {
                "threshold": 2.0,
                "action": "investigate",
                "description": "Volume >200% of average",
            },
            PatternType.SENTIMENT_SHIFT: {
                "threshold": 0.5,
                "action": "analyze",
                "description": "Sentiment shift >0.5",
            },
            PatternType.TREND_REVERSAL: {
                "threshold": 0.15,
                "action": "review",
                "description": "Trend reversal >15%",
            },
            PatternType.MOMENTUM_SURGE: {
                "threshold": 5.0,
                "action": "monitor",
                "description": "Momentum surge >5.0",
            },
        }

    def recognize(
        self, pattern_type: PatternType, value: float, context: dict[str, Any] | None = None
    ) -> PatternMatch:
        """
        Recognize pattern like a Dictionary lookup.

        Args:
            pattern_type: Type of pattern to recognize
            value: Current value to check
            context: Additional context

        Returns:
            PatternMatch with detection result
        """
        if pattern_type not in self.patterns:
            logger.warning(f"Unknown pattern type: {pattern_type}")
            return PatternMatch(
                pattern=pattern_type, detected=False, confidence=0.0, action="unknown"
            )

        pattern_config = self.patterns[pattern_type]
        threshold: float = pattern_config["threshold"]  # type: ignore
        action: str = pattern_config["action"]  # type: ignore

        # Check if pattern detected
        detected = value >= threshold

        # Calculate confidence
        confidence = min(value / threshold, 1.0) if detected else 0.0

        logger.info(
            f"Pattern check: {pattern_type.value} | "
            f"Value: {value:.2f} | Threshold: {threshold:.2f} | "
            f"Detected: {detected} | Confidence: {confidence:.2f}"
        )

        return PatternMatch(
            pattern=pattern_type,
            detected=detected,
            confidence=confidence,
            action=action,
            metadata={
                "value": value,
                "threshold": threshold,
                "description": pattern_config["description"],
                "context": context or {},
            },
        )

    def get_pattern_description(self, pattern_type: PatternType) -> str:
        """
        Get pattern description.

        Args:
            pattern_type: Pattern type

        Returns:
            Description string
        """
        if pattern_type in self.patterns:
            return str(self.patterns[pattern_type]["description"])
        return "Unknown pattern"

    def list_patterns(self) -> list[dict[str, Any]]:
        """
        List all available patterns.

        Returns:
            List of pattern configurations
        """
        return [
            {
                "type": pattern.value,
                "threshold": config["threshold"],
                "action": config["action"],
                "description": config["description"],
            }
            for pattern, config in self.patterns.items()
        ]


# Example usage
def example_usage() -> None:
    """Example usage of PatternDictionary."""
    dictionary = PatternDictionary()

    # Check price spike
    match1 = dictionary.recognize(PatternType.PRICE_SPIKE, value=0.15)
    print(f"Price Spike: {match1.detected} | Confidence: {match1.confidence:.2f}")

    # Check volume anomaly
    match2 = dictionary.recognize(PatternType.VOLUME_ANOMALY, value=1.5)
    print(f"Volume Anomaly: {match2.detected} | Confidence: {match2.confidence:.2f}")

    # List all patterns
    patterns = dictionary.list_patterns()
    print(f"\nAvailable patterns: {len(patterns)}")
    for p in patterns:
        print(f"  - {p['type']}: {p['description']}")


if __name__ == "__main__":
    example_usage()
