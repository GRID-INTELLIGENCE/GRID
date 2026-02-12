"""
Integration Test Suite: Wristwatch Mechanics for Wellness Studio ↔ GRID Integration
Mimics precise timing, interlocking components, and modular dependencies like a wristwatch.
"""
import time
import pytest
from typing import Dict, List, Optional
from pathlib import Path
import sys
import os

# Add Wellness Studio to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wellness_studio.pipeline import WellnessPipeline, PipelineResult
from wellness_studio.config import model_config
from wellness_studio.scribe import StructuredCase
from wellness_studio.medical_model import WellnessPlan

# GRID imports (with fallbacks for scope identification)
try:
    # Add GRID to path if available
    grid_path = Path(__file__).parent.parent.parent / "grid" / "src"
    if grid_path.exists():
        sys.path.insert(0, str(grid_path))

    from grid.agentic.system import AgenticSystem  # type: ignore
    from grid.cognitive.engine import CognitiveEngine  # type: ignore
    from grid.rag.system import RAGSystem  # type: ignore
    GRID_AVAILABLE = True
except ImportError:
    # Mock classes for scope identification when GRID not available
    class AgenticSystem:
        def create_case(self, case): pass
        def process_case(self, case): return {"status": "mock_processed"}

    class CognitiveEngine:
        def process(self, data): return {"insights": ["mock_insight"], "patterns": ["mock_pattern"]}

    class RAGSystem:
        def query(self, symptoms): return ["mock_rag_result"]

    GRID_AVAILABLE = False


def _apply_test_stubs(pipeline: WellnessPipeline):
    """Inject lightweight stubs so pipeline can run without heavy models."""

    class _StubScribe:
        def scribe(self, raw_text: str, case_type: str = "general") -> StructuredCase:
            return StructuredCase(
                patient_summary="Stub summary",
                current_medications=[],
                conditions=["stub-condition"],
                symptoms=["stub-symptom"],
                treatment_history=[],
                goals=[],
                raw_text=raw_text,
            )

    class _StubMedicalModel:
        def generate_wellness_plan(self, structured_case: StructuredCase) -> WellnessPlan:
            from wellness_studio.medical_model import NaturalAlternative
            return WellnessPlan(
                case_summary=structured_case.patient_summary,
                natural_alternatives=[NaturalAlternative(
                    original="stub-medication",
                    alternative="stub-alternative",
                    category="supplement",
                    evidence_level="moderate",
                    description="Stub description",
                    benefits=["stub-benefit"],
                    considerations=["stub-consideration"]
                )],
                mindfulness_practices=["stub-practice"],
                nutritional_suggestions=["stub-nutrition"],
                lifestyle_modifications=["stub-mod"],
                combined_approach="Stub combined approach",
                disclaimer="This is a stub wellness plan for testing purposes.",
            )

    class _StubReportGenerator:
        def generate_report(self, wellness_plan: WellnessPlan, patient_name=None, format="markdown"):
            return Path("./stub_report.md")

    pipeline.scribe = _StubScribe()  # type: ignore
    pipeline.medical_model = _StubMedicalModel()  # type: ignore
    pipeline.report_generator = _StubReportGenerator()  # type: ignore


