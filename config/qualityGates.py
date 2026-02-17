"""
Grid Quality Gates Configuration
Centralized configuration for all quality thresholds and scoring parameters
"""

import json
from pathlib import Path
from typing import Any, cast

# Load configuration
_config_path = Path(__file__).parent / "qualityGates.json"
with open(_config_path) as f:
    _config = json.load(f)


def get_arena_violation_threshold(threshold_type: str) -> int:
    """Get arena violation threshold."""
    thresholds = _config["arena"]["violationThresholds"]
    if threshold_type in thresholds:
        return cast(int, thresholds[threshold_type]["threshold"])
    raise ValueError(f"Unknown threshold type: {threshold_type}")


def get_arena_reputation_threshold(threshold_type: str) -> float:
    """Get arena reputation threshold."""
    thresholds = _config["arena"]["reputationThresholds"]
    if threshold_type in thresholds:
        return thresholds[threshold_type]["threshold"]
    raise ValueError(f"Unknown reputation threshold type: {threshold_type}")


def get_arena_environment_thresholds(environment: str) -> dict[str, Any]:
    """Get environment-specific thresholds."""
    envs = _config["arena"]["environments"]
    if environment in envs:
        return cast(dict[str, Any], envs[environment])
    return cast(dict[str, Any], envs["default"])


def get_inference_threshold(threshold_type: str) -> float:
    """Get inference abrasiveness threshold."""
    thresholds = _config["inferenceAbrasiveness"]["thresholds"]
    if threshold_type in thresholds:
        return cast(float, thresholds[threshold_type]["default"])
    raise ValueError(f"Unknown inference threshold type: {threshold_type}")


def get_optimization_threshold(metric: str, tier: str | None = None) -> float:
    """Get optimization metric threshold."""
    metrics = _config["optimization"]["healthMetrics"]
    if metric in metrics:
        if tier and "tieredScoring" in metrics[metric]:
            return cast(float, metrics[metric]["tieredScoring"].get(tier, metrics[metric].get("threshold", 0.0)))
        return cast(
            float,
            metrics[metric].get(
                "threshold", metrics[metric].get("optimalThreshold", metrics[metric].get("floor", 0.0))
            ),
        )
    raise ValueError(f"Unknown optimization metric: {metric}")


def get_abrasive_extraction_minimum(minimum_type: str) -> int:
    """Get abrasive extraction minimum requirement."""
    minimums = _config["abrasiveExtraction"]["minimums"]
    if minimum_type in minimums:
        return cast(int, minimums[minimum_type]["default"])
    raise ValueError(f"Unknown minimum type: {minimum_type}")


def get_rate_limit(limit_type: str = "default") -> int:
    """Get rate limit configuration."""
    if limit_type == "default":
        return cast(int, _config["rateLimiting"]["default"]["requestsPerMinute"])
    user_types = _config["rateLimiting"]["userTypes"]
    return cast(int, user_types.get(limit_type, user_types["default"]))


# Export configuration
QualityGates = _config
