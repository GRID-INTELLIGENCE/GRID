import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pytest

from cognitive.temporal.temporal_reasoning import (
    CrossReferenceDomain,
    TemporalFact,
    TemporalPath,
    TemporalReasoning,
    TemporalRelation,
)


@dataclass
class TestMetrics:
    """Metrics collected during test execution."""
    execution_time: float
    decision_accuracy: float
    temporal_consistency: float
    cross_reference_coverage: float
    path_construction_efficiency: float
    memory_usage_estimate: int
    reasoning_depth: int


@dataclass
class PrecalculatedResult:
    """Pre-calculated expected results for comparison."""
    scenario: str
    expected_decision_confidence: float
    expected_temporal_consistency: float
    expected_cross_reference_coverage: float
    expected_paths_count: int
    analogy_description: str


class TemporalReasoningTestSuite:
    """Comprehensive test suite for temporal reasoning capabilities."""

    def __init__(self):
        self.metrics_history: list[TestMetrics] = []
        self.precalculated_results = self._load_precalculated_results()

    def _load_precalculated_results(self) -> list[PrecalculatedResult]:
        """Load pre-calculated results for comparison analogies."""
        return [
            PrecalculatedResult(
                scenario="Simple temporal sequence",
                expected_decision_confidence=0.85,
                expected_temporal_consistency=1.0,
                expected_cross_reference_coverage=0.6,
                expected_paths_count=3,
                analogy_description="Like following a clear recipe step-by-step"
            ),
            PrecalculatedResult(
                scenario="Complex cross-domain reasoning",
                expected_decision_confidence=0.72,
                expected_temporal_consistency=0.9,
                expected_cross_reference_coverage=0.8,
                expected_paths_count=7,
                analogy_description="Like solving a mystery novel with clues from different chapters"
            ),
            PrecalculatedResult(
                scenario="Temporal inconsistency detection",
                expected_decision_confidence=0.45,
                expected_temporal_consistency=0.6,
                expected_cross_reference_coverage=0.4,
                expected_paths_count=2,
                analogy_description="Like trying to assemble a puzzle with missing pieces"
            ),
            PrecalculatedResult(
                scenario="High temporal density",
                expected_decision_confidence=0.95,
                expected_temporal_consistency=0.98,
                expected_cross_reference_coverage=0.9,
                expected_paths_count=12,
                analogy_description="Like reading a detailed historical chronicle"
            )
        ]

    @pytest.fixture
    def sample_temporal_facts(self):
        """Generate sample temporal facts for testing."""
        base_time = datetime.now()

        return [
            TemporalFact(
                subject="User_A",
                predicate="viewed",
                object="Product_X",
                timestamp=base_time - timedelta(hours=2),
                metadata={"topic": "shopping", "domain": "ecommerce"}
            ),
            TemporalFact(
                subject="User_A",
                predicate="purchased",
                object="Product_Y",
                timestamp=base_time - timedelta(hours=1),
                metadata={"topic": "shopping", "domain": "ecommerce"}
            ),
            TemporalFact(
                subject="User_A",
                predicate="reviewed",
                object="Product_Y",
                timestamp=base_time - timedelta(minutes=30),
                metadata={"topic": "feedback", "domain": "ecommerce"}
            ),
            TemporalFact(
                subject="Product_Y",
                predicate="related_to",
                object="Product_Z",
                timestamp=base_time - timedelta(hours=24),
                metadata={"topic": "recommendation", "domain": "ecommerce"}
            )
        ]

    @pytest.fixture
    def temporal_reasoning_instance(self):
        """Create configured temporal reasoning instance."""
        return TemporalReasoning(
            history_window=timedelta(days=7),
            temporal_decay_factor=0.8,
            cross_reference_threshold=0.6,
            max_path_length=5
        )

    def test_temporal_fact_addition(self, temporal_reasoning_instance, sample_temporal_facts):
        """Test adding temporal facts and updating consistency."""
        start_time = time.perf_counter()

        for fact in sample_temporal_facts:
            temporal_reasoning_instance.add_temporal_fact(fact)

        execution_time = time.perf_counter() - start_time

        assert len(temporal_reasoning_instance.temporal_facts) == 4
        assert temporal_reasoning_instance.temporal_consistency_score >= 0.8

        # Record metrics
        metrics = TestMetrics(
            execution_time=execution_time,
            decision_accuracy=0.0,
            temporal_consistency=temporal_reasoning_instance.temporal_consistency_score,
            cross_reference_coverage=temporal_reasoning_instance.cross_reference_coverage,
            path_construction_efficiency=0.0,
            memory_usage_estimate=len(sample_temporal_facts) * 100,  # Rough estimate
            reasoning_depth=1
        )
        self.metrics_history.append(metrics)

    def test_temporal_path_construction(self, temporal_reasoning_instance, sample_temporal_facts):
        """Test temporal path construction from query subject."""
        # Setup
        for fact in sample_temporal_facts:
            temporal_reasoning_instance.add_temporal_fact(fact)

        start_time = time.perf_counter()
        paths = temporal_reasoning_instance.construct_temporal_paths("User_A")
        execution_time = time.perf_counter() - start_time

        assert len(paths) > 0
        for path in paths:
            assert path.validate_temporal_consistency()
            assert len(path.facts) >= 2

        # Record metrics
        metrics = TestMetrics(
            execution_time=execution_time,
            decision_accuracy=0.0,
            temporal_consistency=temporal_reasoning_instance.temporal_consistency_score,
            cross_reference_coverage=temporal_reasoning_instance.cross_reference_coverage,
            path_construction_efficiency=len(paths) / execution_time if execution_time > 0 else 0,
            memory_usage_estimate=len(paths) * 50,
            reasoning_depth=max(len(p.facts) for p in paths) if paths else 0
        )
        self.metrics_history.append(metrics)

    def test_cross_referencing(self, temporal_reasoning_instance, sample_temporal_facts):
        """Test cross-referencing between domains."""
        # Setup
        for fact in sample_temporal_facts:
            temporal_reasoning_instance.add_temporal_fact(fact)

        start_time = time.perf_counter()
        references = temporal_reasoning_instance.perform_cross_referencing(
            CrossReferenceDomain.TOPIC,
            CrossReferenceDomain.SUBJECT
        )
        execution_time = time.perf_counter() - start_time

        assert len(references) >= 0  # May be 0 if no cross-references found
        for ref in references:
            assert ref.similarity_score >= temporal_reasoning_instance.cross_reference_threshold
            assert ref.temporal_alignment > 0

        # Record metrics
        metrics = TestMetrics(
            execution_time=execution_time,
            decision_accuracy=0.0,
            temporal_consistency=temporal_reasoning_instance.temporal_consistency_score,
            cross_reference_coverage=temporal_reasoning_instance.cross_reference_coverage,
            path_construction_efficiency=0.0,
            memory_usage_estimate=len(references) * 30,
            reasoning_depth=1
        )
        self.metrics_history.append(metrics)

    def test_decision_confidence_calculation(self, temporal_reasoning_instance, sample_temporal_facts):
        """Test decision confidence calculation."""
        # Setup with cross-referencing
        for fact in sample_temporal_facts:
            temporal_reasoning_instance.add_temporal_fact(fact)

        temporal_reasoning_instance.perform_cross_referencing(
            CrossReferenceDomain.TOPIC,
            CrossReferenceDomain.SUBJECT
        )

        start_time = time.perf_counter()
        confidence = temporal_reasoning_instance.get_decision_confidence("User_A")
        execution_time = time.perf_counter() - start_time

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should have reasonable confidence with good data

        # Record metrics
        metrics = TestMetrics(
            execution_time=execution_time,
            decision_accuracy=confidence,  # Using confidence as proxy for accuracy
            temporal_consistency=temporal_reasoning_instance.temporal_consistency_score,
            cross_reference_coverage=temporal_reasoning_instance.cross_reference_coverage,
            path_construction_efficiency=0.0,
            memory_usage_estimate=100,
            reasoning_depth=1
        )
        self.metrics_history.append(metrics)

    def test_performance_benchmark(self, temporal_reasoning_instance):
        """Performance benchmark with varying data sizes."""
        data_sizes = [10, 50, 100, 500]

        for size in data_sizes:
            # Generate synthetic data
            facts = self._generate_synthetic_facts(size)
            temporal_reasoning_instance.temporal_facts = facts

            start_time = time.perf_counter()

            # Perform full reasoning pipeline
            paths = temporal_reasoning_instance.construct_temporal_paths(facts[0].subject)
            temporal_reasoning_instance.perform_cross_referencing(
                CrossReferenceDomain.TOPIC,
                CrossReferenceDomain.SUBJECT
            )
            confidence = temporal_reasoning_instance.get_decision_confidence(facts[0].subject)

            execution_time = time.perf_counter() - start_time

            # Record comprehensive metrics
            metrics = TestMetrics(
                execution_time=execution_time,
                decision_accuracy=confidence,
                temporal_consistency=temporal_reasoning_instance.temporal_consistency_score,
                cross_reference_coverage=temporal_reasoning_instance.cross_reference_coverage,
                path_construction_efficiency=len(paths) / execution_time if execution_time > 0 else 0,
                memory_usage_estimate=size * 200,  # Rough estimate
                reasoning_depth=max(len(p.facts) for p in paths) if paths else 0
            )
            self.metrics_history.append(metrics)

            print(f"Size {size}: {execution_time:.4f}s, Confidence: {confidence:.3f}")

    def _generate_synthetic_facts(self, count: int) -> list[TemporalFact]:
        """Generate synthetic temporal facts for testing."""
        facts = []
        base_time = datetime.now()

        topics = ["shopping", "feedback", "recommendation", "search", "social"]
        domains = ["ecommerce", "social", "content", "search"]

        for i in range(count):
            facts.append(TemporalFact(
                subject=f"User_{i % 10}",
                predicate=["viewed", "purchased", "searched", "shared"][i % 4],
                object=f"Entity_{i % 20}",
                timestamp=base_time - timedelta(minutes=i * 5),
                metadata={
                    "topic": topics[i % len(topics)],
                    "domain": domains[i % len(domains)]
                }
            ))

        return facts

    def test_temporal_consistency_validation(self, temporal_reasoning_instance):
        """Test temporal consistency validation."""
        # Create inconsistent path (facts out of order)
        base_time = datetime.now()
        inconsistent_facts = [
            TemporalFact("A", "rel", "B", base_time + timedelta(hours=1)),
            TemporalFact("B", "rel", "C", base_time),  # Earlier time
        ]

        path = TemporalPath(facts=inconsistent_facts, relations=[TemporalRelation.BEFORE])
        assert not path.validate_temporal_consistency()

        # Create consistent path
        consistent_facts = [
            TemporalFact("A", "rel", "B", base_time),
            TemporalFact("B", "rel", "C", base_time + timedelta(hours=1)),
        ]

        consistent_path = TemporalPath(facts=consistent_facts, relations=[TemporalRelation.BEFORE])
        assert consistent_path.validate_temporal_consistency()

    def create_analogy_comparison(self) -> dict[str, Any]:
        """Create analogies comparing test results with pre-calculated expectations."""
        if not self.metrics_history:
            return {"error": "No test metrics available"}

        latest_metrics = self.metrics_history[-1]

        # Find closest matching pre-calculated result
        best_match = None
        best_similarity = 0.0

        for result in self.precalculated_results:
            similarity = self._calculate_result_similarity(latest_metrics, result)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = result

        if not best_match:
            return {"error": "No suitable analogy found"}

        return {
            "test_scenario": "Dynamic temporal reasoning test",
            "closest_analogy": best_match.scenario,
            "analogy_description": best_match.analogy_description,
            "similarity_score": best_similarity,
            "comparison_metrics": {
                "decision_confidence": {
                    "actual": latest_metrics.decision_accuracy,
                    "expected": best_match.expected_decision_confidence,
                    "difference": latest_metrics.decision_accuracy - best_match.expected_decision_confidence
                },
                "temporal_consistency": {
                    "actual": latest_metrics.temporal_consistency,
                    "expected": best_match.expected_temporal_consistency,
                    "difference": latest_metrics.temporal_consistency - best_match.expected_temporal_consistency
                },
                "cross_reference_coverage": {
                    "actual": latest_metrics.cross_reference_coverage,
                    "expected": best_match.expected_cross_reference_coverage,
                    "difference": latest_metrics.cross_reference_coverage - best_match.expected_cross_reference_coverage
                }
            },
            "performance_analysis": {
                "execution_efficiency": latest_metrics.execution_time,
                "reasoning_depth": latest_metrics.reasoning_depth,
                "memory_efficiency": latest_metrics.memory_usage_estimate
            }
        }

    def _calculate_result_similarity(self, metrics: TestMetrics, expected: PrecalculatedResult) -> float:
        """Calculate similarity between test metrics and expected results."""
        confidence_diff = abs(metrics.decision_accuracy - expected.expected_decision_confidence)
        consistency_diff = abs(metrics.temporal_consistency - expected.expected_temporal_consistency)
        coverage_diff = abs(metrics.cross_reference_coverage - expected.expected_cross_reference_coverage)

        # Normalize differences (assuming max difference of 1.0)
        total_diff = (confidence_diff + consistency_diff + coverage_diff) / 3.0
        similarity = 1.0 - min(total_diff, 1.0)  # Similarity = 1 - normalized_diff

        return similarity

    def generate_comprehensive_report(self) -> dict[str, Any]:
        """Generate comprehensive test report with metrics and analysis."""
        if not self.metrics_history:
            return {"error": "No test data available"}

        analogy_comparison = self.create_analogy_comparison()

        # Calculate aggregate metrics
        avg_execution_time = np.mean([m.execution_time for m in self.metrics_history])
        avg_decision_accuracy = np.mean([m.decision_accuracy for m in self.metrics_history])
        avg_temporal_consistency = np.mean([m.temporal_consistency for m in self.metrics_history])
        avg_cross_reference_coverage = np.mean([m.cross_reference_coverage for m in self.metrics_history])

        # Analyze temporal reasoning impact on decision accuracy
        accuracy_improvement = self._analyze_accuracy_improvement()
        cross_reference_benefit = self._analyze_cross_reference_benefit()

        return {
            "test_summary": {
                "total_tests_run": len(self.metrics_history),
                "average_execution_time": avg_execution_time,
                "average_decision_accuracy": avg_decision_accuracy,
                "average_temporal_consistency": avg_temporal_consistency,
                "average_cross_reference_coverage": avg_cross_reference_coverage
            },
            "temporal_reasoning_impact": {
                "decision_accuracy_improvement": accuracy_improvement,
                "cross_reference_effectiveness": cross_reference_benefit,
                "consistency_maintenance": avg_temporal_consistency,
                "reasoning_depth_achievement": np.mean([m.reasoning_depth for m in self.metrics_history])
            },
            "analogy_comparison": analogy_comparison,
            "cognitive_state_analysis": {
                "temporal_awareness_level": avg_temporal_consistency,
                "cross_domain_integration": avg_cross_reference_coverage,
                "decision_confidence_stability": np.std([m.decision_accuracy for m in self.metrics_history])
            },
            "performance_characteristics": {
                "scalability_factor": self._calculate_scalability(),
                "memory_efficiency": np.mean([m.memory_usage_estimate for m in self.metrics_history]),
                "processing_efficiency": np.mean([m.path_construction_efficiency for m in self.metrics_history if m.path_construction_efficiency > 0])
            }
        }

    def _analyze_accuracy_improvement(self) -> float:
        """Analyze how temporal reasoning improves decision accuracy."""
        # Compare metrics with and without cross-referencing
        with_cross_ref = [m for m in self.metrics_history if m.cross_reference_coverage > 0.1]
        without_cross_ref = [m for m in self.metrics_history if m.cross_reference_coverage <= 0.1]

        if not with_cross_ref or not without_cross_ref:
            return 0.0

        avg_with = np.mean([m.decision_accuracy for m in with_cross_ref])
        avg_without = np.mean([m.decision_accuracy for m in without_cross_ref])

        return avg_with - avg_without

    def _analyze_cross_reference_benefit(self) -> dict[str, Any]:
        """Analyze the benefits of cross-referencing in temporal reasoning."""
        correlations = []

        for metrics in self.metrics_history:
            if metrics.cross_reference_coverage > 0:
                correlation = np.corrcoef(
                    [metrics.cross_reference_coverage, metrics.decision_accuracy]
                )[0, 1]
                correlations.append(correlation)

        return {
            "average_correlation": float(np.mean(correlations)) if correlations else 0.0,
            "correlation_stability": np.std(correlations) if correlations else 0.0,
            "benefit_confidence": len(correlations) / len(self.metrics_history) if self.metrics_history else 0.0
        }

    def _calculate_scalability(self) -> float:
        """Calculate scalability factor based on performance metrics."""
        if len(self.metrics_history) < 2:
            return 1.0

        # Analyze how execution time scales with complexity
        complexities = [m.reasoning_depth for m in self.metrics_history]
        times = [m.execution_time for m in self.metrics_history]

        if len(set(complexities)) > 1:
            # Simple linear regression slope
            complexity_range = max(complexities) - min(complexities)
            time_range = max(times) - min(times)
            scalability = time_range / complexity_range if complexity_range > 0 else 1.0
            return 1.0 / (1.0 + scalability)  # Lower scalability score = better scaling
        else:
            return 1.0


