"""
AI Safety Privileges for Portfolio Data
=======================================
AI safety controls for portfolio data access and processing.

Security Level: CRITICAL
Privacy: Personal Sensitive Information
AI Safety: Full privileges required
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AISafetyLevel(Enum):
    """AI safety levels for data access."""

    SAFE = "SAFE"
    CAUTION = "CAUTION"
    RESTRICTED = "RESTRICTED"
    PROHIBITED = "PROHIBITED"


class DataSensitivity(Enum):
    """Data sensitivity levels."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    CRITICAL = "CRITICAL"


@dataclass
class AISafetyContext:
    """AI safety context for data access."""

    safety_level: AISafetyLevel
    sensitivity: DataSensitivity
    purpose: str
    timestamp: datetime
    approved: bool = False


class PortfolioAISafety:
    """
    AI safety controls for portfolio data.

    Ensures AI systems only access portfolio data with proper authorization.
    """

    def __init__(self) -> None:
        """Initialize AI safety module."""
        self.safety_level = AISafetyLevel.RESTRICTED
        self.sensitivity = DataSensitivity.CRITICAL
        self.access_log: list[dict[str, Any]] = []
        self.max_log_entries = 1000

    def validate_ai_access(self, user_id: str, purpose: str, context: AISafetyContext) -> bool:
        """
        Validate AI access to portfolio data.

        Args:
            user_id: User ID
            purpose: Purpose of access
            context: AI safety context

        Returns:
            True if access granted
        """
        # Check sensitivity level
        if self.sensitivity == DataSensitivity.CRITICAL:
            if not context.approved:
                self._log_access_denied("AI access not approved for critical data")
                return False

        # Validate purpose
        valid_purposes = [
            "portfolio_analysis",
            "trading_recommendations",
            "risk_assessment",
            "performance_tracking",
        ]

        if purpose not in valid_purposes:
            self._log_access_denied(f"Invalid purpose: {purpose}")
            return False

        # Check safety level
        if context.safety_level == AISafetyLevel.PROHIBITED:
            self._log_access_denied("Prohibited access level")
            return False

        # Grant access
        self._log_access_granted(f"AI access granted for purpose: {purpose}")
        return True

    def _log_access_denied(self, reason: str) -> None:
        """
        Log access denied event.

        Args:
            reason: Reason for denial
        """
        event = {
            "event_type": "ACCESS_DENIED",
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "sensitivity": self.sensitivity.value,
            "safety_level": self.safety_level.value,
        }

        self.access_log.append(event)
        logger.warning(f"AI Access Denied: {reason}")

    def _log_access_granted(self, reason: str) -> None:
        """
        Log access granted event.

        Args:
            reason: Reason for grant
        """
        event = {
            "event_type": "ACCESS_GRANTED",
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "sensitivity": self.sensitivity.value,
            "safety_level": self.safety_level.value,
        }

        self.access_log.append(event)
        logger.info(f"AI Access Granted: {reason}")

    def create_safety_context(self, purpose: str, approved: bool = False) -> AISafetyContext:
        """
        Create AI safety context.

        Args:
            purpose: Purpose of access
            approved: Whether access is approved

        Returns:
            AI safety context
        """
        return AISafetyContext(
            safety_level=self.safety_level,
            sensitivity=self.sensitivity,
            purpose=purpose,
            timestamp=datetime.now(),
            approved=approved,
        )

    def sanitize_for_ai_output(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize data for AI output.

        Args:
            data: Raw data

        Returns:
            Sanitized data
        """
        sanitized = {
            "total_positions": data.get("total_positions", 0),
            "total_value": data.get("total_value", 0.0),
            "total_gain_loss": data.get("total_gain_loss", 0.0),
            "gain_loss_percentage": data.get("gain_loss_percentage", 0.0),
            "risk_level": data.get("risk_level", "UNKNOWN"),
        }

        # Remove sensitive fields
        for key in ["positions", "user_id", "transaction_history"]:
            if key in data:
                sanitized[f"{key}_count"] = len(data[key]) if isinstance(data[key], list) else 1

        return sanitized

    def get_access_log(
        self, event_type: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get access log entries.

        Args:
            event_type: Event type to filter by
            limit: Max entries to return

        Returns:
            Access log entries
        """
        if event_type:
            filtered = [entry for entry in self.access_log if entry.get("event_type") == event_type]
            return filtered[-limit:]

        return self.access_log[-limit:]


# Singleton instance
_ai_safety_instance: PortfolioAISafety | None = None


def get_ai_safety() -> PortfolioAISafety:
    """
    Get singleton AI safety instance.

    Returns:
        PortfolioAISafety instance
    """
    global _ai_safety_instance
    if _ai_safety_instance is None:
        _ai_safety_instance = PortfolioAISafety()
    return _ai_safety_instance


# Example usage
def example_usage() -> None:
    """Example usage of AI safety controls."""
    print("=" * 70)
    print("AI Safety Controls Demo")
    print("=" * 70)
    print()

    # Initialize AI safety
    ai_safety = PortfolioAISafety()

    # Create safety context
    context = ai_safety.create_safety_context(purpose="portfolio_analysis", approved=True)
    print("AI Safety Context Created")
    print(f"  Safety Level: {context.safety_level.value}")
    print(f"  Sensitivity: {context.sensitivity.value}")
    print(f"  Purpose: {context.purpose}")
    print(f"  Approved: {context.approved}")
    print()

    # Validate AI access
    granted = ai_safety.validate_ai_access(
        user_id="user123", purpose="portfolio_analysis", context=context
    )
    print(f"AI Access Granted: {granted}")
    print()

    # Sanitize data for AI output
    portfolio_data = {
        "total_positions": 5,
        "total_value": 50000.0,
        "total_gain_loss": 5000.0,
        "gain_loss_percentage": 10.0,
        "positions": [
            {"symbol": "AAPL", "quantity": 50, "value": 10000.0},
            {"symbol": "MSFT", "quantity": 30, "value": 15000.0},
        ],
    }

    sanitized = ai_safety.sanitize_for_ai_output(portfolio_data)
    print("Sanitized Data for AI Output:")
    print(f"  Total Positions: {sanitized['total_positions']}")
    print(f"  Total Value: ${sanitized['total_value']:,.2f}")
    print(f"  Positions Count: {sanitized['positions_count']}")
    print("  (Individual positions removed for security)")
    print()

    # Get access log
    access_log = ai_safety.get_access_log(limit=5)
    print(f"Access Log Entries: {len(access_log)}")
    for entry in access_log:
        print(f"  {entry['event_type']}: {entry['reason']}")


if __name__ == "__main__":
    example_usage()
