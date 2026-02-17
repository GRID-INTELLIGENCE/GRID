"""
Cognitive Explainer - XAI (Explainable AI) for Routing Decisions.

Provides human-readable explanations for:
- Routing decisions
- Priority assignments
- Pattern detections
- Cognitive state impacts
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ExplanationLevel(Enum):
    """Level of detail for explanations."""

    BRIEF = "brief"  # One-liner
    STANDARD = "standard"  # Normal explanation
    DETAILED = "detailed"  # Full technical details
    DEBUG = "debug"  # All available information


class ExplanationCategory(Enum):
    """Categories of explanations."""

    ROUTING = "routing"
    PRIORITY = "priority"
    PATTERN = "pattern"
    COGNITIVE = "cognitive"
    TEMPORAL = "temporal"


@dataclass
class ExplanationFactor:
    """A single factor contributing to a decision."""

    name: str
    weight: float
    value: Any
    description: str
    impact: str  # positive, negative, neutral

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "weight": self.weight,
            "value": self.value,
            "description": self.description,
            "impact": self.impact,
        }


@dataclass
class Explanation:
    """Complete explanation for a decision."""

    decision_id: str
    category: ExplanationCategory
    summary: str
    reasoning: str
    factors: list[ExplanationFactor] = field(default_factory=list)
    confidence: float = 0.8
    alternatives: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "category": self.category.value,
            "summary": self.summary,
            "reasoning": self.reasoning,
            "factors": [f.to_dict() for f in self.factors],
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def to_brief(self) -> str:
        """Get brief one-line explanation."""
        return self.summary

    def to_standard(self) -> str:
        """Get standard explanation."""
        lines = [
            f"**Decision:** {self.summary}",
            f"**Reasoning:** {self.reasoning}",
            f"**Confidence:** {self.confidence * 100:.0f}%",
        ]

        if self.factors:
            lines.append("\n**Key Factors:**")
            for factor in self.factors[:3]:
                lines.append(f"  • {factor.name}: {factor.description}")

        if self.recommendations:
            lines.append("\n**Recommendations:**")
            for rec in self.recommendations[:2]:
                lines.append(f"  → {rec}")

        return "\n".join(lines)

    def to_detailed(self) -> str:
        """Get detailed explanation."""
        lines = [
            f"# Decision Explanation: {self.decision_id}",
            f"**Category:** {self.category.value}",
            f"**Timestamp:** {self.timestamp.isoformat()}",
            "",
            "## Summary",
            self.summary,
            "",
            "## Reasoning",
            self.reasoning,
            "",
            f"## Confidence Score: {self.confidence * 100:.1f}%",
        ]

        if self.factors:
            lines.extend(["", "## Contributing Factors"])
            for i, factor in enumerate(self.factors, 1):
                lines.extend(
                    [
                        f"### Factor {i}: {factor.name}",
                        f"- **Weight:** {factor.weight}",
                        f"- **Value:** {factor.value}",
                        f"- **Impact:** {factor.impact}",
                        f"- **Description:** {factor.description}",
                        "",
                    ]
                )

        if self.alternatives:
            lines.extend(["## Alternative Decisions Considered"])
            for alt in self.alternatives:
                lines.append(f"- {alt}")

        if self.recommendations:
            lines.extend(["", "## Recommendations"])
            for rec in self.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


class CognitiveExplainer:
    """
    XAI system for cognitive routing decisions.

    Generates human-readable explanations for:
    - Why a particular route was chosen
    - Why priority was adjusted
    - What patterns were detected
    - How cognitive state influenced decisions
    """

    def __init__(self):
        self._explanation_history: list[Explanation] = []
        self._templates = self._load_templates()

    def _load_templates(self) -> dict[str, str]:
        """Load explanation templates."""
        return {
            "routing_explicit": "Activity routed to {target} because explicit target was specified in metadata.",
            "routing_pattern": "Activity routed to {target} based on detected {pattern} pattern.",
            "routing_type": "Activity routed to {target} based on activity type: {type}.",
            "routing_priority": "Activity routed to {target} due to {priority} priority level.",
            "priority_security": "Priority elevated to ENTERPRISE due to security incident pattern detection.",
            "priority_critical": "Priority elevated to CRITICAL due to critical pattern detection.",
            "priority_temporal": "Priority adjusted based on temporal context ({context}).",
            "pattern_detected": "Pattern '{pattern}' detected with {confidence}% confidence.",
            "cognitive_overload": "Cognitive load high ({load}) - simplified processing applied.",
            "cognitive_optimal": "Cognitive state optimal - full analysis capabilities available.",
        }

    def explain_routing_decision(
        self,
        activity: Any,
        route: str,
        decision_context: dict[str, Any] | None = None,
    ) -> Explanation:
        """
        Explain why a routing decision was made.

        Args:
            activity: The activity that was routed
            route: The route that was chosen
            decision_context: Additional context about the decision

        Returns:
            Explanation object with reasoning
        """
        factors = []
        reasoning_parts = []

        # Analyze routing factors
        activity_type = getattr(activity, "type", None)
        priority = getattr(activity, "priority", None)
        meta = getattr(getattr(activity, "context", None), "meta", {})
        cognitive_insights = meta.get("cognitive_insights", {})

        # Check for explicit target
        if meta.get("target_system"):
            factors.append(
                ExplanationFactor(
                    name="explicit_target",
                    weight=1.0,
                    value=meta["target_system"],
                    description="Explicit target system specified in metadata",
                    impact="positive",
                )
            )
            reasoning_parts.append(self._templates["routing_explicit"].format(target=route))

        # Check for pattern matches
        patterns = cognitive_insights.get("patterns", [])
        if patterns:
            factors.append(
                ExplanationFactor(
                    name="pattern_matches",
                    weight=0.8,
                    value=patterns,
                    description=f"Matched {len(patterns)} cognitive pattern(s)",
                    impact="positive",
                )
            )
            reasoning_parts.append(self._templates["routing_pattern"].format(target=route, pattern=patterns[0]))

        # Check activity type
        if activity_type:
            type_value = activity_type.value if hasattr(activity_type, "value") else str(activity_type)
            factors.append(
                ExplanationFactor(
                    name="activity_type",
                    weight=0.7,
                    value=type_value,
                    description=f"Activity type: {type_value}",
                    impact="neutral",
                )
            )
            reasoning_parts.append(self._templates["routing_type"].format(target=route, type=type_value))

        # Check priority
        if priority:
            priority_value = priority.value if hasattr(priority, "value") else str(priority)
            factors.append(
                ExplanationFactor(
                    name="priority",
                    weight=0.6,
                    value=priority_value,
                    description=f"Priority level: {priority_value}",
                    impact="positive" if priority_value in ("enterprise", "critical") else "neutral",
                )
            )

        # Cognitive context
        cog_context = cognitive_insights.get("context", {})
        if cog_context:
            factors.append(
                ExplanationFactor(
                    name="cognitive_state",
                    weight=0.4,
                    value=cog_context.get("state", "unknown"),
                    description="Cognitive state during routing",
                    impact="neutral",
                )
            )

        # Build summary
        if patterns:
            summary = f"Routed to {route} based on {patterns[0]} pattern"
        elif activity_type:
            type_str = activity_type.value if hasattr(activity_type, "value") else str(activity_type)
            summary = f"Routed to {route} based on {type_str} activity type"
        else:
            summary = f"Routed to {route} using default routing logic"

        # Calculate confidence
        confidence = sum(f.weight for f in factors) / (len(factors) or 1)

        # Generate alternatives
        alternatives = self._generate_alternatives(route, factors)

        # Generate recommendations
        recommendations = cognitive_insights.get("recommendations", [])

        explanation = Explanation(
            decision_id=f"route_{getattr(activity, 'id', 'unknown')}",
            category=ExplanationCategory.ROUTING,
            summary=summary,
            reasoning=" ".join(reasoning_parts) if reasoning_parts else "Standard routing logic applied.",
            factors=factors,
            confidence=min(1.0, confidence),
            alternatives=alternatives,
            recommendations=recommendations,
        )

        self._explanation_history.append(explanation)
        return explanation

    def explain_priority_assignment(
        self,
        activity: Any,
        new_priority: str,
        old_priority: str | None = None,
        reason: str | None = None,
    ) -> Explanation:
        """
        Explain why a priority was assigned or changed.

        Args:
            activity: The activity
            new_priority: The new priority level
            old_priority: The previous priority (if changed)
            reason: The reason for the change

        Returns:
            Explanation object
        """
        factors = []
        reasoning_parts = []

        # Determine if this was a boost
        was_boosted = old_priority and old_priority != new_priority

        # Analyze the reason
        if reason == "security_incident":
            factors.append(
                ExplanationFactor(
                    name="security_pattern",
                    weight=1.0,
                    value="SECURITY_INCIDENT_PATTERN",
                    description="Security incident pattern detected in activity",
                    impact="positive",
                )
            )
            reasoning_parts.append(self._templates["priority_security"])

        elif reason == "critical_pattern":
            factors.append(
                ExplanationFactor(
                    name="critical_pattern",
                    weight=0.9,
                    value="CRITICAL_PATTERN",
                    description="Critical pattern detected in activity",
                    impact="positive",
                )
            )
            reasoning_parts.append(self._templates["priority_critical"])

        elif reason:
            factors.append(
                ExplanationFactor(
                    name="custom_reason",
                    weight=0.7,
                    value=reason,
                    description=f"Priority adjusted due to: {reason}",
                    impact="positive",
                )
            )
            reasoning_parts.append(f"Priority set based on: {reason}")

        # Build summary
        if was_boosted:
            summary = f"Priority boosted from {old_priority} to {new_priority}"
        else:
            summary = f"Priority assigned as {new_priority}"

        explanation = Explanation(
            decision_id=f"priority_{getattr(activity, 'id', 'unknown')}",
            category=ExplanationCategory.PRIORITY,
            summary=summary,
            reasoning=" ".join(reasoning_parts) if reasoning_parts else "Default priority assignment.",
            factors=factors,
            confidence=0.85 if factors else 0.5,
        )

        self._explanation_history.append(explanation)
        return explanation

    def explain_pattern_detection(
        self,
        pattern_name: str,
        confidence: float,
        matched_features: list[str],
        input_summary: str,
    ) -> Explanation:
        """
        Explain why a pattern was detected.

        Args:
            pattern_name: Name of the detected pattern
            confidence: Detection confidence
            matched_features: Features that matched
            input_summary: Summary of the input

        Returns:
            Explanation object
        """
        factors = [
            ExplanationFactor(
                name=feature,
                weight=1.0 / len(matched_features) if matched_features else 0,
                value=True,
                description=f"Feature '{feature}' matched in input",
                impact="positive",
            )
            for feature in matched_features
        ]

        summary = f"Pattern '{pattern_name}' detected with {confidence * 100:.0f}% confidence"
        reasoning = (
            f"The input matched {len(matched_features)} feature(s) of the {pattern_name} pattern. "
            f"Input context: {input_summary}"
        )

        explanation = Explanation(
            decision_id=f"pattern_{pattern_name}_{datetime.now().timestamp()}",
            category=ExplanationCategory.PATTERN,
            summary=summary,
            reasoning=reasoning,
            factors=factors,
            confidence=confidence,
        )

        self._explanation_history.append(explanation)
        return explanation

    def _generate_alternatives(self, chosen_route: str, factors: list[ExplanationFactor]) -> list[str]:
        """Generate alternative routing options that were considered."""
        alternatives = []
        route_options = ["grid", "eufle", "apps", "nexus"]

        for option in route_options:
            if option != chosen_route:
                alternatives.append(f"{option} (not selected)")

        return alternatives[:3]

    def get_explanation(
        self,
        decision_id: str,
        level: ExplanationLevel = ExplanationLevel.STANDARD,
    ) -> str | None:
        """
        Get an explanation by decision ID.

        Args:
            decision_id: The decision to explain
            level: Level of detail

        Returns:
            Formatted explanation string
        """
        explanation = next((e for e in self._explanation_history if e.decision_id == decision_id), None)

        if not explanation:
            return None

        if level == ExplanationLevel.BRIEF:
            return explanation.to_brief()
        elif level == ExplanationLevel.STANDARD:
            return explanation.to_standard()
        elif level == ExplanationLevel.DETAILED:
            return explanation.to_detailed()
        else:  # DEBUG
            return str(explanation.to_dict())

    def get_recent_explanations(self, count: int = 20) -> list[dict[str, Any]]:
        """Get recent explanations."""
        return [e.to_dict() for e in self._explanation_history[-count:]]

    def clear_history(self) -> None:
        """Clear explanation history."""
        self._explanation_history.clear()


# Singleton instance
_explainer: CognitiveExplainer | None = None


def get_cognitive_explainer() -> CognitiveExplainer:
    """Get the singleton CognitiveExplainer instance."""
    global _explainer
    if _explainer is None:
        _explainer = CognitiveExplainer()
    return _explainer