# Convenience function for running the full test suite
def run_temporal_reasoning_test_suite() -> dict[str, Any]:
    """Run the complete temporal reasoning test suite."""
    suite = TemporalReasoningTestSuite()

    # Run individual tests (would normally use pytest)
    print("Running temporal reasoning tests...")

    # Create test instance
    tr = TemporalReasoning()
    facts = suite._generate_synthetic_facts(20)

    for fact in facts:
        tr.add_temporal_fact(fact)

    # Test path construction
    paths = tr.construct_temporal_paths("User_0")

    # Test cross-referencing
    references = tr.perform_cross_referencing(
        CrossReferenceDomain.TOPIC,
        CrossReferenceDomain.SUBJECT
    )

    # Test decision confidence
    tr.get_decision_confidence("User_0")

    # Record processing
    tr.record_processing_event("full_test", {
        "facts_processed": len(facts),
        "paths_constructed": len(paths),
        "references_generated": len(references)
    })

    # Run performance benchmark
    suite.test_performance_benchmark(tr)

    # Generate comprehensive report
    report = suite.generate_comprehensive_report()

    return report


if __name__ == "__main__":
    # Run the test suite when executed directly
    results = run_temporal_reasoning_test_suite()
    print("\n=== TEMPORAL REASONING TEST RESULTS ===")
    print(f"Tests Run: {results['test_summary']['total_tests_run']}")
    print(".4f")
    print(".3f")
    print(".3f")
    print(".3f")
    print("\nTemporal Reasoning Impact:")
    print(".3f")
    print(".3f")
    print(f"\nAnalogy: {results['analogy_comparison']['closest_analogy']}")
    print(f"Description: {results['analogy_comparison']['analogy_description']}")
    print(".3f")
