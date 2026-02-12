"""Human-readable explanations for each cognition pattern.

This module provides templates and generators for explaining the 9 cognition
patterns to users in an accessible, meaningful way.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PatternExplanation:
    """Human-readable explanation for a cognition pattern."""

    pattern_name: str
    short_description: str
    full_explanation: str
    when_applies: str
    what_to_do: str
    benefits: list[str]


# Pattern explanations dictionary
PATTERN_EXPLANATIONS: dict[str, PatternExplanation] = {
    "flow": PatternExplanation(
        pattern_name="Flow",
        short_description="You are in a state of optimal experience with balanced cognitive load.",
        full_explanation=(
            "Flow is the psychological state of being completely absorbed in an activity. "
            "In this state, you experience: deep focus, clear goals, immediate feedback, "
            "a sense of control, and a distorted sense of time. Your cognitive load is "
            "balanced - not too easy (boring) or too hard (anxious)."
        ),
        when_applies=(
            "Flow applies when you're working on a challenging task that matches your skills, "
            "you're fully engaged, and you're making steady progress without interruption."
        ),
        what_to_do=(
            "To maintain flow: avoid interruptions, maintain the challenge level, and "
            "focus on the task at hand. If you're losing flow, adjust the difficulty or "
            "remove distractions."
        ),
        benefits=[
            "Increased productivity and efficiency",
            "Enhanced creativity and problem-solving",
            "Greater enjoyment and satisfaction",
            "Improved learning and skill development",
        ],
    ),
    "spatial": PatternExplanation(
        pattern_name="Spatial",
        short_description="This involves understanding relationships and positioning in information structures.",
        full_explanation=(
            "Spatial patterns involve how information is organized in space. This includes: "
            "the relationships between different concepts, how information is positioned "
            "relative to other information, and the geometric structure of your knowledge. "
            "Strong spatial patterns indicate clear mental organization."
        ),
        when_applies=(
            "Spatial patterns apply when you're working with complex information that can "
            "be organized visually or geometrically, such as software architecture, data "
            "structures, or conceptual models."
        ),
        what_to_do=(
            "Leverage spatial thinking: use diagrams, mind maps, and visual representations "
            "to organize information. Consider spatial metaphors for abstract concepts."
        ),
        benefits=[
            "Better mental organization of complex information",
            "Improved ability to navigate large codebases or systems",
            "Enhanced understanding of relationships and dependencies",
            "More efficient problem decomposition",
        ],
    ),
    "rhythm": PatternExplanation(
        pattern_name="Rhythm",
        short_description="This involves detecting and establishing regular patterns in your work cadence.",
        full_explanation=(
            "Rhythm patterns reflect the temporal regularity of your work. A strong rhythm "
            "means you're working with consistent timing, predictable patterns, and a steady "
            "cadence. Good rhythm helps you anticipate what comes next and maintain momentum."
        ),
        when_applies=(
            "Rhythm applies when you're working on repetitive tasks, following established "
            "processes, or engaging in activities with clear timing patterns (like test "
            "cycles, deployments, or daily workflows)."
        ),
        what_to_do=(
            "Establish and maintain rhythm: create consistent timing for related activities, "
            "minimize interruptions during rhythmic work, and use predictability to your advantage."
        ),
        benefits=[
            "Increased predictability and planning accuracy",
            "Reduced cognitive overhead from timing uncertainty",
            "Better anticipation of next steps",
            "Improved team coordination",
        ],
    ),
    "color": PatternExplanation(
        pattern_name="Color",
        short_description="This fuses multiple dimensions into a unified, multi-faceted understanding.",
        full_explanation=(
            "Color patterns represent the fusion of multiple attributes or dimensions. Just as "
            "colors combine hue, saturation, and luminance, this pattern combines different "
            "aspects of information. Strong color patterns indicate rich, multi-dimensional "
            "understanding and the ability to synthesize diverse information."
        ),
        when_applies=(
            "Color patterns apply when you're working with complex, multi-faceted problems "
            "that require considering multiple dimensions simultaneously, such as performance "
            "optimization (speed, memory, readability), or architecture decisions (scalability, "
            "maintainability, security)."
        ),
        what_to_do=(
            "Embrace multi-dimensional thinking: use color-coding for related concepts, "
            "consider multiple attributes simultaneously, and look for trade-offs between "
            "different dimensions."
        ),
        benefits=[
            "More comprehensive understanding of complex systems",
            "Better identification of trade-offs and synergies",
            "Enhanced ability to see the 'big picture'",
            "Improved decision-making with multiple criteria",
        ],
    ),
    "repetition": PatternExplanation(
        pattern_name="Repetition",
        short_description="This detects recurring patterns and opportunities for automation.",
        full_explanation=(
            "Repetition patterns identify behaviors, tasks, or structures that occur repeatedly. "
            "Strong repetition suggests opportunities for automation, abstraction, or "
            "systematization. Recognizing repetition helps reduce redundancy and improve "
            "efficiency."
        ),
        when_applies=(
            "Repetition applies when you find yourself doing similar tasks multiple times, "
            "encountering similar code patterns, or solving related problems repeatedly."
        ),
        what_to_do=(
            "Act on repetition: automate repetitive tasks, extract common patterns into "
            "reusable components, and look for opportunities to reduce duplication through "
            "abstraction."
        ),
        benefits=[
            "Increased efficiency through automation",
            "Reduced errors from manual repetition",
            "More maintainable code and systems",
            "Faster development of similar features",
        ],
    ),
    "deviation": PatternExplanation(
        pattern_name="Deviation",
        short_description="This detects unexpected changes and anomalies from expected patterns.",
        full_explanation=(
            "Deviation patterns identify when behavior deviates from established baselines or "
            "norms. Deviations can indicate: bugs, new features, changing requirements, or "
            "novel situations. Recognizing deviations helps catch issues early and adapt to change."
        ),
        when_applies=(
            "Deviation applies when you notice unexpected behavior, test failures, performance "
            "changes, or when established patterns break. It's particularly important for "
            "detecting bugs and regressions."
        ),
        what_to_do=(
            "Investigate deviations: determine if they represent bugs, features, or expected "
            "changes. Update baselines if the deviation is intentional, or fix issues if it's "
            "a problem."
        ),
        benefits=[
            "Early detection of bugs and regressions",
            "Faster adaptation to changing requirements",
            "Improved monitoring and observability",
            "Better understanding of normal vs. abnormal behavior",
        ],
    ),
    "cause": PatternExplanation(
        pattern_name="Cause",
        short_description="This identifies causal relationships between events and outcomes.",
        full_explanation=(
            "Cause patterns reveal how events lead to other events. Understanding causality "
            "helps you: predict future behavior, identify root causes of problems, and make "
            "effective interventions. Strong causal patterns indicate predictable, "
            "understandable system behavior."
        ),
        when_applies=(
            "Cause patterns apply when you're debugging, investigating system behavior, or "
            "trying to understand how changes affect outcomes. They're essential for root "
            "cause analysis and impact assessment."
        ),
        what_to_do=(
            "Use causal understanding: map causal chains, identify intervention points, and "
            "predict the effects of changes. When debugging, work backwards from symptoms "
            "to root causes."
        ),
        benefits=[
            "More effective debugging and problem-solving",
            "Better prediction of system behavior",
            "Improved impact assessment for changes",
            "Enhanced ability to prevent problems before they occur",
        ],
    ),
    "time": PatternExplanation(
        pattern_name="Time",
        short_description="This analyzes temporal evolution, trends, and seasonal patterns.",
        full_explanation=(
            "Time patterns reveal how behavior changes over time. They include: trends "
            "(increasing/decreasing), volatility (consistency), seasonality (repeating cycles), "
            "and growth/decay patterns. Understanding time patterns helps with forecasting "
            "and long-term planning."
        ),
        when_applies=(
            "Time patterns apply when analyzing system performance over time, tracking "
            "metrics and KPIs, understanding user behavior evolution, or planning for "
            "growth and capacity needs."
        ),
        what_to_do=(
            "Track time-based metrics: monitor trends, understand seasonal patterns, and "
            "use historical data for forecasting. Plan for both growth and potential "
            "decline scenarios."
        ),
        benefits=[
            "Better long-term planning and forecasting",
            "Earlier detection of performance degradation",
            "Understanding of seasonal patterns and cycles",
            "Improved capacity planning and resource allocation",
        ],
    ),
    "combination": PatternExplanation(
        pattern_name="Combination",
        short_description="This composes multiple patterns into higher-level, emergent insights.",
        full_explanation=(
            "Combination patterns emerge when multiple cognition patterns interact. These "
            "composite patterns reveal emergent behavior that's not apparent from any "
            "single pattern alone. For example, flow + rhythm might indicate 'productive "
            "groove', while deviation + cause might indicate 'investigation needed'."
        ),
        when_applies=(
            "Combination patterns apply when multiple patterns are active simultaneously, "
            "revealing complex, multi-faceted situations that require holistic understanding."
        ),
        what_to_do=(
            "Look for emergent patterns: consider how different patterns interact, and use "
            "combination insights for more nuanced understanding and decision-making."
        ),
        benefits=[
            "More nuanced understanding of complex situations",
            "Ability to see emergent behavior and properties",
            "Better contextual awareness",
            "More sophisticated decision-making",
        ],
    ),
}


# Composite pattern explanations (when multiple patterns combine)
COMPOSITE_EXPLANATIONS: dict[tuple[str, ...], PatternExplanation] = {
    ("flow", "rhythm"): PatternExplanation(
        pattern_name="Flow + Rhythm",
        short_description="Productive Groove",
        full_explanation=(
            "You're in a productive groove - deep flow with consistent timing. This is an "
            "optimal state for sustained productivity. Your cognitive load is balanced, "
            "you're fully engaged, and your work has a predictable, steady rhythm."
        ),
        when_applies="When you're deeply focused and working with consistent timing.",
        what_to_do="Protect this state - minimize interruptions and maintain the rhythm.",
        benefits=["Maximum sustained productivity", "High quality output", "Enjoyable work experience"],
    ),
    ("deviation", "cause"): PatternExplanation(
        pattern_name="Deviation + Cause",
        short_description="Investigation Mode",
        full_explanation=(
            "Something has deviated from expected behavior, and causal relationships are "
            "implicated. This signals that investigation is needed. You may need to debug, "
            "analyze root causes, or understand system changes."
        ),
        when_applies="When unexpected behavior occurs with potential causal factors.",
        what_to_do="Investigate systematically: identify the deviation, trace causal chains, and determine appropriate action.",
        benefits=["Systematic problem-solving", "Root cause identification", "Effective remediation"],
    ),
    ("repetition", "cause"): PatternExplanation(
        pattern_name="Repetition + Cause",
        short_description="Systematic Issue",
        full_explanation=(
            "Repetitive patterns with clear causal relationships suggest a systematic issue "
            "that needs structural attention. This isn't just a one-off problem - it's a "
            "pattern that's being caused by something specific and recurring."
        ),
        when_applies="When the same issue recurs due to identifiable causes.",
        what_to_do="Address the root cause systematically: fix the underlying issue, not just the symptoms.",
        benefits=["Permanent problem resolution", "Reduced future incidents", "System improvement"],
    ),
    ("flow", "deviation"): PatternExplanation(
        pattern_name="Flow + Deviation",
        short_description="Flow Disruption",
        full_explanation=(
            "You were in flow but something has deviated from expected patterns, potentially "
            "disrupting your productive state. This could be: a bug you hit, unexpected "
            "system behavior, or an interruption that broke your concentration."
        ),
        when_applies="When flow is interrupted by unexpected deviations.",
        what_to_do="Quickly assess and address the deviation, then work to restore flow. Minimize time spent in disrupted state.",
        benefits=[
            "Faster return to productivity",
            "Reduced flow disruption impact",
            "Better resilience to interruptions",
        ],
    ),
    ("spatial", "cause"): PatternExplanation(
        pattern_name="Spatial + Cause",
        short_description="Structural Understanding",
        full_explanation=(
            "You're working with spatial information structures and have identified causal "
            "relationships within those structures. This indicates deep architectural "
            "understanding - you see both how things are organized AND how they affect each other."
        ),
        when_applies="When analyzing complex architectures with clear causal relationships.",
        what_to_do="Leverage this understanding: use it for architecture decisions, impact analysis, and system design.",
        benefits=["Informed architecture decisions", "Accurate impact analysis", "Better system design"],
    ),
}


def get_pattern_explanation(pattern_name: str) -> PatternExplanation | None:
    """Get explanation for a specific pattern.

    Args:
        pattern_name: Name of the pattern

    Returns:
        PatternExplanation if found, None otherwise
    """
    return PATTERN_EXPLANATIONS.get(pattern_name)


def get_all_explanations() -> dict[str, PatternExplanation]:
    """Get all pattern explanations.

    Returns:
        Dictionary of pattern names to explanations
    """
    return PATTERN_EXPLANATIONS.copy()


def get_composite_explanation(patterns: tuple[str, ...]) -> PatternExplanation | None:
    """Get explanation for a composite pattern combination.

    Args:
        patterns: Tuple of pattern names

    Returns:
        PatternExplanation if composite found, None otherwise
    """
    # Try exact match
    if patterns in COMPOSITE_EXPLANATIONS:
        return COMPOSITE_EXPLANATIONS[patterns]

    # Try sorted match (order doesn't matter)
    sorted_patterns = tuple(sorted(patterns))
    if sorted_patterns in COMPOSITE_EXPLANATIONS:
        return COMPOSITE_EXPLANATIONS[sorted_patterns]

    return None


def generate_pattern_summary(
    detections: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Generate a human-readable summary of pattern detections.

    Args:
        detections: Dictionary of pattern name -> detection result

    Returns:
        Summary dictionary with human-readable text
    """
    detected = [name for name, det in detections.items() if det.get("detected", False)]
    high_confidence = [name for name, det in detections.items() if det.get("confidence", 0) > 0.7]

    # Build summary
    summary_parts = []

    if not detected:
        summary_parts.append("No significant patterns detected at this time.")
    else:
        if len(detected) == 1:
            summary_parts.append(f"One pattern detected: {detected[0]}")
        else:
            summary_parts.append(f"{len(detected)} patterns detected: {', '.join(detected)}")

        # Add high confidence patterns
        if high_confidence:
            if len(high_confidence) == 1:
                summary_parts.append(f"Strong signal: {high_confidence[0]}")
            else:
                summary_parts.append(f"Strong signals: {', '.join(high_confidence)}")

    # Add specific explanations
    explanations = []
    for pattern in detected:
        explanation = get_pattern_explanation(pattern)
        if explanation:
            explanations.append(
                {
                    "pattern": pattern,
                    "short": explanation.short_description,
                    "what_to_do": explanation.what_to_do,
                }
            )

    # Check for composite patterns
    if len(detected) >= 2:
        composite = get_composite_explanation(tuple(detected))
        if composite:
            summary_parts.append(f"Composite insight: {composite.short_description}")

    return {
        "summary": " ".join(summary_parts),
        "detected_patterns": detected,
        "high_confidence_patterns": high_confidence,
        "pattern_explanations": explanations,
        "composite_insight": composite.short_description
        if (len(detected) >= 2 and (composite := get_composite_explanation(tuple(detected))))
        else None,
    }


