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
