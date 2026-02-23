import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pytest

from cognitive.temporal.temporal_reasoning import (
    CrossReferenceDomain,
    TemporalFact,
    TemporalReasoning,
)


@dataclass
class SoftwareDevelopmentMetrics:
    """Metrics collected during software development test execution."""

    execution_time: float
    architecture_confidence: float
    feature_integration_score: float
    code_quality_prediction: float
    development_velocity_estimate: float
    technical_debt_projection: int
    scalability_confidence: float


@dataclass
class PrecalculatedSoftwareResult:
    """Pre-calculated expected results for software development scenarios."""

    scenario: str
    expected_architecture_confidence: float
    expected_feature_integration_score: float
    expected_code_quality_prediction: float
    expected_scalability_confidence: float
    analogy_description: str


class SoftwareDevelopmentTemporalReasoningTestSuite:
    """Comprehensive test suite for temporal reasoning in software development contexts."""

    def __init__(self):
        self.metrics_history: list[SoftwareDevelopmentMetrics] = []
        self.precalculated_results = self._load_precalculated_results()

    def _load_precalculated_results(self) -> list[PrecalculatedSoftwareResult]:
        """Load pre-calculated results for software development scenarios."""
        return [
            PrecalculatedSoftwareResult(
                scenario="Agile sprint planning",
                expected_architecture_confidence=0.82,
                expected_feature_integration_score=0.75,
                expected_code_quality_prediction=0.78,
                expected_scalability_confidence=0.70,
                analogy_description="Like building a house with a flexible blueprint",
            ),
            PrecalculatedSoftwareResult(
                scenario="Legacy system refactoring",
                expected_architecture_confidence=0.65,
                expected_feature_integration_score=0.55,
                expected_code_quality_prediction=0.60,
                expected_scalability_confidence=0.45,
                analogy_description="Like renovating an old building with structural issues",
            ),
            PrecalculatedSoftwareResult(
                scenario="Microservices migration",
                expected_architecture_confidence=0.75,
                expected_feature_integration_score=0.68,
                expected_code_quality_prediction=0.72,
                expected_scalability_confidence=0.85,
                analogy_description="Like reorganizing a large corporation into specialized departments",
            ),
            PrecalculatedSoftwareResult(
                scenario="Real-time system development",
                expected_architecture_confidence=0.90,
                expected_feature_integration_score=0.85,
                expected_code_quality_prediction=0.88,
                expected_scalability_confidence=0.95,
                analogy_description="Like designing a high-performance race car",
            ),
        ]

    @pytest.fixture
    def sample_software_development_facts(self):
        """Generate sample software development temporal facts."""
        base_time = datetime.now()

        return [
            TemporalFact(
                subject="authentication_module",
                predicate="developed",
                object="JWT_implementation",
                timestamp=base_time - timedelta(days=30),
                metadata={
                    "programming_language": "python",
                    "system_architecture": "microservices",
                    "product_feature": "security",
                    "development_stage": "implementation",
                },
            ),
            TemporalFact(
                subject="authentication_module",
                predicate="integrated_with",
                object="user_management_service",
                timestamp=base_time - timedelta(days=25),
                metadata={
                    "programming_language": "python",
                    "system_architecture": "microservices",
                    "product_feature": "user_experience",
                    "development_stage": "integration",
                },
            ),
            TemporalFact(
                subject="authentication_module",
                predicate="tested",
                object="unit_tests_passed",
                timestamp=base_time - timedelta(days=20),
                metadata={
                    "programming_language": "python",
                    "system_architecture": "microservices",
                    "product_feature": "reliability",
                    "development_stage": "testing",
                },
            ),
            TemporalFact(
                subject="payment_service",
                predicate="depends_on",
                object="authentication_module",
                timestamp=base_time - timedelta(days=15),
                metadata={
                    "programming_language": "java",
                    "system_architecture": "microservices",
                    "product_feature": "ecommerce",
                    "development_stage": "design",
                },
            ),
            TemporalFact(
                subject="payment_service",
                predicate="uses_framework",
                object="spring_boot",
                timestamp=base_time - timedelta(days=10),
                metadata={
                    "programming_language": "java",
                    "system_architecture": "microservices",
                    "product_feature": "ecommerce",
                    "development_stage": "implementation",
                },
            ),
            TemporalFact(
                subject="database_layer",
                predicate="migrated_to",
                object="postgresql",
                timestamp=base_time - timedelta(days=5),
                metadata={
                    "programming_language": "sql",
                    "system_architecture": "data_layer",
                    "product_feature": "data_persistence",
                    "development_stage": "migration",
                },
            ),
            TemporalFact(
                subject="api_gateway",
                predicate="configured",
                object="rate_limiting",
                timestamp=base_time - timedelta(hours=12),
                metadata={
                    "programming_language": "go",
                    "system_architecture": "api_management",
                    "product_feature": "scalability",
                    "development_stage": "configuration",
                },
            ),
            TemporalFact(
                subject="monitoring_system",
                predicate="implemented",
                object="prometheus_metrics",
                timestamp=base_time - timedelta(hours=6),
                metadata={
                    "programming_language": "yaml",
                    "system_architecture": "observability",
                    "product_feature": "reliability",
                    "development_stage": "implementation",
                },
            ),
        ]

    @pytest.fixture
    def software_temporal_reasoning_instance(self):
        """Create configured temporal reasoning instance for software development."""
        return TemporalReasoning(
            history_window=timedelta(days=60),  # Software development cycles
            temporal_decay_factor=0.85,  # Slower decay for technical decisions
            cross_reference_threshold=0.65,  # Higher threshold for technical accuracy
            max_path_length=8,  # Allow longer dependency chains
        )

    def test_software_architecture_evolution(
        self, software_temporal_reasoning_instance, sample_software_development_facts
    ):
        """Test how temporal reasoning tracks software architecture evolution."""
        start_time = time.perf_counter()

        for fact in sample_software_development_facts:
            software_temporal_reasoning_instance.add_temporal_fact(fact)

        # Analyze architecture evolution
        paths = software_temporal_reasoning_instance.construct_temporal_paths("authentication_module")

        execution_time = time.perf_counter() - start_time

        assert len(paths) > 0
        assert all(path.validate_temporal_consistency() for path in paths)

        # Architecture confidence based on temporal consistency
        architecture_confidence = software_temporal_reasoning_instance.temporal_consistency_score

        metrics = SoftwareDevelopmentMetrics(
            execution_time=execution_time,
            architecture_confidence=architecture_confidence,
            feature_integration_score=0.0,
            code_quality_prediction=0.0,
            development_velocity_estimate=0.0,
            technical_debt_projection=0,
            scalability_confidence=0.0,
        )
        self.metrics_history.append(metrics)

    def test_feature_integration_analysis(
        self, software_temporal_reasoning_instance, sample_software_development_facts
    ):
        """Test feature integration analysis using temporal reasoning."""
        for fact in sample_software_development_facts:
            software_temporal_reasoning_instance.add_temporal_fact(fact)

        start_time = time.perf_counter()

        # Analyze feature integration across different product areas
        references = software_temporal_reasoning_instance.perform_cross_referencing(
            CrossReferenceDomain.TOPIC,
            CrossReferenceDomain.SUBJECT,  # Programming languages  # System components
        )

        execution_time = time.perf_counter() - start_time

        # Feature integration score based on cross-references
        integration_score = min(1.0, len(references) / 15)  # Normalize

        metrics = SoftwareDevelopmentMetrics(
            execution_time=execution_time,
            architecture_confidence=0.0,
            feature_integration_score=integration_score,
            code_quality_prediction=0.0,
            development_velocity_estimate=0.0,
            technical_debt_projection=0,
            scalability_confidence=0.0,
        )
        self.metrics_history.append(metrics)

    def test_code_quality_prediction(self, software_temporal_reasoning_instance, sample_software_development_facts):
        """Test code quality prediction based on development patterns."""
        for fact in sample_software_development_facts:
            software_temporal_reasoning_instance.add_temporal_fact(fact)

        start_time = time.perf_counter()

        # Predict code quality based on development stages and testing
        testing_facts = [f for f in sample_software_development_facts if "test" in f.predicate.lower()]
        implementation_facts = [f for f in sample_software_development_facts if "implement" in f.predicate.lower()]

        testing_ratio = len(testing_facts) / max(1, len(implementation_facts))
        quality_prediction = min(1.0, testing_ratio * 0.8 + 0.4)  # Base quality + testing bonus

        execution_time = time.perf_counter() - start_time

        metrics = SoftwareDevelopmentMetrics(
            execution_time=execution_time,
            architecture_confidence=0.0,
            feature_integration_score=0.0,
            code_quality_prediction=quality_prediction,
            development_velocity_estimate=0.0,
            technical_debt_projection=0,
            scalability_confidence=0.0,
        )
        self.metrics_history.append(metrics)

    def test_scalability_confidence_assessment(
        self, software_temporal_reasoning_instance, sample_software_development_facts
    ):
        """Test scalability confidence assessment."""
        for fact in sample_software_development_facts:
            software_temporal_reasoning_instance.add_temporal_fact(fact)

        start_time = time.perf_counter()

        # Assess scalability based on architecture choices and features
        scalability_indicators = [
            any(
                "microservices" in f.metadata.get("system_architecture", "") for f in sample_software_development_facts
            ),
            any("rate_limiting" in f.object for f in sample_software_development_facts),
            any("postgresql" in f.object for f in sample_software_development_facts),
            any("prometheus" in f.object for f in sample_software_development_facts),
        ]

        scalability_score = sum(scalability_indicators) / len(scalability_indicators)

        execution_time = time.perf_counter() - start_time

        metrics = SoftwareDevelopmentMetrics(
            execution_time=execution_time,
            architecture_confidence=0.0,
            feature_integration_score=0.0,
            code_quality_prediction=0.0,
            development_velocity_estimate=0.0,
            technical_debt_projection=0,
            scalability_confidence=scalability_score,
        )
        self.metrics_history.append(metrics)

    def test_development_velocity_estimation(
        self, software_temporal_reasoning_instance, sample_software_development_facts
    ):
        """Test development velocity estimation."""
        for fact in sample_software_development_facts:
            software_temporal_reasoning_instance.add_temporal_fact(fact)

        start_time = time.perf_counter()

        # Estimate development velocity based on temporal patterns
        timestamps = sorted([f.timestamp for f in sample_software_development_facts])
        if len(timestamps) > 1:
            time_span = timestamps[-1] - timestamps[0]
            velocity = len(sample_software_development_facts) / max(1, time_span.days)
            velocity_score = min(1.0, velocity / 2.0)  # Normalize
        else:
            velocity_score = 0.5

        execution_time = time.perf_counter() - start_time

        metrics = SoftwareDevelopmentMetrics(
            execution_time=execution_time,
            architecture_confidence=0.0,
            feature_integration_score=0.0,
            code_quality_prediction=0.0,
            development_velocity_estimate=velocity_score,
            technical_debt_projection=0,
            scalability_confidence=0.0,
        )
        self.metrics_history.append(metrics)

    def test_technical_debt_projection(self, software_temporal_reasoning_instance, sample_software_development_facts):
        """Test technical debt projection."""
        for fact in sample_software_development_facts:
            software_temporal_reasoning_instance.add_temporal_fact(fact)

        start_time = time.perf_counter()

        # Project technical debt based on shortcuts and dependencies
        debt_indicators = [
            len([f for f in sample_software_development_facts if "migration" in f.predicate]),  # Migration debt
            len([f for f in sample_software_development_facts if "depends" in f.predicate]),  # Coupling debt
            len(
                {f.metadata.get("programming_language") for f in sample_software_development_facts}
            ),  # Language diversity debt
        ]

        technical_debt = sum(debt_indicators) * 10  # Rough estimation

        execution_time = time.perf_counter() - start_time

        metrics = SoftwareDevelopmentMetrics(
            execution_time=execution_time,
            architecture_confidence=0.0,
            feature_integration_score=0.0,
            code_quality_prediction=0.0,
            development_velocity_estimate=0.0,
            technical_debt_projection=technical_debt,
            scalability_confidence=0.0,
        )
        self.metrics_history.append(metrics)

    def test_comprehensive_software_analysis(
        self, software_temporal_reasoning_instance, sample_software_development_facts
    ):
        """Run comprehensive software development analysis."""
        for fact in sample_software_development_facts:
            software_temporal_reasoning_instance.add_temporal_fact(fact)

        start_time = time.perf_counter()

        # Perform all analyses
        paths = software_temporal_reasoning_instance.construct_temporal_paths("authentication_module")
        references = software_temporal_reasoning_instance.perform_cross_referencing(
            CrossReferenceDomain.TOPIC, CrossReferenceDomain.SUBJECT
        )
        confidence = software_temporal_reasoning_instance.get_decision_confidence("authentication_module")

        execution_time = time.perf_counter() - start_time

        # Calculate comprehensive metrics
        architecture_confidence = software_temporal_reasoning_instance.temporal_consistency_score
        feature_integration_score = min(1.0, len(references) / 20)
        code_quality_prediction = confidence * 0.8  # Correlated with overall confidence
        scalability_confidence = (
            0.75 if any("microservices" in str(f.metadata) for f in sample_software_development_facts) else 0.5
        )
        development_velocity_estimate = len(paths) / max(0.1, execution_time)
        technical_debt_projection = (
            len([f for f in sample_software_development_facts if "migration" in f.predicate]) * 15
        )

        metrics = SoftwareDevelopmentMetrics(
            execution_time=execution_time,
            architecture_confidence=architecture_confidence,
            feature_integration_score=feature_integration_score,
            code_quality_prediction=code_quality_prediction,
            development_velocity_estimate=development_velocity_estimate,
            technical_debt_projection=technical_debt_projection,
            scalability_confidence=scalability_confidence,
        )
        self.metrics_history.append(metrics)

    def create_software_analogy_comparison(self) -> dict[str, Any]:
        """Create analogies comparing software development results with pre-calculated expectations."""
        if not self.metrics_history:
            return {"error": "No software development metrics available"}

        # Use the most recent comprehensive metrics
        latest_metrics = None
        for metrics in reversed(self.metrics_history):
            if metrics.architecture_confidence > 0:  # Comprehensive test
                latest_metrics = metrics
                break

        if not latest_metrics:
            return {"error": "No comprehensive software analysis found"}

        # Find closest matching pre-calculated result
        best_match = None
        best_similarity = 0.0

        for result in self.precalculated_results:
            similarity = self._calculate_software_result_similarity(latest_metrics, result)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = result

        if not best_match:
            return {"error": "No suitable software development analogy found"}

        return {
            "software_scenario": "E-commerce platform development",
            "closest_analogy": best_match.scenario,
            "analogy_description": best_match.analogy_description,
            "similarity_score": best_similarity,
            "software_metrics_comparison": {
                "architecture_confidence": {
                    "actual": latest_metrics.architecture_confidence,
                    "expected": best_match.expected_architecture_confidence,
                    "difference": latest_metrics.architecture_confidence - best_match.expected_architecture_confidence,
                },
                "feature_integration_score": {
                    "actual": latest_metrics.feature_integration_score,
                    "expected": best_match.expected_feature_integration_score,
                    "difference": latest_metrics.feature_integration_score
                    - best_match.expected_feature_integration_score,
                },
                "code_quality_prediction": {
                    "actual": latest_metrics.code_quality_prediction,
                    "expected": best_match.expected_code_quality_prediction,
                    "difference": latest_metrics.code_quality_prediction - best_match.expected_code_quality_prediction,
                },
                "scalability_confidence": {
                    "actual": latest_metrics.scalability_confidence,
                    "expected": best_match.expected_scalability_confidence,
                    "difference": latest_metrics.scalability_confidence - best_match.expected_scalability_confidence,
                },
            },
            "development_insights": {
                "technical_debt_projection": latest_metrics.technical_debt_projection,
                "development_velocity_estimate": latest_metrics.development_velocity_estimate,
                "execution_efficiency": latest_metrics.execution_time,
            },
        }

    def _calculate_software_result_similarity(
        self, metrics: SoftwareDevelopmentMetrics, expected: PrecalculatedSoftwareResult
    ) -> float:
        """Calculate similarity between software metrics and expected results."""
        arch_diff = abs(metrics.architecture_confidence - expected.expected_architecture_confidence)
        integration_diff = abs(metrics.feature_integration_score - expected.expected_feature_integration_score)
        quality_diff = abs(metrics.code_quality_prediction - expected.expected_code_quality_prediction)
        scalability_diff = abs(metrics.scalability_confidence - expected.expected_scalability_confidence)

        # Normalize differences (assuming max difference of 1.0)
        total_diff = (arch_diff + integration_diff + quality_diff + scalability_diff) / 4.0
        similarity = 1.0 - min(total_diff, 1.0)

        return similarity

    def generate_software_development_report(self) -> dict[str, Any]:
        """Generate comprehensive software development analysis report."""
        if not self.metrics_history:
            return {"error": "No software development data available"}

        analogy_comparison = self.create_software_analogy_comparison()

        # Calculate aggregate metrics
        avg_architecture_confidence = float(
            np.mean([m.architecture_confidence for m in self.metrics_history if m.architecture_confidence > 0])
        )
        avg_feature_integration_score = float(
            np.mean([m.feature_integration_score for m in self.metrics_history if m.feature_integration_score > 0])
        )
        avg_code_quality_prediction = float(
            np.mean([m.code_quality_prediction for m in self.metrics_history if m.code_quality_prediction > 0])
        )
        avg_scalability_confidence = float(
            np.mean([m.scalability_confidence for m in self.metrics_history if m.scalability_confidence > 0])
        )
        avg_technical_debt = float(
            np.mean([m.technical_debt_projection for m in self.metrics_history if m.technical_debt_projection > 0])
        )

        # Analyze temporal reasoning impact on software development
        quality_improvement = self._analyze_code_quality_improvement()
        integration_benefit = self._analyze_feature_integration_benefit()

        return {
            "software_analysis_summary": {
                "total_analyses_run": len(self.metrics_history),
                "average_architecture_confidence": avg_architecture_confidence,
                "average_feature_integration_score": avg_feature_integration_score,
                "average_code_quality_prediction": avg_code_quality_prediction,
                "average_scalability_confidence": avg_scalability_confidence,
                "average_technical_debt_projection": avg_technical_debt,
            },
            "temporal_reasoning_software_impact": {
                "code_quality_improvement": quality_improvement,
                "feature_integration_effectiveness": integration_benefit,
                "architecture_consistency_maintenance": avg_architecture_confidence,
                "scalability_prediction_accuracy": avg_scalability_confidence,
            },
            "analogy_comparison": analogy_comparison,
            "software_engineering_insights": {
                "temporal_architecture_awareness": avg_architecture_confidence,
                "cross_component_integration": avg_feature_integration_score,
                "quality_prediction_reliability": (
                    np.std([m.code_quality_prediction for m in self.metrics_history if m.code_quality_prediction > 0])
                    if self.metrics_history
                    else 0.0
                ),
                "scalability_assessment_stability": (
                    np.std([m.scalability_confidence for m in self.metrics_history if m.scalability_confidence > 0])
                    if self.metrics_history
                    else 0.0
                ),
            },
            "development_efficiency_characteristics": {
                "analysis_scalability": self._calculate_software_scalability(),
                "processing_efficiency": float(np.mean([m.execution_time for m in self.metrics_history])),
                "prediction_consistency": self._calculate_prediction_consistency(),
            },
        }

    def _analyze_code_quality_improvement(self) -> float:
        """Analyze how temporal reasoning improves code quality prediction."""
        # Compare quality predictions with and without cross-referencing
        with_integration = [m for m in self.metrics_history if m.feature_integration_score > 0.1]
        without_integration = [m for m in self.metrics_history if m.feature_integration_score <= 0.1]

        if not with_integration or not without_integration:
            return 0.0

        avg_with = float(np.mean([m.code_quality_prediction for m in with_integration]))
        avg_without = float(np.mean([m.code_quality_prediction for m in without_integration]))

        return avg_with - avg_without

    def _analyze_feature_integration_benefit(self) -> dict[str, Any]:
        """Analyze the benefits of feature integration in software development."""
        correlations = []

        for metrics in self.metrics_history:
            if metrics.feature_integration_score > 0 and metrics.code_quality_prediction > 0:
                # Simplified correlation calculation
                correlation = min(1.0, metrics.feature_integration_score * 0.8 + 0.2)
                correlations.append(correlation)

        return {
            "average_integration_correlation": float(np.mean(correlations)) if correlations else 0.0,
            "integration_stability": float(np.std(correlations)) if correlations else 0.0,
            "benefit_confidence": len(correlations) / len(self.metrics_history) if self.metrics_history else 0.0,
        }

    def _calculate_software_scalability(self) -> float:
        """Calculate scalability factor for software development analysis."""
        if len(self.metrics_history) < 2:
            return 1.0

        # Analyze how execution time scales with analysis complexity
        times = [m.execution_time for m in self.metrics_history]
        complexities = [m.technical_debt_projection for m in self.metrics_history]

        if len(set(complexities)) > 1:
            complexity_range = max(complexities) - min(complexities)
            time_range = max(times) - min(times)
            scalability = time_range / complexity_range if complexity_range > 0 else 1.0
            return 1.0 / (1.0 + scalability)
        else:
            return 1.0

    def _calculate_prediction_consistency(self) -> float:
        """Calculate consistency of predictions across different analyses."""
        quality_predictions = [m.code_quality_prediction for m in self.metrics_history if m.code_quality_prediction > 0]
        scalability_predictions = [
            m.scalability_confidence for m in self.metrics_history if m.scalability_confidence > 0
        ]

        if not quality_predictions or not scalability_predictions:
            return 0.0

        quality_std = float(np.std(quality_predictions))
        scalability_std = float(np.std(scalability_predictions))

        # Lower standard deviation = higher consistency
        consistency = 1.0 - min(1.0, (quality_std + scalability_std) / 2.0)
        return consistency


