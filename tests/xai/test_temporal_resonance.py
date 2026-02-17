import pytest

from grid.xai.explainer import XAIExplainer


class TestXAITemporalResonance:
    @pytest.fixture
    def explainer(self, tmp_path):
        # Use a temporary directory for traces
        return XAIExplainer(trace_dir=tmp_path / "xai_traces")

    def test_explain_temporal_resonance(self, explainer):
        explanation = explainer.explain_temporal_resonance(resonance_score=0.9, q_factor=0.2, distance=0.05, decay=0.9)
        assert "strong resonance peak" in explanation
        assert "narrow (high specificity)" in explanation
        assert "near-perfect alignment" in explanation

    def test_generate_coffee_metaphor_narrative_espresso(self, explainer):
        narrative = explainer.generate_coffee_metaphor_narrative(
            cognitive_load=2.0, processing_mode="system_1", momentum="high"
        )
        assert "Espresso mode" in narrative
        assert "rapid fire processing" in narrative
        assert "High momentum" in narrative

    def test_generate_coffee_metaphor_narrative_cold_brew(self, explainer):
        narrative = explainer.generate_coffee_metaphor_narrative(
            cognitive_load=8.0, processing_mode="system_2", momentum="low"
        )
        assert "Cold Brew mode" in narrative
        assert "deliberate analysis" in narrative
        assert "Low momentum" in narrative

    def test_synthesize_explanation_with_coffee_metaphor(self, explainer):
        decision_id = "test_decision_1"
        context = {"resonance": 0.8}
        rationale = "Test rationale."
        cognitive_state = {"estimated_load": 2.0, "processing_mode": "system_1"}

        explanation = explainer.synthesize_explanation_with_coffee_metaphor(
            decision_id=decision_id, context=context, rationale=rationale, cognitive_state=cognitive_state
        )

        assert "coffee_metaphor_narrative" in explanation
        assert "Espresso" in explanation["coffee_metaphor_narrative"]

    def test_explain_pattern_with_coffee_metaphor_flow(self, explainer):
        pattern_detection = {
            "pattern_name": "flow",
            "detected": True,
            "confidence": 0.9,
            "explanation": "Flowing well.",
            "features": {"coffee_mode": "Espresso", "processing_mode": "rapid", "momentum": "high"},
        }
        explanation = explainer.explain_pattern_with_coffee_metaphor(pattern_detection)
        assert "Espresso" in explanation["coffee_metaphor"]
        assert "high" in explanation["coffee_metaphor"]
        explanation = explainer.explain_pattern_with_coffee_metaphor(pattern_detection)
        assert "Espresso" in explanation["coffee_metaphor"]
        assert "high" in explanation["coffee_metaphor"]

    def test_explain_temporal_resonance_low_score(self, explainer):
        """Test explanation for low resonance score."""
        explanation = explainer.explain_temporal_resonance(resonance_score=0.2, q_factor=0.8, distance=0.95, decay=0.3)
        assert "weak" in explanation.lower() or "low" in explanation.lower()

    def test_explain_temporal_resonance_medium_score(self, explainer):
        """Test explanation for medium resonance score."""
        explanation = explainer.explain_temporal_resonance(resonance_score=0.5, q_factor=0.5, distance=0.5, decay=0.6)
        assert "moderate" in explanation.lower() or "resonance" in explanation.lower()

    def test_generate_coffee_metaphor_narrative_americano(self, explainer):
        """Test coffee metaphor for Americano mode."""
        narrative = explainer.generate_coffee_metaphor_narrative(
            cognitive_load=5.0, processing_mode="balanced", momentum="balanced"
        )
        assert "Americano" in narrative or "balanced" in narrative.lower()
        assert "momentum" in narrative.lower()

    def test_synthesize_explanation_with_coffee_metaphor_cold_brew(self, explainer):
        """Test coffee metaphor synthesis for Cold Brew mode."""
        decision_id = "test_decision_2"
        context = {"resonance": 0.6}
        rationale = "Complex analysis required."
        cognitive_state = {"estimated_load": 8.0, "processing_mode": "system_2"}

        explanation = explainer.synthesize_explanation_with_coffee_metaphor(
            decision_id=decision_id, context=context, rationale=rationale, cognitive_state=cognitive_state
        )

        assert "coffee_metaphor_narrative" in explanation
        assert (
            "Cold Brew" in explanation["coffee_metaphor_narrative"]
            or "deliberate" in explanation["coffee_metaphor_narrative"].lower()
        )

    def test_explain_pattern_with_coffee_metaphor_multiple_features(self, explainer):
        """Test pattern explanation with flow pattern and coffee features."""
        pattern_detection = {
            "pattern_name": "flow",
            "detected": True,
            "confidence": 0.85,
            "explanation": "Flow state maintained.",
            "features": {
                "coffee_mode": "Cold Brew",
                "processing_mode": "comprehensive",
                "momentum": "low",
                "chunk_size": 128,
            },
        }
        explanation = explainer.explain_pattern_with_coffee_metaphor(pattern_detection)
        assert "coffee_metaphor" in explanation
        assert "Cold Brew" in explanation["coffee_metaphor"]
        assert "comprehensive" in explanation["coffee_metaphor"].lower()
        assert "low" in explanation["coffee_metaphor"].lower()

    def test_synthesize_explanation_with_coffee_metaphor_high_resonance(self, explainer):
        """Test synthesis with high resonance (near-perfect alignment)."""
        decision_id = "test_decision_perfect"
        context = {"resonance": 0.95, "safety_check": "PASSED"}
        rationale = "Perfect alignment with pattern."
        cognitive_state = {"estimated_load": 2.5, "processing_mode": "system_1", "mental_model_alignment": 0.95}

        explanation = explainer.synthesize_explanation_with_coffee_metaphor(
            decision_id=decision_id, context=context, rationale=rationale, cognitive_state=cognitive_state
        )

        assert explanation["decision_id"] == decision_id
        assert "coffee_metaphor_narrative" in explanation

    def test_synthesize_explanation_with_coffee_metaphor_low_resonance(self, explainer):
        """Test synthesis with low resonance (poor alignment)."""
        decision_id = "test_decision_poor"
        context = {"resonance": 0.3, "safety_check": "WARNING"}
        rationale = "Poor pattern alignment."
        cognitive_state = {"estimated_load": 9.0, "processing_mode": "system_2", "mental_model_alignment": 0.2}

        explanation = explainer.synthesize_explanation_with_coffee_metaphor(
            decision_id=decision_id, context=context, rationale=rationale, cognitive_state=cognitive_state
        )

        assert explanation["decision_id"] == decision_id
        assert "coffee_metaphor_narrative" in explanation
