"""AI Safety Thresholds Skill.

Dynamic threshold calculation and violation detection.
"""

from __future__ import annotations

import logging
import statistics
from typing import Any

from grid.skills.base import SimpleSkill

from .base import SafetyCategory, SafetyViolation, ThreatLevel
from .config import get_config

logger = logging.getLogger(__name__)


def calculate_baseline(values: list[float], method: str = "mean") -> float:
    """Calculate baseline value from historical data.

    Args:
        values: List of historical values.
        method: Baseline method (mean, median, percentile_90).

    Returns:
        Baseline value.
    """
    if not values:
        return 0.0

    if method == "mean":
        return statistics.mean(values)
    elif method == "median":
        return statistics.median(values)
    elif method == "percentile_90":
        sorted_values = sorted(values)
        index = int(len(sorted_values) * 0.9)
        return sorted_values[min(index, len(sorted_values) - 1)]
    else:
        return statistics.mean(values)


def calculate_threshold(
    baseline: float,
    sensitivity: str,
    direction: str = "above",
) -> float:
    """Calculate threshold based on sensitivity.

    Args:
        baseline: Baseline value.
        sensitivity: Sensitivity level (low, medium, high).
        direction: Direction (above or below baseline).

    Returns:
        Threshold value.
    """
    sensitivity_multipliers = {
        "low": 2.0,  # 2 standard deviations
        "medium": 1.5,  # 1.5 standard deviations
        "high": 1.0,  # 1 standard deviation
    }

    multiplier = sensitivity_multipliers.get(sensitivity, 1.5)

    if direction == "above":
        return baseline * (1 + multiplier * 0.1)
    else:
        return baseline * (1 - multiplier * 0.1)


def check_threshold_violation(
    value: float,
    threshold: float,
    direction: str = "above",
) -> bool:
    """Check if value violates threshold.

    Args:
        value: Current value.
        threshold: Threshold value.
        direction: Direction (above or below).

    Returns:
        True if violation detected.
    """
    if direction == "above":
        return value > threshold
    else:
        return value < threshold


def get_severity_from_deviation(
    value: float,
    baseline: float,
    threshold: float,
) -> ThreatLevel:
    """Determine severity based on deviation from threshold.

    Args:
        value: Current value.
        baseline: Baseline value.
        threshold: Threshold value.

    Returns:
        Threat level based on severity.
    """
    if baseline == 0:
        deviation = abs(value)
    else:
        deviation = abs(value - baseline) / baseline

    if deviation >= 0.5:
        return ThreatLevel.CRITICAL
    elif deviation >= 0.3:
        return ThreatLevel.HIGH
    elif deviation >= 0.2:
        return ThreatLevel.MEDIUM
    elif deviation >= 0.1:
        return ThreatLevel.LOW
    else:
        return ThreatLevel.NONE


def thresholds_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle threshold-based violation detection.

    Args:
        args: Dictionary containing:
            - metrics: dict of metric_name -> current_value, required
            - baseline: dict of metric_name -> baseline_value, optional
            - sensitivity: str (low/medium/high), default "medium"
            - historical_data: dict of metric_name -> list of values, optional

    Returns:
        Dictionary with threshold violations.
    """
    metrics = args.get("metrics", {})
    if not metrics:
        return {
            "success": True,
            "violations": [],
            "violation_count": 0,
            "message": "No metrics provided",
        }

    baseline = args.get("baseline", {})
    sensitivity = args.get("sensitivity", "medium")
    historical_data = args.get("historical_data", {})

    config = get_config()
    violations = []

    for metric_name, current_value in metrics.items():
        try:
            # Get or calculate baseline
            if metric_name in baseline:
                metric_baseline = baseline[metric_name]
            elif metric_name in historical_data:
                metric_baseline = calculate_baseline(historical_data[metric_name])
            else:
                # Use current value as baseline if no history
                metric_baseline = current_value
                logger.debug(f"No baseline for {metric_name}, using current value")

            # Calculate threshold
            threshold = calculate_threshold(metric_baseline, sensitivity)

            # Check for violation
            direction = "above" if current_value > metric_baseline else "below"

            if check_threshold_violation(current_value, threshold, direction):
                severity = get_severity_from_deviation(current_value, metric_baseline, threshold)

                if severity != ThreatLevel.NONE:
                    violation = SafetyViolation(
                        category=SafetyCategory.BEHAVIORAL_ANOMALY,
                        severity=severity,
                        confidence=0.8,
                        description=f"Threshold violation for {metric_name}",
                        evidence={
                            "metric": metric_name,
                            "current_value": current_value,
                            "baseline": metric_baseline,
                            "threshold": threshold,
                            "direction": direction,
                            "deviation": abs(current_value - metric_baseline),
                        },
                        provider="ai_safety_thresholds",
                    )
                    violations.append(violation)
                    logger.debug(f"Threshold violation for {metric_name}: {current_value}")

        except Exception as e:
            logger.error(f"Error checking threshold for {metric_name}: {e}")
            continue

    return {
        "success": True,
        "violations": [v.to_dict() for v in violations],
        "violation_count": len(violations),
        "metrics_evaluated": len(metrics),
        "sensitivity": sensitivity,
        "thresholds_used": config.safety_thresholds,
    }


# Skill instance
ai_safety_thresholds = SimpleSkill(
    id="ai_safety_thresholds",
    name="AI Safety Thresholds",
    description="Dynamic threshold calculation and violation detection",
    handler=thresholds_handler,
    version="1.0.0",
)