def format_explanation_for_user(
    pattern_name: str,
    detail_level: str = "medium",
) -> str:
    """Format a pattern explanation for user display.

    Args:
        pattern_name: Name of the pattern
        detail_level: Level of detail (brief, medium, full)

    Returns:
        Formatted explanation string
    """
    explanation = get_pattern_explanation(pattern_name)
    if not explanation:
        return f"Pattern '{pattern_name}' not found."

    if detail_level == "brief":
        return explanation.short_description
    elif detail_level == "full":
        lines = [
            f"## {explanation.pattern_name}",
            explanation.short_description,
            "",
            "**Full Explanation:**",
            explanation.full_explanation,
            "",
            "**When This Applies:**",
            explanation.when_applies,
            "",
            "**What To Do:**",
            explanation.what_to_do,
            "",
            "**Benefits:**",
            *[f"- {b}" for b in explanation.benefits],
        ]
        return "\n".join(lines)
    else:  # medium
        lines = [
            f"**{explanation.pattern_name}:** {explanation.short_description}",
            "",
            explanation.when_applies,
            "",
            f"**Action:** {explanation.what_to_do}",
        ]
        return "\n".join(lines)


def get_pattern_recommendations(
    pattern_name: str,
    context: dict[str, Any] | None = None,
) -> list[str]:
    """Get actionable recommendations for a pattern.

    Args:
        pattern_name: Name of the pattern
        context: Optional context for contextual recommendations

    Returns:
        List of recommendation strings
    """
    explanation = get_pattern_explanation(pattern_name)
    if not explanation:
        return []

    recommendations = [explanation.what_to_do]

    # Add context-specific recommendations
    if context:
        if pattern_name == "flow" and context.get("cognitive_load", 0) > 7:
            recommendations.append("High load detected - consider taking a break to preserve long-term productivity.")

        elif pattern_name == "repetition" and context.get("automation_opportunity", False):
            recommendations.append("Strong automation opportunity detected - consider creating a reusable component.")

        elif pattern_name == "deviation" and context.get("critical", False):
            recommendations.append("CRITICAL: Address this deviation immediately to prevent further issues.")

    return recommendations


def explain_resonance_with_patterns(
    resonance_score: float,
    detected_patterns: list[str],
) -> str:
    """Explain a resonance score in the context of detected patterns.

    Args:
        resonance_score: Resonance score (0-1)
        detected_patterns: List of detected pattern names

    Returns:
        Human-readable explanation
    """
    if resonance_score > 0.9:
        base = "Excellent resonance - strong alignment detected across multiple patterns."
    elif resonance_score > 0.7:
        base = "Good resonance - most patterns are aligned and consistent."
    elif resonance_score > 0.5:
        base = "Moderate resonance - some patterns show alignment."
    else:
        base = "Low resonance - patterns show inconsistency or misalignment."

    if not detected_patterns:
        return f"{base} No specific patterns were detected."

    # Add pattern-specific context
    pattern_descriptions = []
    for pattern in detected_patterns[:3]:  # Limit to top 3
        explanation = get_pattern_explanation(pattern)
        if explanation:
            pattern_descriptions.append(explanation.short_description)

    if pattern_descriptions:
        return f"{base} Detected: {', '.join(pattern_descriptions)}"

    return f"{base} Patterns: {', '.join(detected_patterns)}"
