"""
AI-Safe Portfolio Analyzer
============================
Wraps portfolio analytics with AI safety approval and output sanitization.
"""

import logging
from datetime import datetime
from typing import Any

from ..security.ai_safety import (
    AISafetyContext,
    AISafetyLevel,
    DataSensitivity,
    PortfolioAISafety,
    get_ai_safety,
)
from ..security.audit_logger import AuditEventType, PortfolioAuditLogger, get_audit_logger
from ..security.portfolio_data_policy import (
    PortfolioDataPolicy,
    get_portfolio_data_policy,
)
from .databricks_analyzer import DatabricksPortfolioAnalyzer

logger = logging.getLogger(__name__)


class AISafePortfolioAnalyzer:
    """
    AI-safe portfolio analyzer with approval and sanitization.

    Enforces AI safety controls before providing analytics.
    """

    def __init__(
        self,
        ai_safety: PortfolioAISafety | None = None,
        policy: PortfolioDataPolicy | None = None,
        audit_logger: PortfolioAuditLogger | None = None,
        analyzer: DatabricksPortfolioAnalyzer | None = None,
    ):
        """
        Initialize AI-safe analyzer.

        Args:
            ai_safety: PortfolioAISafety instance
            policy: PortfolioDataPolicy instance
            audit_logger: PortfolioAuditLogger instance
            analyzer: DatabricksPortfolioAnalyzer instance
        """
        self.ai_safety = ai_safety or get_ai_safety()
        self.policy = policy or get_portfolio_data_policy()
        self.audit_logger = audit_logger or get_audit_logger()
        self.analyzer = analyzer or DatabricksPortfolioAnalyzer()

    def analyze_portfolio(
        self, user_id: str, purpose: str = "portfolio_analysis", require_approval: bool = True
    ) -> dict[str, Any]:
        """
        Analyze portfolio with AI safety approval.

        Args:
            user_id: User ID
            purpose: Purpose of analysis
            require_approval: Whether to require AI approval

        Returns:
            Sanitized portfolio analysis
        """
        # Create AI safety context
        safety_context = AISafetyContext(
            safety_level=AISafetyLevel.RESTRICTED,
            sensitivity=DataSensitivity.CRITICAL,
            purpose=purpose,
            timestamp=datetime.now(),
        )

        # Validate AI access
        if require_approval:
            if not self.ai_safety.validate_ai_access(user_id, purpose, safety_context):
                raise PermissionError("AI access denied: insufficient privileges")

        # Log AI access
        self.audit_logger.log_event(
            event_type=AuditEventType.AI_ACCESS,
            user_id=user_id,
            action="analyze_portfolio",
            details={"purpose": purpose, "approved": True},
        )

        # Get analysis
        analysis = self.analyzer.analyze_portfolio(user_id)

        # Sanitize output
        sanitized_analysis = self._sanitize_analysis(analysis)

        logger.info("AI-safe analysis completed for user")
        return sanitized_analysis

    def get_top_performers(
        self, user_id: str, limit: int = 5, purpose: str = "performance_analysis"
    ) -> list[dict[str, Any]]:
        """
        Get top performers with AI safety.

        Args:
            user_id: User ID
            limit: Number of performers
            purpose: Purpose of analysis

        Returns:
            Sanitized list of top performers
        """
        # Create safety context
        safety_context = AISafetyContext(
            safety_level=AISafetyLevel.RESTRICTED,
            sensitivity=DataSensitivity.CRITICAL,
            purpose=purpose,
            timestamp=datetime.now(),
        )

        # Validate AI access
        if not self.ai_safety.validate_ai_access(user_id, purpose, safety_context):
            raise PermissionError("AI access denied: insufficient privileges")

        # Log AI access
        self.audit_logger.log_event(
            event_type=AuditEventType.AI_ACCESS,
            user_id=user_id,
            action="get_top_performers",
            details={"limit": limit, "purpose": purpose},
        )

        # Get top performers
        performers = self.analyzer.get_top_performers(user_id, limit)

        # Sanitize output (symbol only, no quantities)
        sanitized = []
        for performer in performers:
            sanitized.append(
                {
                    "symbol": performer.get("symbol"),
                    "gain_loss_percentage": round(performer.get("gain_loss_percentage", 0), 2),
                }
            )

        logger.info(f"Retrieved {len(sanitized)} top performers")
        return sanitized

    def get_worst_performers(
        self, user_id: str, limit: int = 5, purpose: str = "risk_analysis"
    ) -> list[dict[str, Any]]:
        """
        Get worst performers with AI safety.

        Args:
            user_id: User ID
            limit: Number of performers
            purpose: Purpose of analysis

        Returns:
            Sanitized list of worst performers
        """
        # Create safety context
        safety_context = AISafetyContext(
            safety_level=AISafetyLevel.RESTRICTED,
            sensitivity=DataSensitivity.CRITICAL,
            purpose=purpose,
            timestamp=datetime.now(),
        )

        # Validate AI access
        if not self.ai_safety.validate_ai_access(user_id, purpose, safety_context):
            raise PermissionError("AI access denied: insufficient privileges")

        # Log AI access
        self.audit_logger.log_event(
            event_type=AuditEventType.AI_ACCESS,
            user_id=user_id,
            action="get_worst_performers",
            details={"limit": limit, "purpose": purpose},
        )

        # Get worst performers
        performers = self.analyzer.get_worst_performers(user_id, limit)

        # Sanitize output (symbol only, no quantities)
        sanitized = []
        for performer in performers:
            sanitized.append(
                {
                    "symbol": performer.get("symbol"),
                    "gain_loss_percentage": round(performer.get("gain_loss_percentage", 0), 2),
                }
            )

        logger.info(f"Retrieved {len(sanitized)} worst performers")
        return sanitized

    def get_sector_allocation(
        self, user_id: str, purpose: str = "allocation_analysis"
    ) -> dict[str, float]:
        """
        Get sector allocation with AI safety.

        Args:
            user_id: User ID
            purpose: Purpose of analysis

        Returns:
            Sanitized sector allocation
        """
        # Create safety context
        from datetime import datetime

        safety_context = AISafetyContext(
            safety_level=AISafetyLevel.RESTRICTED,
            sensitivity=DataSensitivity.RESTRICTED,
            purpose=purpose,
            timestamp=datetime.now(),
        )

        # Validate AI access
        if not self.ai_safety.validate_ai_access(user_id, purpose, safety_context):
            raise PermissionError("AI access denied: insufficient privileges")

        # Log AI access
        self.audit_logger.log_event(
            event_type=AuditEventType.AI_ACCESS,
            user_id=user_id,
            action="get_sector_allocation",
            details={"purpose": purpose},
        )

        # Get sector allocation
        allocation = self.analyzer.get_sector_allocation(user_id)

        # Sanitize output (round percentages)
        sanitized = {sector: round(percentage, 2) for sector, percentage in allocation.items()}

        logger.info("Retrieved sector allocation")
        return sanitized

    def get_concentration_risk(
        self, user_id: str, purpose: str = "risk_analysis"
    ) -> dict[str, Any]:
        """
        Get concentration risk with AI safety.

        Args:
            user_id: User ID
            purpose: Purpose of analysis

        Returns:
            Sanitized concentration risk metrics
        """
        # Create safety context
        from datetime import datetime

        safety_context = AISafetyContext(
            safety_level=AISafetyLevel.RESTRICTED,
            sensitivity=DataSensitivity.RESTRICTED,
            purpose=purpose,
            timestamp=datetime.now(),
        )

        # Validate AI access
        if not self.ai_safety.validate_ai_access(user_id, purpose, safety_context):
            raise PermissionError("AI access denied: insufficient privileges")

        # Log AI access
        self.audit_logger.log_event(
            event_type=AuditEventType.AI_ACCESS,
            user_id=user_id,
            action="get_concentration_risk",
            details={"purpose": purpose},
        )

        # Get concentration risk
        risk = self.analyzer.get_concentration_risk(user_id)

        # Sanitize output (round percentages)
        sanitized = {
            "risk_level": risk.get("risk_level", "UNKNOWN"),
            "top_position_percentage": round(risk.get("top_position_percentage", 0), 2),
            "top_3_percentage": round(risk.get("top_3_percentage", 0), 2),
            "recommendation": risk.get("recommendation", "No data available"),
        }

        logger.info("Retrieved concentration risk")
        return sanitized

    def get_safe_recommendations(
        self, user_id: str, purpose: str = "recommendation_generation"
    ) -> dict[str, Any]:
        """
        Get safe AI recommendations with sanitization.

        Args:
            user_id: User ID
            purpose: Purpose of recommendations

        Returns:
            Sanitized recommendations
        """
        # Create safety context
        safety_context = AISafetyContext(
            safety_level=AISafetyLevel.RESTRICTED,
            sensitivity=DataSensitivity.CRITICAL,
            purpose=purpose,
            timestamp=datetime.now(),
        )

        # Validate AI access
        if not self.ai_safety.validate_ai_access(user_id, purpose, safety_context):
            raise PermissionError("AI access denied: insufficient privileges")

        # Log AI access
        self.audit_logger.log_event(
            event_type=AuditEventType.AI_ACCESS,
            user_id=user_id,
            action="get_safe_recommendations",
            details={"purpose": purpose},
        )

        # Get basic metrics
        analysis = self.analyzer.analyze_portfolio(user_id)

        # Generate safe recommendations (no specific buy/sell advice)
        recommendations = {
            "total_positions": analysis.get("total_positions", 0),
            "diversification_score": self._calculate_diversification(analysis),
            "risk_level": self._assess_risk_level(analysis),
            "recommendations": [
                "Review portfolio diversification",
                "Monitor concentration risk",
                "Consider rebalancing if needed",
            ],
        }

        # Sanitize AI output
        sanitized = self.ai_safety.sanitize_for_ai_output(recommendations)

        logger.info("Generated safe recommendations")
        return sanitized

    def _sanitize_analysis(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Sanitize portfolio analysis output."""
        # Remove sensitive fields
        sanitized = {
            "total_positions": analysis.get("total_positions", 0),
            "total_value": round(analysis.get("total_value", 0), 2),
            "total_purchase_value": round(analysis.get("total_purchase_value", 0), 2),
            "total_commission": round(analysis.get("total_commission", 0), 2),
            "total_gain_loss": round(analysis.get("total_gain_loss", 0), 2),
            "gain_loss_percentage": round(analysis.get("gain_loss_percentage", 0), 2),
            "positions_count": len(analysis.get("positions", [])),
        }

        return sanitized

    def _calculate_diversification(self, analysis: dict[str, Any]) -> float:
        """Calculate diversification score (0-100)."""
        total_positions = analysis.get("total_positions", 0)
        if total_positions == 0:
            return 0.0

        # Simple diversification based on position count
        # More positions = better diversification (up to 20)
        return float(min((total_positions / 20) * 100, 100.0))

    def _assess_risk_level(self, analysis: dict[str, Any]) -> str:
        """Assess portfolio risk level."""
        total_value = analysis.get("total_value", 0)
        positions = analysis.get("positions", [])

        if total_value == 0 or not positions:
            return "UNKNOWN"

        # Check top position concentration
        top_position_value = positions[0].get("current_value", 0)
        top_position_percentage = (top_position_value / total_value) * 100

        if top_position_percentage > 50:
            return "HIGH"
        elif top_position_percentage > 30:
            return "MEDIUM"
        else:
            return "LOW"


def get_ai_safe_analyzer() -> AISafePortfolioAnalyzer:
    """
    Get singleton instance of AISafePortfolioAnalyzer.

    Returns:
        AISafePortfolioAnalyzer instance
    """
    return AISafePortfolioAnalyzer()