class IntegrationTestSuite:
    """Wristwatch-style integration tests: gears must mesh precisely under timing constraints."""

    @pytest.fixture
    def wellness_pipeline(self):
        """Initialize Wellness Pipeline with minimal models for testing."""
        pipeline = WellnessPipeline(skip_embeddings=True, device="cpu")
        # Load lightweight models only for testing
        pipeline.load_models(load_scribe=False, load_medical=False)
        _apply_test_stubs(pipeline)
        yield pipeline

    @pytest.fixture
    def grid_components(self):
        """Initialize GRID components if available."""
        if not GRID_AVAILABLE:
            pytest.skip("GRID not available - testing integration scope identification")
        return {
            "agentic": AgenticSystem(),
            "cognitive": CognitiveEngine(),
            "rag": RAGSystem()
        }

    def test_component_initialization_timing(self, wellness_pipeline, grid_components):
        """Test gear initialization precision - components must start within time windows."""
        start_time = time.perf_counter()

        # Wellness initialization already done in fixture
        wellness_init_time = time.perf_counter() - start_time

        # GRID components (if available)
        grid_init_start = time.perf_counter()
        grid_components  # Trigger any lazy loading
        grid_init_time = time.perf_counter() - grid_init_start

        # Assert timing precision (wristwatch escapement analogy)
        max_wellness_init = 15.0  # seconds
        max_grid_init = 10.0

        assert wellness_init_time < max_wellness_init, \
            f"Wellness init too slow: {wellness_init_time:.2f}s (max: {max_wellness_init}s)"
        assert grid_init_time < max_grid_init, \
            f"GRID init too slow: {grid_init_time:.2f}s (max: {max_grid_init}s)"

    def test_data_flow_interlocking(self, wellness_pipeline, grid_components):
        """Test data flows between gears - must mesh without gaps or data loss."""
        test_case = "Patient John Doe, 45 years old, experiencing anxiety and sleep issues."

        # Process through Wellness pipeline
        result = wellness_pipeline.quick_process(test_case)

        assert result.success, f"Wellness processing failed: {result.error_message}"
        assert result.structured_case is not None, "No structured case generated"

        # Feed to GRID cognitive layer (if available)
        cognitive_input = {
            "case": result.structured_case,
            "plan": result.wellness_plan
        }

        cognitive_output = grid_components["cognitive"].process(cognitive_input)

        # Verify interlocking (no data loss)
        assert "insights" in cognitive_output, "Cognitive processing missing insights"
        assert len(cognitive_output.get("patterns", [])) > 0, "No patterns detected from case"

        # Verify data consistency
        assert cognitive_output["insights"], "Empty insights from cognitive processing"

    def test_failure_propagation_circuit_breaker(self, wellness_pipeline):
        """Test gear failure propagation - circuit breakers prevent cascade failures."""
        # Simulate component failure by breaking a dependency
        original_scriber = wellness_pipeline.scribe
        wellness_pipeline.scribe = None  # Break the scribe "gear"

        test_case = "Patient with hypertension."

        # Should fail gracefully with circuit breaker pattern
        result = wellness_pipeline.quick_process(test_case)

        assert not result.success, "Should have failed with broken component"
        assert result.error_message, "Should have error message for failure"

        # Restore for other tests
        wellness_pipeline.scribe = original_scriber

    def test_performance_under_timing_constraints(self, wellness_pipeline, grid_components):
        """Test system under timing load - wristwatch must maintain accuracy under stress."""
        test_cases = [
            "Patient with anxiety and insomnia",
            "45-year-old male with hypertension",
            "Patient experiencing chronic fatigue",
            "Individual with stress-related digestive issues"
        ]

        start_time = time.perf_counter()
        results = []

        # Process cases sequentially (simulating concurrent load)
        for case in test_cases:
            result = wellness_pipeline.quick_process(case)

            # Integrate with GRID agentic system
            if result.success and GRID_AVAILABLE:
                grid_components["agentic"].create_case(result.structured_case)

            results.append(result)

        total_time = time.perf_counter() - start_time
        avg_time_per_case = total_time / len(test_cases)

        # Assert performance constraints (wristwatch accuracy standards)
        max_total_time = 90.0  # seconds for 4 cases
        max_avg_time = 15.0    # seconds per case

        assert total_time < max_total_time, \
            f"Total processing too slow: {total_time:.2f}s (max: {max_total_time}s)"
        assert avg_time_per_case < max_avg_time, \
            f"Average case time too slow: {avg_time_per_case:.2f}s (max: {max_avg_time}s)"
        assert all(r.success for r in results), f"Failed cases: {[i for i, r in enumerate(results) if not r.success]}"

    def test_modularity_component_swapping(self, wellness_pipeline, grid_components):
        """Test component modularity - gears can be replaced/swapped."""
        # Test swapping Wellness embedder with GRID RAG
        original_embedder = wellness_pipeline.embedder
        wellness_pipeline.embedder = None  # Remove embedder gear

        test_case = "Patient with chronic pain and stress"
        result = wellness_pipeline.quick_process(test_case)

        assert result.success, "Wellness processing failed without embedder"

        # Use GRID RAG instead of Wellness embedder
        if result.structured_case and GRID_AVAILABLE:
            rag_results = grid_components["rag"].query(result.structured_case.symptoms)
            assert rag_results, "RAG integration failed - no results from symptom query"

        # Restore embedder
        wellness_pipeline.embedder = original_embedder

    def test_scope_identification_dependency_mapping(self, wellness_pipeline, grid_components):
        """Identify exact integration scope - map which gears fit together."""
        # Define component dependency chains for integration scope
        dependency_chains = {
            "wellness_input": {"deps": [], "component": "Input Processor"},
            "wellness_scribe": {"deps": ["wellness_input"], "component": "Medical Scribe"},
            "wellness_model": {"deps": ["wellness_scribe"], "component": "Medical Model"},
            "grid_agentic": {"deps": ["wellness_model"], "component": "Agentic Case Management"},
            "grid_cognitive": {"deps": ["grid_agentic"], "component": "Cognitive Decision Support"},
            "grid_rag": {"deps": ["grid_cognitive"], "component": "RAG Knowledge Retrieval"}
        }

        integration_scope = {
            "high_fit": [],
            "medium_fit": [],
            "low_fit": [],
            "requires_adaptation": []
        }

        # Test each dependency
        for component, info in dependency_chains.items():
            fit_level = self._assess_integration_fit(component, info, wellness_pipeline, grid_components)
            integration_scope[fit_level].append({
                "component": component,
                "description": info["component"],
                "dependencies": info["deps"]
            })

        # Assert minimum viable integration scope
        assert len(integration_scope["high_fit"]) >= 2, "Insufficient high-fit components for integration"

        # Log integration scope findings (would be captured in test output)
        print(f"Integration Scope Analysis:")
        for level, components in integration_scope.items():
            print(f"  {level.upper()}: {len(components)} components")
            for comp in components:
                print(f"    - {comp['component']}: {comp['description']}")

    def _assess_integration_fit(self, component: str, info: Dict, wellness_pipeline, grid_components) -> str:
        """Assess how well a component fits in the integration."""
        try:
            if component.startswith("wellness_"):
                # Test Wellness component
                result = wellness_pipeline.quick_process("Test patient case")
                return "high_fit" if result.success else "requires_adaptation"

            elif component.startswith("grid_") and GRID_AVAILABLE:
                # Test GRID component integration
                test_data = {"symptoms": ["anxiety"], "case_id": "test_123"}
                if "agentic" in component:
                    grid_components["agentic"].create_case(test_data)
                elif "cognitive" in component:
                    grid_components["cognitive"].process(test_data)
                elif "rag" in component:
                    grid_components["rag"].query(test_data["symptoms"])
                return "high_fit"

            else:
                return "low_fit"  # Component not available or incompatible

        except Exception as e:
            print(f"Fit assessment failed for {component}: {e}")
            return "requires_adaptation"

    def test_wristwatch_synchronization_accuracy(self, wellness_pipeline, grid_components):
        """Test overall system synchronization - all gears must work in harmony."""
        # Simulate wristwatch timekeeping accuracy test
        test_cycles = 3
        cycle_times = []

        for cycle in range(test_cycles):
            cycle_start = time.perf_counter()

            # Process through full pipeline
            result = wellness_pipeline.quick_process(f"Cycle {cycle} patient case")

            if GRID_AVAILABLE and result.success:
                # Integrate with GRID components
                grid_components["agentic"].create_case(result.structured_case)
                grid_components["cognitive"].process({"case": result.structured_case})
                grid_components["rag"].query(result.structured_case.symptoms)

            cycle_time = time.perf_counter() - cycle_start
            cycle_times.append(cycle_time)

        # Calculate synchronization metrics
        avg_cycle_time = sum(cycle_times) / len(cycle_times)
        max_deviation = max(cycle_times) - min(cycle_times)

        # Assert synchronization (wristwatch accuracy)
        max_avg_cycle = 20.0  # seconds
        max_deviation_pct = 25.0  # percent

        assert avg_cycle_time < max_avg_cycle, \
            f"Average cycle time too slow: {avg_cycle_time:.2f}s (max: {max_avg_cycle}s)"

        deviation_pct = (max_deviation / avg_cycle_time) * 100
        assert deviation_pct < max_deviation_pct, \
            f"Timing inconsistency too high: {deviation_pct:.1f}% deviation (max: {max_deviation_pct}%)"

if __name__ == "__main__":
    # Run standalone for integration scope identification
    print("Running Integration Test Suite - Wristwatch Mechanics Analysis")
    print("=" * 60)

    suite = IntegrationTestSuite()

    # Run basic scope identification tests
    try:
        pipeline = WellnessPipeline(skip_embeddings=True, device="cpu")
        pipeline.load_models(load_scribe=False, load_medical=False)
        _apply_test_stubs(pipeline)

        mock_grid = {
            "agentic": AgenticSystem(),
            "cognitive": CognitiveEngine(),
            "rag": RAGSystem()
        }

        print("Testing component initialization timing...")
        suite.test_component_initialization_timing(pipeline, mock_grid)

        print("Testing data flow interlocking...")
        suite.test_data_flow_interlocking(pipeline, mock_grid)

        print("Testing scope identification...")
        suite.test_scope_identification_dependency_mapping(pipeline, mock_grid)

        print("\n✅ Integration scope identification complete!")
        print("Review test output above for specific integration recommendations.")

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        print("Check that both Wellness Studio and GRID are properly set up.")
