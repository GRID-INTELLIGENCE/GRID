"""
Precision Validation for Parasite Guard.

Provides statistical validation tools:
- Sample size calculation for significance testing
- Confidence interval comparison
- Hypothesis testing for performance validation
- Effect size calculations

These tools ensure detection precision meets statistical requirements.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceInterval:
    """A confidence interval result.

    Attributes:
        lower: Lower bound of the interval.
        upper: Upper bound of the interval.
        point_estimate: Point estimate (usually mean).
        confidence_level: Confidence level (e.g., 0.95 for 95%).
    """

    lower: float
    upper: float
    point_estimate: float
    confidence_level: float = 0.95

    @property
    def width(self) -> float:
        """Width of the confidence interval."""
        return self.upper - self.lower

    @property
    def margin_of_error(self) -> float:
        """Margin of error (half-width)."""
        return self.width / 2

    def contains(self, value: float) -> bool:
        """Check if the interval contains a value."""
        return self.lower <= value <= self.upper

    def overlaps(self, other: ConfidenceInterval) -> bool:
        """Check if this interval overlaps with another."""
        return not (self.upper < other.lower or other.upper < self.lower)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "lower": self.lower,
            "upper": self.upper,
            "point_estimate": self.point_estimate,
            "confidence_level": self.confidence_level,
            "width": self.width,
            "margin_of_error": self.margin_of_error,
        }


@dataclass
class HypothesisTestResult:
    """Result of a hypothesis test.

    Attributes:
        statistic: Test statistic (e.g., t-statistic).
        p_value: P-value for the test.
        significant: Whether the result is statistically significant.
        effect_size: Effect size (e.g., Cohen's d).
        alpha: Significance level used.
        test_type: Type of test performed.
    """

    statistic: float
    p_value: float
    significant: bool
    effect_size: float = 0.0
    alpha: float = 0.05
    test_type: str = "t-test"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "statistic": self.statistic,
            "p_value": self.p_value,
            "significant": self.significant,
            "effect_size": self.effect_size,
            "alpha": self.alpha,
            "test_type": self.test_type,
        }


@dataclass
class ValidationReport:
    """Report from precision validation.

    Attributes:
        is_valid: Whether validation passed.
        precision: Precision metric.
        recall: Recall metric.
        f1_score: F1 score.
        confidence_intervals: Confidence intervals for metrics.
        hypothesis_tests: Results of hypothesis tests.
        recommendations: Recommendations for improvement.
    """

    is_valid: bool = True
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    confidence_intervals: dict[str, ConfidenceInterval] = field(default_factory=dict)
    hypothesis_tests: dict[str, HypothesisTestResult] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "is_valid": self.is_valid,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "confidence_intervals": {k: v.to_dict() for k, v in self.confidence_intervals.items()},
            "hypothesis_tests": {k: v.to_dict() for k, v in self.hypothesis_tests.items()},
            "recommendations": self.recommendations,
        }


class PrecisionValidator:
    """Validates detection precision with statistical rigor.

    Provides methods for:
    - Sample size calculation
    - Confidence interval estimation
    - Hypothesis testing
    - Effect size calculation
    """

    def __init__(
        self,
        target_precision: float = 0.985,
        target_recall: float = 0.985,
        alpha: float = 0.05,
        power: float = 0.8,
    ):
        """Initialize the validator.

        Args:
            target_precision: Target precision (e.g., 0.985 for 98.5%).
            target_recall: Target recall.
            alpha: Significance level for hypothesis tests.
            power: Statistical power for sample size calculations.
        """
        self.target_precision = target_precision
        self.target_recall = target_recall
        self.alpha = alpha
        self.power = power

    def _t_critical(self, df: int, alpha: float) -> float:
        """Approximate t-critical value using normal approximation.

        For large df, t approaches normal distribution.
        For small df, this is an approximation.
        """
        # Use normal approximation for simplicity
        # z-value for common alpha levels
        z_values = {
            0.01: 2.576,
            0.025: 1.96,
            0.05: 1.645,
            0.10: 1.282,
        }

        # For two-tailed test, use alpha/2
        if alpha / 2 in z_values:
            z = z_values[alpha / 2]
        elif alpha in z_values:
            z = z_values[alpha]
        else:
            # Default to 1.96 (95% CI)
            z = 1.96

        # Adjust for small sample sizes
        if df < 30:
            z *= 1 + 1 / (4 * df)

        return z

    def calculate_required_sample_size(
        self,
        effect_size: float = 0.5,
        power: float | None = None,
        alpha: float | None = None,
    ) -> int:
        """Calculate required sample size for statistical significance.

        Uses the formula for two-sample t-test:
        n = 2 * ((z_alpha + z_power) / d)^2

        Args:
            effect_size: Expected effect size (Cohen's d).
            power: Desired statistical power (default: self.power).
            alpha: Significance level (default: self.alpha).

        Returns:
            Required sample size per group.
        """
        power = power or self.power
        alpha = alpha or self.alpha

        # Z-values for power and alpha
        z_alpha = self._t_critical(100, alpha)  # Two-tailed
        z_power = self._t_critical(100, 1 - power)

        # Sample size formula
        n = 2 * ((z_alpha + z_power) / effect_size) ** 2

        return int(math.ceil(n))

    def calculate_confidence_interval(
        self,
        data: list[float],
        confidence: float = 0.95,
    ) -> ConfidenceInterval:
        """Calculate confidence interval for data.

        Args:
            data: List of data points.
            confidence: Confidence level (e.g., 0.95).

        Returns:
            ConfidenceInterval for the data.
        """
        if len(data) < 2:
            return ConfidenceInterval(
                lower=data[0] if data else 0,
                upper=data[0] if data else 0,
                point_estimate=data[0] if data else 0,
                confidence_level=confidence,
            )

        n = len(data)
        mean = sum(data) / n
        variance = sum((x - mean) ** 2 for x in data) / (n - 1)
        std_error = math.sqrt(variance / n)

        # t-critical value
        df = n - 1
        alpha = 1 - confidence
        t_crit = self._t_critical(df, alpha / 2)

        margin = t_crit * std_error

        return ConfidenceInterval(
            lower=mean - margin,
            upper=mean + margin,
            point_estimate=mean,
            confidence_level=confidence,
        )

    def compare_confidence_intervals(
        self,
        data_a: list[float],
        data_b: list[float],
        confidence: float = 0.95,
    ) -> dict[str, Any]:
        """Compare two datasets using confidence intervals.

        Args:
            data_a: First dataset.
            data_b: Second dataset.
            confidence: Confidence level.

        Returns:
            Dictionary with comparison results.
        """
        ci_a = self.calculate_confidence_interval(data_a, confidence)
        ci_b = self.calculate_confidence_interval(data_b, confidence)

        overlap = max(0, min(ci_a.upper, ci_b.upper) - max(ci_a.lower, ci_b.lower))

        # Calculate effect size
        mean_a = sum(data_a) / len(data_a) if data_a else 0
        mean_b = sum(data_b) / len(data_b) if data_b else 0

        var_a = sum((x - mean_a) ** 2 for x in data_a) / (len(data_a) - 1) if len(data_a) > 1 else 1
        var_b = sum((x - mean_b) ** 2 for x in data_b) / (len(data_b) - 1) if len(data_b) > 1 else 1

        pooled_std = math.sqrt((var_a + var_b) / 2)
        effect_size = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0

        # Significant if CIs don't overlap
        significant = not ci_a.overlaps(ci_b)

        return {
            "ci_a": ci_a,
            "ci_b": ci_b,
            "overlap": overlap,
            "significant": significant,
            "effect_size": effect_size,
        }

    def perform_t_test(
        self,
        data_a: list[float],
        data_b: list[float],
        alpha: float | None = None,
    ) -> HypothesisTestResult:
        """Perform a two-sample t-test.

        Uses Welch's t-test (unequal variances assumed).

        Args:
            data_a: First dataset.
            data_b: Second dataset.
            alpha: Significance level.

        Returns:
            HypothesisTestResult with test results.
        """
        alpha = alpha or self.alpha

        if len(data_a) < 2 or len(data_b) < 2:
            return HypothesisTestResult(
                statistic=0,
                p_value=1.0,
                significant=False,
                alpha=alpha,
            )

        # Calculate statistics
        n_a, n_b = len(data_a), len(data_b)
        mean_a = sum(data_a) / n_a
        mean_b = sum(data_b) / n_b

        var_a = sum((x - mean_a) ** 2 for x in data_a) / (n_a - 1)
        var_b = sum((x - mean_b) ** 2 for x in data_b) / (n_b - 1)

        # Welch's t-test
        se = math.sqrt(var_a / n_a + var_b / n_b)
        if se < 1e-9:
            se = 1e-9

        t_stat = (mean_a - mean_b) / se

        # Welch-Satterthwaite degrees of freedom
        num = (var_a / n_a + var_b / n_b) ** 2
        denom = (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
        df = num / denom if denom > 0 else 1

        # Approximate p-value using normal distribution
        # For a more accurate p-value, we'd need scipy
        p_value = 2 * (1 - self._normal_cdf(abs(t_stat)))

        # Effect size (Cohen's d)
        pooled_std = math.sqrt((var_a + var_b) / 2)
        effect_size = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0

        return HypothesisTestResult(
            statistic=t_stat,
            p_value=p_value,
            significant=p_value < alpha,
            effect_size=effect_size,
            alpha=alpha,
            test_type="welch-t-test",
        )

    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF."""
        t = 1.0 / (1.0 + 0.2316419 * abs(x))
        d = 0.3989422804014327  # 1/sqrt(2*pi)
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        cdf = 1.0 - d * math.exp(-0.5 * x * x) * poly
        return cdf if x >= 0 else 1.0 - cdf

    def validate_detection_precision(
        self,
        true_positives: int,
        false_positives: int,
        true_negatives: int,
        false_negatives: int,
        confidence: float = 0.95,
    ) -> ValidationReport:
        """Validate detection precision against targets.

        Args:
            true_positives: Count of true positives.
            false_positives: Count of false positives.
            true_negatives: Count of true negatives.
            false_negatives: Count of false negatives.
            confidence: Confidence level for intervals.

        Returns:
            ValidationReport with validation results.
        """
        report = ValidationReport()

        # Calculate metrics
        total_positive_predictions = true_positives + false_positives
        total_actual_positives = true_positives + false_negatives
        total = true_positives + false_positives + true_negatives + false_negatives

        report.precision = true_positives / total_positive_predictions if total_positive_predictions > 0 else 0
        report.recall = true_positives / total_actual_positives if total_actual_positives > 0 else 0

        if report.precision + report.recall > 0:
            report.f1_score = 2 * report.precision * report.recall / (report.precision + report.recall)
        else:
            report.f1_score = 0

        # Calculate confidence intervals for precision
        # Using Wilson score interval for proportions
        if total_positive_predictions > 0:
            z = self._t_critical(100, (1 - confidence) / 2)
            p = report.precision
            n = total_positive_predictions

            denom = 1 + z**2 / n
            center = (p + z**2 / (2 * n)) / denom
            margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom

            report.confidence_intervals["precision"] = ConfidenceInterval(
                lower=max(0, center - margin),
                upper=min(1, center + margin),
                point_estimate=report.precision,
                confidence_level=confidence,
            )

        # Check if precision meets target
        precision_ci = report.confidence_intervals.get("precision")
        if precision_ci:
            if precision_ci.lower < self.target_precision:
                report.is_valid = False
                report.recommendations.append(
                    f"Precision lower bound ({precision_ci.lower:.3f}) is below "
                    f"target ({self.target_precision:.3f}). Need more true positives "
                    f"or fewer false positives."
                )

        # Check sample size
        recommended_n = self.calculate_required_sample_size(effect_size=0.3)
        if total < recommended_n:
            report.recommendations.append(
                f"Sample size ({total}) is below recommended minimum ({recommended_n}). "
                f"Results may not be statistically reliable."
            )

        return report

    def validate_performance_degradation(
        self,
        baseline: list[float],
        current: list[float],
        max_degradation_percent: float = 10.0,
    ) -> dict[str, Any]:
        """Check if performance has degraded significantly.

        Args:
            baseline: Baseline metric values.
            current: Current metric values.
            max_degradation_percent: Maximum allowed degradation.

        Returns:
            Dictionary with degradation analysis.
        """
        if not baseline or not current:
            return {"degraded": False, "error": "Insufficient data"}

        baseline_mean = sum(baseline) / len(baseline)
        current_mean = sum(current) / len(current)

        degradation_percent = (current_mean - baseline_mean) / baseline_mean * 100 if baseline_mean > 0 else 0

        # Perform t-test
        test_result = self.perform_t_test(baseline, current)

        degraded = test_result.significant and degradation_percent > max_degradation_percent

        return {
            "degraded": degraded,
            "degradation_percent": degradation_percent,
            "baseline_mean": baseline_mean,
            "current_mean": current_mean,
            "test_result": test_result.to_dict(),
            "max_allowed": max_degradation_percent,
        }


def validate_implementation(
    implementation: Callable[..., Any],
    test_cases: list[dict[str, Any]],
    tolerance: float = 1e-6,
) -> dict[str, Any]:
    """Validate an implementation against test cases.

    Args:
        implementation: Function to test.
        test_cases: List of test cases with "input" and "expected" keys.
        tolerance: Numerical tolerance for floating point comparisons.

    Returns:
        Dictionary with validation results.
    """
    results: dict[str, Any] = {"passed": 0, "failed": 0, "test_cases": []}

    for i, test in enumerate(test_cases):
        try:
            output = implementation(**test["input"])

            if isinstance(test["expected"], (int, float)):
                is_correct = abs(output - test["expected"]) <= tolerance
            else:
                is_correct = output == test["expected"]

            results["test_cases"].append(
                {
                    "test_case": i + 1,
                    "status": "PASS" if is_correct else "FAIL",
                    "expected": test["expected"],
                    "actual": output,
                }
            )

            if is_correct:
                results["passed"] += 1
            else:
                results["failed"] += 1

        except Exception as e:
            results["test_cases"].append(
                {
                    "test_case": i + 1,
                    "status": "ERROR",
                    "error": str(e),
                }
            )
            results["failed"] += 1

    total = results["passed"] + results["failed"]
    results["pass_rate"] = results["passed"] / total if total > 0 else 0

    return results
