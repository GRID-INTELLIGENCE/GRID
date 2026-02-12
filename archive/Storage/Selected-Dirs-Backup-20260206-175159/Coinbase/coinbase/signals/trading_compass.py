"""
Trading Compass
===============
Generate trading signals - Compass pattern.

Reference: Compass - Points to trading direction
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TradingDirection(Enum):
    """Trading directions."""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class TradingSignal:
    """Trading signal result."""

    direction: TradingDirection
    confidence: float
    reasoning: str
    target_price: float | None = None
    stop_loss: float | None = None
    metadata: dict[str, Any] | None = None


class TradingCompass:
    """
    Generate trading signals like a Compass.

    Points to trading direction based on sentiment and momentum.
    """

    def __init__(self) -> None:
        """Initialize trading compass."""
        self.directions = {
            TradingDirection.STRONG_BUY: 0.8,
            TradingDirection.BUY: 0.6,
            TradingDirection.HOLD: 0.5,
            TradingDirection.SELL: 0.4,
            TradingDirection.STRONG_SELL: 0.2,
        }

    def point_direction(
        self, sentiment: float, momentum: float, current_price: float = 0.0
    ) -> TradingSignal:
        """
        Point trading direction like a Compass.

        Args:
            sentiment: Sentiment score (-1.0 to 1.0)
            momentum: Momentum value
            current_price: Current price

        Returns:
            TradingSignal with direction and confidence
        """
        # Normalize sentiment to 0-1
        score = (sentiment + 1) / 2

        # Normalize momentum factor
        momentum_factor = min(momentum / 10.0, 1.0)

        # Determine direction
        if score > 0.8 and momentum_factor > 0.5:
            direction = TradingDirection.STRONG_BUY
        elif score > 0.6 and momentum_factor > 0.3:
            direction = TradingDirection.BUY
        elif score < 0.2 and momentum_factor < 0.3:
            direction = TradingDirection.STRONG_SELL
        elif score < 0.4 and momentum_factor < 0.5:
            direction = TradingDirection.SELL
        else:
            direction = TradingDirection.HOLD

        # Calculate confidence
        confidence = self.directions[direction]

        # Generate reasoning
        reasoning = self._generate_reasoning(sentiment, momentum, direction)

        # Calculate targets
        target_price = None
        stop_loss = None

        if direction in [TradingDirection.BUY, TradingDirection.STRONG_BUY] and current_price > 0:
            target_price = current_price * 1.05
            stop_loss = current_price * 0.95
        elif (
            direction in [TradingDirection.SELL, TradingDirection.STRONG_SELL] and current_price > 0
        ):
            target_price = current_price * 0.95
            stop_loss = current_price * 1.05

        logger.info(
            f"Trading signal: {direction.value} | "
            f"Confidence: {confidence:.2f} | "
            f"Sentiment: {sentiment:.2f} | "
            f"Momentum: {momentum:.2f}"
        )

        return TradingSignal(
            direction=direction,
            confidence=confidence,
            reasoning=reasoning,
            target_price=target_price,
            stop_loss=stop_loss,
            metadata={
                "sentiment": sentiment,
                "momentum": momentum,
                "score": score,
                "momentum_factor": momentum_factor,
            },
        )

    def _generate_reasoning(
        self, sentiment: float, momentum: float, direction: TradingDirection
    ) -> str:
        """
        Generate reasoning for signal.

        Args:
            sentiment: Sentiment score
            momentum: Momentum value
            direction: Trading direction

        Returns:
            Reasoning string
        """
        parts = []

        if sentiment > 0.5:
            parts.append(f"Strong positive sentiment ({sentiment:.2f})")
        elif sentiment > 0.3:
            parts.append(f"Positive sentiment ({sentiment:.2f})")
        elif sentiment < -0.5:
            parts.append(f"Strong negative sentiment ({sentiment:.2f})")
        elif sentiment < -0.3:
            parts.append(f"Negative sentiment ({sentiment:.2f})")

        if momentum > 5.0:
            parts.append(f"High momentum ({momentum:.2f})")
        elif momentum > 2.0:
            parts.append(f"Moderate momentum ({momentum:.2f})")
        elif momentum < -2.0:
            parts.append(f"Negative momentum ({momentum:.2f})")

        return " and ".join(parts)


# Example usage
def example_usage() -> None:
    """Example usage of TradingCompass."""
    compass = TradingCompass()

    # Strong buy signal
    signal1 = compass.point_direction(sentiment=0.75, momentum=5.0, current_price=50000.0)
    print(f"Signal 1: {signal1.direction.value}")
    print(f"Confidence: {signal1.confidence:.2f}")
    print(f"Reasoning: {signal1.reasoning}")
    print(f"Target: ${signal1.target_price:,.2f}" if signal1.target_price else "")
    print(f"Stop Loss: ${signal1.stop_loss:,.2f}" if signal1.stop_loss else "")


if __name__ == "__main__":
    example_usage()