# Convenience function for running the software development test suite
def run_software_development_temporal_reasoning_test_suite() -> dict[str, Any]:
    """Run the complete software development temporal reasoning test suite."""
    suite = SoftwareDevelopmentTemporalReasoningTestSuite()

    # Create test instance
    tr = TemporalReasoning()
    facts = suite.sample_software_development_facts.__wrapped__(suite)  # Get the fixture data

    print("Running software development temporal reasoning tests...")

    for fact in facts:
        tr.add_temporal_fact(fact)

    # Run comprehensive analysis
    suite.test_comprehensive_software_analysis(tr, facts)

    # Generate comprehensive report
    report = suite.generate_software_development_report()

    return report


if __name__ == "__main__":
    # Run the software development test suite when executed directly
    results = run_software_development_temporal_reasoning_test_suite()
    print("\n=== SOFTWARE DEVELOPMENT TEMPORAL REASONING TEST RESULTS ===")
    print(f"Analyses Run: {results['software_analysis_summary']['total_analyses_run']}")
    print(".3f")
    print(".3f")
    print(".3f")
    print(".3f")
    print(".1f")
    print("\nTemporal Reasoning Software Impact:")
    print(".3f")
    print(".3f")
    print(f"\nAnalogy: {results['analogy_comparison']['closest_analogy']}")
    print(f"Description: {results['analogy_comparison']['analogy_description']}")
    print(".3f")
    print("\nKey Insights:")
    print(
        f"- Architecture Consistency: {results['software_engineering_insights']['temporal_architecture_awareness']:.3f}"
    )
    print(f"- Integration Effectiveness: {results['software_engineering_insights']['cross_component_integration']:.3f}")
    print(f"- Analysis Scalability: {results['development_efficiency_characteristics']['analysis_scalability']:.3f}")
    print(
        f"- Prediction Consistency: {results['development_efficiency_characteristics']['prediction_consistency']:.3f}"
    )
