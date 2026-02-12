"""
Notification Watch
==================
Custom notification system - Watch pattern.

Reference: Watch - Set alarms and notify on triggers
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AlarmType(Enum):
    """Alarm types."""

    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    VOLUME_HIGH = "volume_high"
    SENTIMENT_HIGH = "sentiment_high"
    CUSTOM = "custom"


@dataclass
class Alarm:
    """Alarm configuration."""

    alarm_id: str
    condition: str
    threshold: float
    action: str
    triggered: bool = False
    created_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class NotificationWatch:
    """
    Custom notification system like a Watch.

    Set alarms and notify when conditions met.
    """

    def __init__(self) -> None:
        """Initialize notification watch."""
        self.alarms: list[Alarm] = []
        self.notification_handlers: dict[str, Callable] = {}
        self.max_alarms = 100

    def set_alarm(
        self, condition: str, threshold: float, action: str, metadata: dict[str, Any] | None = None
    ) -> Alarm:
        """
        Set alarm like a Watch.

        Args:
            condition: Condition to check (e.g., "price_above")
            threshold: Threshold value
            action: Action to take when triggered
            metadata: Additional metadata

        Returns:
            Alarm configuration
        """
        import uuid

        alarm = Alarm(
            alarm_id=str(uuid.uuid4()),
            condition=condition,
            threshold=threshold,
            action=action,
            triggered=False,
            created_at=datetime.now(),
            metadata=metadata or {},
        )

        self.alarms.append(alarm)

        if len(self.alarms) > self.max_alarms:
            self.alarms.pop(0)

        logger.info(f"Alarm set: {condition} | " f"Threshold: {threshold} | " f"Action: {action}")

        return alarm

    def check_alarms(
        self, current_value: float, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Check alarms like a Watch beeping.

        Args:
            current_value: Current value to check
            context: Additional context

        Returns:
            List of triggered alarm actions
        """
        triggered_actions = []

        for alarm in self.alarms:
            if alarm.triggered:
                continue

            # Check if alarm should trigger
            should_trigger = self._should_trigger(alarm, current_value)

            if should_trigger:
                alarm.triggered = True

                action_result = {
                    "alarm_id": alarm.alarm_id,
                    "condition": alarm.condition,
                    "action": alarm.action,
                    "threshold": alarm.threshold,
                    "current_value": current_value,
                    "timestamp": datetime.now().isoformat(),
                    "context": context or {},
                }

                # Execute action handler if registered
                if alarm.action in self.notification_handlers:
                    try:
                        handler_result = self.notification_handlers[alarm.action](action_result)
                        action_result["handler_result"] = handler_result
                    except Exception as e:
                        logger.error(f"Handler error: {e}")

                triggered_actions.append(action_result)

                logger.info(
                    f"Alarm triggered: {alarm.condition} | "
                    f"Action: {alarm.action} | "
                    f"Value: {current_value}"
                )

        return triggered_actions

    def _should_trigger(self, alarm: Alarm, current_value: float) -> bool:
        """
        Check if alarm should trigger.

        Args:
            alarm: Alarm configuration
            current_value: Current value

        Returns:
            True if should trigger
        """
        condition = alarm.condition.lower()

        if "above" in condition:
            return current_value >= alarm.threshold
        elif "below" in condition:
            return current_value <= alarm.threshold
        elif "high" in condition:
            return current_value >= alarm.threshold
        elif "low" in condition:
            return current_value <= alarm.threshold
        else:
            # Default: equality check
            return abs(current_value - alarm.threshold) < 0.01

    def register_handler(self, action: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        """
        Register notification handler.

        Args:
            action: Action name
            handler: Handler function
        """
        self.notification_handlers[action] = handler
        logger.info(f"Handler registered: {action}")

    def clear_alarm(self, alarm_id: str) -> bool:
        """
        Clear alarm by ID.

        Args:
            alarm_id: Alarm ID

        Returns:
            True if cleared
        """
        for alarm in self.alarms:
            if alarm.alarm_id == alarm_id:
                alarm.triggered = False
                logger.info(f"Alarm cleared: {alarm_id}")
                return True
        return False

    def get_active_alarms(self) -> list[Alarm]:
        """
        Get active (non-triggered) alarms.

        Returns:
            List of active alarms
        """
        return [a for a in self.alarms if not a.triggered]

    def get_triggered_alarms(self) -> list[Alarm]:
        """
        Get triggered alarms.

        Returns:
            List of triggered alarms
        """
        return [a for a in self.alarms if a.triggered]


# Example usage
def example_usage() -> None:
    """Example usage of NotificationWatch."""
    watch = NotificationWatch()

    # Set price alarm
    watch.set_alarm(condition="price_above", threshold=52000.0, action="notify_user")

    # Set volume alarm
    watch.set_alarm(condition="volume_high", threshold=1000000.0, action="send_alert")

    # Check alarms with current value
    triggered = watch.check_alarms(current_value=52500.0)
    print(f"Triggered actions: {len(triggered)}")

    # Get active alarms
    active = watch.get_active_alarms()
    print(f"Active alarms: {len(active)}")


if __name__ == "__main__":
    example_usage()
