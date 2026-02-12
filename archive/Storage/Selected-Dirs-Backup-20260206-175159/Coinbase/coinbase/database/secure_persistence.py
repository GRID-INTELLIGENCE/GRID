"""
Secure Portfolio Persistence
=============================
Wraps Databricks persistence with security validation and audit logging.
"""

import logging
from typing import Any

from ..security.audit_logger import AuditEventType, PortfolioAuditLogger, get_audit_logger
from ..security.portfolio_data_policy import (
    AccessPurpose,
    OutputRule,
    PortfolioDataPolicy,
    get_portfolio_data_policy,
)
from ..security.portfolio_security import (
    AccessLevel,
    PortfolioDataSecurity,
    get_portfolio_security,
)
from .databricks_persistence import DatabricksPortfolioPersistence, PortfolioPosition

logger = logging.getLogger(__name__)


class SecurePortfolioPersistence:
    """
    Secure wrapper for portfolio persistence with guardrails.

    Enforces security validation, audit logging, and output sanitization.
    """

    def __init__(
        self,
        security: PortfolioDataSecurity | None = None,
        policy: PortfolioDataPolicy | None = None,
        audit_logger: PortfolioAuditLogger | None = None,
        persistence: DatabricksPortfolioPersistence | None = None,
    ):
        """
        Initialize secure persistence.

        Args:
            security: PortfolioDataSecurity instance
            policy: PortfolioDataPolicy instance
            audit_logger: PortfolioAuditLogger instance
            persistence: DatabricksPortfolioPersistence instance
        """
        self.security = security or get_portfolio_security()
        self.policy = policy or get_portfolio_data_policy()
        self.audit_logger = audit_logger or get_audit_logger()
        self.persistence = persistence or DatabricksPortfolioPersistence()

    def save_position(
        self, user_id: str, position: PortfolioPosition, context: dict[str, Any] | None = None
    ) -> None:
        """
        Save position with security validation.

        Args:
            user_id: User ID
            position: Portfolio position data
            context: Optional context metadata
        """
        # Validate access
        security_context = self.security.create_security_context(
            user_id=user_id, access_level=AccessLevel.READ_WRITE
        )

        if not self.security.validate_access(security_context):
            raise PermissionError("Access denied: insufficient privileges")

        # Log access
        self.audit_logger.log_event(
            event_type=AuditEventType.WRITE,
            user_id=user_id,
            action="save_position",
            details={
                "symbol": position.symbol,
                "quantity": position.quantity,
                "context": context or {},
            },
        )

        # Save to persistence
        self.persistence.save_position(user_id, position)
        logger.info(f"Securely saved position: {position.symbol}")

    def save_positions_batch(
        self,
        user_id: str,
        positions: list[PortfolioPosition],
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Save multiple positions with security validation.

        Args:
            user_id: User ID
            positions: List of portfolio positions
            context: Optional context metadata
        """
        # Validate access
        security_context = self.security.create_security_context(
            user_id=user_id, access_level=AccessLevel.READ_WRITE
        )

        if not self.security.validate_access(security_context):
            raise PermissionError("Access denied: insufficient privileges")

        # Log access
        self.audit_logger.log_event(
            event_type=AuditEventType.WRITE,
            user_id=user_id,
            action="save_positions_batch",
            details={
                "count": len(positions),
                "symbols": [p.symbol for p in positions],
                "context": context or {},
            },
        )

        # Save to persistence
        self.persistence.save_positions_batch(user_id, positions)
        logger.info(f"Securely saved {len(positions)} positions")

    def save_portfolio_summary(
        self, user_id: str, summary: dict[str, Any], context: dict[str, Any] | None = None
    ) -> None:
        """
        Save portfolio summary with security validation.

        Args:
            user_id: User ID
            summary: Portfolio summary data
            context: Optional context metadata
        """
        # Validate access
        security_context = self.security.create_security_context(
            user_id=user_id, access_level=AccessLevel.READ_WRITE
        )

        if not self.security.validate_access(security_context):
            raise PermissionError("Access denied: insufficient privileges")

        # Log access
        self.audit_logger.log_event(
            event_type=AuditEventType.WRITE,
            user_id=user_id,
            action="save_portfolio_summary",
            details={"total_value": summary.get("total_value", 0), "context": context or {}},
        )

        # Save to persistence
        self.persistence.save_portfolio_summary(user_id, summary)
        logger.info("Securely saved portfolio summary")

    def get_positions(
        self,
        user_id: str,
        purpose: AccessPurpose = AccessPurpose.ANALYTICS,
        output_rule: OutputRule = OutputRule.SANITIZED,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get positions with security validation and sanitization.

        Args:
            user_id: User ID
            purpose: Purpose of access
            output_rule: Output sanitization rule
            context: Optional context metadata

        Returns:
            Sanitized list of positions
        """
        # Validate access
        security_context = self.security.create_security_context(
            user_id=user_id, access_level=AccessLevel.READ_ONLY
        )

        if not self.security.validate_access(security_context):
            raise PermissionError("Access denied: insufficient privileges")

        # Log access
        self.audit_logger.log_event(
            event_type=AuditEventType.READ,
            user_id=user_id,
            action="get_positions",
            details={
                "purpose": purpose.value,
                "output_rule": output_rule.value,
                "context": context or {},
            },
        )

        # Get from persistence
        positions = self.persistence.get_positions(user_id)

        # Sanitize output
        sanitized_positions = []
        for position in positions:
            sanitized = self.policy.validate_output_dict(
                position, purpose=purpose, output_rule=output_rule
            )
            if sanitized:
                sanitized_positions.append(sanitized)

        logger.info(f"Securely retrieved {len(sanitized_positions)} positions")
        return sanitized_positions

    def get_portfolio_summary(
        self,
        user_id: str,
        purpose: AccessPurpose = AccessPurpose.ANALYTICS,
        output_rule: OutputRule = OutputRule.SANITIZED,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Get portfolio summary with security validation and sanitization.

        Args:
            user_id: User ID
            purpose: Purpose of access
            output_rule: Output sanitization rule
            context: Optional context metadata

        Returns:
            Sanitized portfolio summary or None
        """
        # Validate access
        security_context = self.security.create_security_context(
            user_id=user_id, access_level=AccessLevel.READ_ONLY
        )

        if not self.security.validate_access(security_context):
            raise PermissionError("Access denied: insufficient privileges")

        # Log access
        self.audit_logger.log_event(
            event_type=AuditEventType.READ,
            user_id=user_id,
            action="get_portfolio_summary",
            details={
                "purpose": purpose.value,
                "output_rule": output_rule.value,
                "context": context or {},
            },
        )

        # Get from persistence
        summary = self.persistence.get_portfolio_summary(user_id)

        if summary is None:
            return None

        # Sanitize output
        sanitized_summary = self.policy.validate_output_dict(
            summary, purpose=purpose, output_rule=output_rule
        )

        logger.info("Securely retrieved portfolio summary")
        return sanitized_summary

    def get_safe_metrics(
        self, user_id: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Get safe metrics only (no raw data).

        Args:
            user_id: User ID
            context: Optional context metadata

        Returns:
            Dictionary of safe metrics
        """
        # Validate access
        security_context = self.security.create_security_context(
            user_id=user_id, access_level=AccessLevel.READ_ONLY
        )

        if not self.security.validate_access(security_context):
            raise PermissionError("Access denied: insufficient privileges")

        # Log access
        self.audit_logger.log_event(
            event_type=AuditEventType.READ,
            user_id=user_id,
            action="get_safe_metrics",
            details={"context": context or {}},
        )

        # Get summary
        summary = self.persistence.get_portfolio_summary(user_id)

        if summary is None:
            return {
                "total_positions": 0,
                "total_value": 0.0,
                "total_gain_loss": 0.0,
                "gain_loss_percentage": 0.0,
            }

        # Return only safe metrics
        return {
            "total_positions": summary.get("total_positions", 0),
            "total_value": round(summary.get("total_value", 0.0), 2),
            "total_gain_loss": round(summary.get("total_gain_loss", 0.0), 2),
            "gain_loss_percentage": round(summary.get("gain_loss_percentage", 0.0), 2),
        }


def get_secure_persistence() -> SecurePortfolioPersistence:
    """
    Get singleton instance of SecurePortfolioPersistence.

    Returns:
        SecurePortfolioPersistence instance
    """
    return SecurePortfolioPersistence()
