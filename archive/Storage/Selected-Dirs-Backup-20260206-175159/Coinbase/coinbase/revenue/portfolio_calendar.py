"""
Portfolio Calendar
==================
Track portfolio events - Calendar pattern.

Reference: Calendar - Schedule events with purpose
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Portfolio event types."""

    BUY = "buy"
    SELL = "sell"
    REBALANCE = "rebalance"
    DIVIDEND = "dividend"
    STAKING_REWARD = "staking_reward"


@dataclass
class PortfolioEvent:
    """Portfolio event entry."""

    event_type: EventType
    asset_symbol: str
    timestamp: datetime
    quantity: float
    price: float
    purpose: str
    metadata: dict[str, Any] | None = None


class PortfolioCalendar:
    """
    Track portfolio events like a Calendar.

    Schedules events with purpose and direction.
    """

    def __init__(self) -> None:
        """Initialize portfolio calendar."""
        self.events: list[PortfolioEvent] = []
        self.max_events = 1000

    def schedule_event(
        self,
        event_type: EventType,
        asset_symbol: str,
        quantity: float,
        price: float,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PortfolioEvent:
        """
        Schedule portfolio event like a Calendar.

        Args:
            event_type: Type of event
            asset_symbol: Asset symbol
            quantity: Quantity of asset
            price: Price per unit
            timestamp: Event timestamp
            metadata: Additional metadata

        Returns:
            PortfolioEvent
        """
        event = PortfolioEvent(
            event_type=event_type,
            asset_symbol=asset_symbol,
            timestamp=timestamp or datetime.now(),
            quantity=quantity,
            price=price,
            purpose=self._get_purpose(event_type),
            metadata=metadata or {},
        )

        self.events.append(event)

        if len(self.events) > self.max_events:
            self.events.pop(0)

        logger.info(
            f"Event scheduled: {event_type.value.upper()} | "
            f"{asset_symbol} | {quantity} @ ${price:,.2f}"
        )

        return event

    def _get_purpose(self, event_type: EventType) -> str:
        """
        Get purpose like a Dictionary translation.

        Args:
            event_type: Event type

        Returns:
            Purpose description
        """
        purposes = {
            EventType.BUY: "Acquire position",
            EventType.SELL: "Realize gains",
            EventType.REBALANCE: "Optimize allocation",
            EventType.DIVIDEND: "Passive income",
            EventType.STAKING_REWARD: "Staking yield",
        }
        return purposes.get(event_type, "Track activity")

    def get_events_by_asset(self, asset_symbol: str, limit: int = 50) -> list[PortfolioEvent]:
        """
        Get events for specific asset.

        Args:
            asset_symbol: Asset symbol
            limit: Max events to return

        Returns:
            List of events
        """
        asset_events = [e for e in self.events if e.asset_symbol == asset_symbol]
        return asset_events[-limit:]

    def get_events_by_type(self, event_type: EventType, limit: int = 50) -> list[PortfolioEvent]:
        """
        Get events by type.

        Args:
            event_type: Event type
            limit: Max events to return

        Returns:
            List of events
        """
        type_events = [e for e in self.events if e.event_type == event_type]
        return type_events[-limit:]

    def get_recent_events(self, limit: int = 10) -> list[PortfolioEvent]:
        """
        Get recent events.

        Args:
            limit: Max events to return

        Returns:
            List of recent events
        """
        return self.events[-limit:]

    def calculate_position(self, asset_symbol: str) -> dict[str, Any]:
        """
        Calculate current position for asset.

        Args:
            asset_symbol: Asset symbol

        Returns:
            Position details
        """
        events = self.get_events_by_asset(asset_symbol)

        total_quantity = 0.0
        total_cost = 0.0
        total_value = 0.0

        for event in events:
            if event.event_type == EventType.BUY:
                total_quantity += event.quantity
                total_cost += event.quantity * event.price
            elif event.event_type == EventType.SELL:
                total_quantity -= event.quantity
                total_value += event.quantity * event.price

        average_cost = total_cost / total_quantity if total_quantity > 0 else 0.0
        current_price = events[-1].price if events else 0.0
        current_value = total_quantity * current_price
        unrealized_pnl = current_value - (total_quantity * average_cost)

        return {
            "asset_symbol": asset_symbol,
            "quantity": total_quantity,
            "average_cost": average_cost,
            "current_price": current_price,
            "current_value": current_value,
            "unrealized_pnl": unrealized_pnl,
            "pnl_percentage": (
                (unrealized_pnl / (total_quantity * average_cost) * 100)
                if (total_quantity * average_cost) > 0
                else 0.0
            ),
        }


# Example usage
def example_usage() -> None:
    """Example usage of PortfolioCalendar."""
    calendar = PortfolioCalendar()

    # Schedule buy event
    calendar.schedule_event(
        event_type=EventType.BUY, asset_symbol="BTC", quantity=0.5, price=50000.0
    )

    # Schedule another buy
    calendar.schedule_event(
        event_type=EventType.BUY, asset_symbol="BTC", quantity=0.3, price=51000.0
    )

    # Calculate position
    position = calendar.calculate_position("BTC")
    print(f"BTC Position: {position['quantity']} BTC")
    print(f"Average Cost: ${position['average_cost']:,.2f}")
    print(f"Current Value: ${position['current_value']:,.2f}")
    print(f"Unrealized PnL: ${position['unrealized_pnl']:,.2f}")
    print(f"PnL %: {position['pnl_percentage']:.2f}%")


if __name__ == "__main__":
    example_usage()
