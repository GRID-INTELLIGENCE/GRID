from typing import Any

from scipy import stats  # type: ignore


def test_performance_degradation(
    baseline_metrics: dict[str, Any],
    current_metrics: dict[str, Any],
    alpha: float = 0.01
) -> dict[str, Any]:
    """Test if performance degradation is statistically significant."""
    t_stat, p_value = stats.ttest_ind_from_stats(
        mean1=baseline_metrics["mean_latency"],
        std1=baseline_metrics["std_latency"],
        nobs1=baseline_metrics["sample_size"],
        mean2=current_metrics["mean_latency"],
        std2=current_metrics["std_latency"],
        nobs2=current_metrics["sample_size"],
        equal_var=False,
    )

    effect_size = (
        (current_metrics["mean_latency"] - baseline_metrics["mean_latency"]) /
        baseline_metrics["std_latency"]
    )

    return {
        "significant": bool(p_value < alpha),
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "degradation_detected": bool(p_value < alpha and effect_size > 0.5),
    }
