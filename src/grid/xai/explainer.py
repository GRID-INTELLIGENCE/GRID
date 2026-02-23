"""
XAI (eXplainable AI) Framework for GRID.

Provides diagnostic explanations for agentic decisions, resonance scores,
and architectural enforcement with cognitive context and pattern awareness.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from cognitive import explain_resonance_with_patterns, get_pattern_explanation, get_pattern_matcher

logger = logging.getLogger(__name__)


class XAIExplainer:
    """
    XAI (eXplainable AI) Framework for GRID.

    Provides diagnostic explanations for agentic decisions, resonance scores,
    and architectural enforcement with cognitive context and pattern awareness.
    """

    def __init__(self, trace_dir: Path = Path("e:/grid/logs/xai_traces")):
        """Initialize the XAI explainer.

        Args:
            trace_dir: Directory for storing trace files
        """
        self.trace_dir = trace_dir
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.pattern_matcher = get_pattern_matcher()

    def synthesize_explanation(
        self,
        decision_id: str,
        context: dict[str, Any],
        rationale: str,
        cognitive_state: dict[str, Any] | None = None,
        detected_patterns: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate explanation with cognitive context.

        Args:
            decision_id: Unique identifier for the decision
            context: Decision context
            rationale: Decision rationale
            cognitive_state: Optional cognitive state information
            detected_patterns: Optional list of detected pattern results

        Returns:
            Structured explanation dictionary
        """
        explanation = {
            "decision_id": decision_id,
            "resonance_alignment": context.get("resonance", 0.0),
            "logic_path": self._decompose_logic(rationale),
            "safety_verification": context.get("safety_check", "PASSED"),
            "evidence_nodes": context.get("evidence", []),
            "uncertainty_factor": 1.0 - context.get("resonance", 1.0),
        }

        # Add cognitive context if available
        if cognitive_state:
            explanation["cognitive_context"] = {
                "load": cognitive_state.get("estimated_load", 0.0),
                "load_type": cognitive_state.get("load_type", "unknown"),
                "processing_mode": cognitive_state.get("processing_mode", "unknown"),
                "mental_model_alignment": cognitive_state.get("mental_model_alignment", 0.5),
                "working_memory_usage": cognitive_state.get("working_memory_usage", 0.0),
            }
            # Add cognitive-aware narrative
            explanation["narrative"] = self._generate_cognitive_narrative(
                explanation["cognitive_context"],
                context,
            )

        # Add pattern context if available
        if detected_patterns:
            explanation["pattern_context"] = self._process_patterns(detected_patterns)

        # Generate resonance explanation with patterns
        detected_pattern_names = [p.get("pattern_name") for p in (detected_patterns or []) if p.get("detected")]
        explanation["resonance_explanation"] = explain_resonance_with_patterns(
            context.get("resonance", 0.0),
            detected_pattern_names,
        )

        # Save trace for audit
        trace_path = self.trace_dir / f"trace_{decision_id}.json"
        try:
            with open(trace_path, "w") as f:
                json.dump(explanation, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save trace to {trace_path}: {e}")

        return explanation

    def get_pattern_explanation(self, pattern: str) -> dict[str, Any]:
        """Get human-readable explanation for a cognition pattern.

        Args:
            pattern: Pattern name

        Returns:
            Pattern explanation dictionary
        """
        explanation = get_pattern_explanation(pattern)

        if explanation:
            return {
                "pattern": pattern,
                "short_description": explanation.short_description,
                "full_explanation": explanation.full_explanation,
                "when_applies": explanation.when_applies,
                "what_to_do": explanation.what_to_do,
                "benefits": explanation.benefits,
            }

        return {
            "pattern": pattern,
            "short_description": "Pattern not found",
            "full_explanation": "",
            "when_applies": "",
            "what_to_do": "",
            "benefits": [],
        }

    def get_resonance_explanation(
        self,
        score: float,
        patterns: list[str] | None = None,
    ) -> str:
        """Get human-readable explanation for resonance score with pattern context.

        Args:
            score: Resonance score (0-1)
            patterns: Optional list of detected pattern names

        Returns:
            Human-readable explanation
        """
        return explain_resonance_with_patterns(score, patterns or [])

    def explain_case_execution(
        self,
        case_id: str,
        result: dict[str, Any],
        cognitive_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Explain a case execution with cognitive context.

        Args:
            case_id: Case identifier
            result: Execution result
            cognitive_state: Optional cognitive state

        Returns:
            Execution explanation
        """
        explanation = {
            "case_id": case_id,
            "outcome": result.get("outcome", "unknown"),
            "execution_time": result.get("execution_time_seconds", 0),
            "agent_role": result.get("agent_role", "unknown"),
        }

        # Add cognitive impact
        if cognitive_state:
            load = cognitive_state.get("estimated_load", 0.0)
            processing_mode = cognitive_state.get("processing_mode", "system_1")

            explanation["cognitive_impact"] = {
                "load": load,
                "mode": processing_mode,
                "recommendation": self._get_cognitive_recommendation(load, processing_mode),
            }

            # Check if flow state was maintained
            flow_state = load > 3.0 and load < 7.0
            explanation["flow_state"] = {
                "maintained": flow_state,
                "explanation": (
                    "Optimal cognitive balance was maintained during execution"
                    if flow_state
                    else "Cognitive balance was not optimal during execution"
                ),
            }

        return explanation

    def _decompose_logic(self, rationale: str) -> list[str]:
        """Break down a raw rationale into discrete logic steps.

        Args:
            rationale: Raw rationale text

        Returns:
            List of logic steps
        """
        # Simple heuristic decomposition
        steps = rationale.split(". ")
        return [step.strip() for step in steps if step.strip()]

    def _generate_cognitive_narrative(
        self,
        cognitive: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        """Generate human-readable narrative of cognitive factors.

        Args:
            cognitive: Cognitive state dictionary
            context: Decision context

        Returns:
            Human-readable narrative
        """
        load = cognitive.get("load", 0.0)
        mode = cognitive.get("processing_mode", "system_1")
        alignment = cognitive.get("mental_model_alignment", 0.5)

        parts = []

        # Load description
        if load < 3.0:
            parts.append("Low cognitive load enabled rapid processing")
        elif load < 6.0:
            parts.append("Balanced cognitive load supported effective decision-making")
        elif load < 8.0:
            parts.append("Elevated cognitive load required careful consideration")
        else:
            parts.append("High cognitive load may have impacted decision quality")

        # Processing mode description
        if mode == "system_1":
            parts.append("The decision relied on fast, intuitive processing (System 1)")
        else:
            parts.append("The decision employed deliberate, analytical processing (System 2)")

        # Mental model alignment
        if alignment > 0.7:
            parts.append("High alignment with user mental model")
        elif alignment > 0.4:
            parts.append("Moderate alignment with user expectations")
        else:
            parts.append("Some misalignment with user mental model was detected")

        return ". ".join(parts) + "."

    def _process_patterns(self, patterns: list[dict[str, Any]]) -> dict[str, Any]:
        """Process detected patterns into structured information.

        Args:
            patterns: List of pattern detection results

        Returns:
            Processed pattern information
        """
        detected = [p for p in patterns if p.get("detected", False)]
        high_confidence = [p for p in detected if p.get("confidence", 0) > 0.7]

        return {
            "total_detected": len(detected),
            "high_confidence": len(high_confidence),
            "pattern_names": [p.get("pattern_name") for p in detected],
            "high_confidence_patterns": [p.get("pattern_name") for p in high_confidence],
            "recommendations": self._aggregate_pattern_recommendations(detected),
        }

    def _aggregate_pattern_recommendations(self, patterns: list[dict[str, Any]]) -> list[str]:
        """Aggregate recommendations from multiple patterns.

        Args:
            patterns: List of pattern detection results

        Returns:
            Aggregated recommendations
        """
        all_recommendations = []
        for pattern in patterns:
            pattern.get("pattern_name", "")
            pattern_recs = pattern.get("recommendations", [])
            all_recommendations.extend(pattern_recs)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique.append(rec)

        return unique[:5]  # Limit to top 5

    def _get_cognitive_recommendation(self, load: float, mode: str) -> str:
        """Get recommendation based on cognitive state.

        Args:
            load: Cognitive load (0-10)
            mode: Processing mode

        Returns:
            Recommendation string
        """
        if load > 8.0:
            return "Consider simplifying the task or providing additional support"
        elif load > 6.0:
            return "Task complexity is high - break down into smaller steps"
        elif mode == "system_1":
            return "Fast processing was appropriate for this task"
        else:
            return "Analytical processing was beneficial for this complex task"

    # ========== Coffee House Temporal Resonance & Coffee Metaphor Concepts ==========

    def explain_temporal_resonance(
        self,
        resonance_score: float,
        q_factor: float,
        distance: float,
        decay: float,
    ) -> str:
        """Explain temporal resonance with audio engineering terminology (Coffee House concept).

        Args:
            resonance_score: Overall resonance score (0-1)
            q_factor: Width of resonance peak (0.1 = narrow, 0.9 = wide)
            distance: Temporal distance from resonance peak
            decay: Temporal decay factor

        Returns:
            Human-readable temporal resonance explanation
        """
        # Q factor description
        if q_factor < 0.3:
            q_desc = "narrow (high specificity)"
        elif q_factor > 0.7:
            q_desc = "wide (general coverage)"
        else:
            q_desc = "moderate (balanced specificity)"

        # Resonance strength description
        if resonance_score > 0.8:
            resonance_desc = "strong resonance peak detected"
        elif resonance_score > 0.5:
            resonance_desc = "moderate resonance alignment"
        else:
            resonance_desc = "weak resonance signal"

        # Distance description
        if distance < 0.2:
            distance_desc = "at the resonance peak (near-perfect alignment)"
        elif distance < 0.5:
            distance_desc = "close to resonance (good temporal alignment)"
        elif distance < 0.8:
            distance_desc = "approaching resonance fringe (moderate alignment)"
        else:
            distance_desc = "outside resonance zone (low alignment)"

        # Damping description
        if decay > 0.8:
            damping_desc = "minimal damping (signal preserved)"
        elif decay > 0.5:
            damping_desc = "moderate damping (signal attenuated)"
        else:
            damping_desc = "significant damping (signal decayed)"

        return (
            f"Temporal resonance: {resonance_desc}. "
            f"Q-factor {q_factor:.2f} ({q_desc}), "
            f"{distance_desc}. "
            f"Damping: {damping_desc}."
        )

    def generate_coffee_metaphor_narrative(
        self,
        cognitive_load: float,
        processing_mode: str,
        momentum: str | None = None,
    ) -> str:
        """Generate coffee-themed narrative for cognitive state (Coffee House concept).

        Maps cognitive state to coffee preparation metaphors.

        Args:
            cognitive_load: Current cognitive load (0-10)
            processing_mode: Processing mode (system_1, system_2, balanced)
            momentum: Optional momentum level (high, balanced, low)

        Returns:
            Coffee-themed narrative string
        """
        # Determine coffee mode
        if cognitive_load < 3.0:
            coffee_mode = "Espresso"
            chunk_size = "32 characters"
            pace = "rapid fire"
        elif cognitive_load < 7.0:
            coffee_mode = "Americano"
            chunk_size = "64 characters"
            pace = "steady rhythm"
        else:
            coffee_mode = "Cold Brew"
            chunk_size = "128 characters"
            pace = "deliberate"

        # Build narrative
        parts = [f"Decision made in {coffee_mode} mode."]

        # Add processing mode information
        if processing_mode == "system_1":
            parts.append(f"Engaging {pace} processing characteristic of {coffee_mode.lower()} shots.")
        elif processing_mode == "system_2":
            parts.append(f"Deep {pace} analysis typical of {coffee_mode.lower()} extraction.")
        else:
            parts.append(f"Balanced {pace} flow maintained throughout.")

        # Add momentum if available
        if momentum == "high":
            parts.append("High momentum enabled quick, concentrated decisions.")
        elif momentum == "low":
            parts.append("Low momentum allowed for thorough, comprehensive evaluation.")
        elif momentum == "balanced":
            parts.append("Balanced momentum sustained steady progress.")

        # Add chunk size recommendation
        parts.append(f"Optimal chunk size: {chunk_size} for current cognitive state.")

        return " ".join(parts) + "."

    def synthesize_explanation_with_coffee_metaphor(
        self,
        decision_id: str,
        context: dict[str, Any],
        rationale: str,
        cognitive_state: dict[str, Any] | None = None,
        detected_patterns: list[dict[str, Any]] | None = None,
        temporal_resonance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Synthesize explanation with coffee metaphors and temporal resonance (Coffee House concept).

        Extended version of synthesize_explanation() with Coffee House enhancements.

        Args:
            decision_id: Unique identifier for the decision
            context: Decision context
            rationale: Decision rationale
            cognitive_state: Optional cognitive state information
            detected_patterns: Optional list of detected pattern results
            temporal_resonance: Optional temporal resonance information

        Returns:
            Structured explanation dictionary with coffee metaphors
        """
        # Get base explanation
        explanation = self.synthesize_explanation(
            decision_id=decision_id,
            context=context,
            rationale=rationale,
            cognitive_state=cognitive_state,
            detected_patterns=detected_patterns,
        )

        # Add coffee metaphor narrative if cognitive state available
        if cognitive_state:
            cognitive_load = cognitive_state.get("estimated_load", 5.0)
            processing_mode = cognitive_state.get("processing_mode", "balanced")

            # Check for coffee mode in patterns (if Flow pattern detected)
            if detected_patterns:
                flow_pattern = next((p for p in detected_patterns if p.get("pattern_name") == "flow"), None)
                if flow_pattern:
                    flow_pattern.get("features", {}).get("coffee_mode", None)
                    momentum = flow_pattern.get("features", {}).get("momentum", None)
                else:
                    momentum = None
            else:
                momentum = None

            # Generate coffee metaphor narrative
            coffee_narrative = self.generate_coffee_metaphor_narrative(
                cognitive_load=cognitive_load,
                processing_mode=processing_mode,
                momentum=momentum,
            )
            explanation["coffee_metaphor_narrative"] = coffee_narrative

        # Add temporal resonance if available
        if temporal_resonance:
            temporal_narrative = self.explain_temporal_resonance(
                resonance_score=temporal_resonance.get("score", 0.0),
                q_factor=temporal_resonance.get("q_factor", 0.5),
                distance=temporal_resonance.get("distance", 0.0),
                decay=temporal_resonance.get("decay", 1.0),
            )
            explanation["temporal_resonance_explanation"] = temporal_narrative
            explanation["temporal_resonance"] = temporal_resonance

        return explanation

    def explain_pattern_with_coffee_metaphor(
        self,
        pattern_detection: dict[str, Any],
    ) -> dict[str, Any]:
        """Explain a pattern detection with coffee metaphors (Coffee House concept).

        Args:
            pattern_detection: Pattern detection result with features

        Returns:
            Pattern explanation with coffee metaphor context
        """
        pattern_name = pattern_detection.get("pattern_name", "unknown")
        features = pattern_detection.get("features", {})
        confidence = pattern_detection.get("confidence", 0.0)

        explanation = {
            "pattern": pattern_name,
            "detected": pattern_detection.get("detected", False),
            "confidence": confidence,
            "base_explanation": pattern_detection.get("explanation", ""),
        }

        # Add coffee metaphor for Flow pattern
        if pattern_name == "flow":
            coffee_mode = features.get("coffee_mode", "Americano")
            processing_mode = features.get("processing_mode", "balanced")
            momentum = features.get("momentum", "balanced")

            coffee_explanation = (
                f"Flow detected in {coffee_mode} mode. Processing: {processing_mode}, Momentum: {momentum}. "
            )
            if coffee_mode == "Espresso":
                coffee_explanation += "Ultra-focused precision with rapid decision-making."
            elif coffee_mode == "Americano":
                coffee_explanation += "Balanced cognitive flow for sustained engagement."
            else:  # Cold Brew
                coffee_explanation += "Comprehensive analysis for complex decisions."

            explanation["coffee_metaphor"] = coffee_explanation

        # Add temporal resonance for Time pattern
        elif pattern_name == "time":
            temporal_intent = features.get("temporal_intent")
            if temporal_intent:
                explanation["temporal_context"] = {
                    "era_type": temporal_intent.get("era_type", "none"),
                    "start_year": temporal_intent.get("start_year"),
                    "end_year": temporal_intent.get("end_year"),
                }

        return explanation

    def generate_hybrid_explanation(
        self,
        decision_id: str,
        context: dict[str, Any],
        rationale: str,
        cognitive_state: dict[str, Any] | None = None,
        detected_patterns: list[dict[str, Any]] | None = None,
        temporal_resonance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate comprehensive explanation with all Coffee House concepts.

        Combines cognitive context, coffee metaphors, temporal resonance, and patterns.

        Args:
            decision_id: Unique identifier for the decision
            context: Decision context
            rationale: Decision rationale
            cognitive_state: Optional cognitive state information
            detected_patterns: Optional list of detected pattern results
            temporal_resonance: Optional temporal resonance information

        Returns:
            Comprehensive explanation with all Coffee House concepts
        """
        # Synthesize with coffee metaphors and temporal resonance
        explanation = self.synthesize_explanation_with_coffee_metaphor(
            decision_id=decision_id,
            context=context,
            rationale=rationale,
            cognitive_state=cognitive_state,
            detected_patterns=detected_patterns,
            temporal_resonance=temporal_resonance,
        )

        # Add pattern-specific explanations with coffee metaphors
        if detected_patterns:
            explanation["pattern_explanations"] = [
                self.explain_pattern_with_coffee_metaphor(pattern)
                for pattern in detected_patterns
                if pattern.get("detected")
            ]

        # Add comprehensive narrative combining all elements
        narrative_parts = []

        if cognitive_state:
            narrative_parts.append(explanation.get("narrative", ""))

        if "coffee_metaphor_narrative" in explanation:
            narrative_parts.append(explanation["coffee_metaphor_narrative"])

        if "temporal_resonance_explanation" in explanation:
            narrative_parts.append(explanation["temporal_resonance_explanation"])

        if "resonance_explanation" in explanation:
            narrative_parts.append(explanation["resonance_explanation"])

        explanation["comprehensive_narrative"] = " ".join(narrative_parts)

        return explanation


# Global instance for convenience
explainer = XAIExplainer()
