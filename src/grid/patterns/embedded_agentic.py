"""Embedded agentic pattern detection for GRID.

This module extends GRID's pattern recognition to detect embedded agentic species:
systems whose structure/behavior reveals agentic patterns without direct actions.
Examples: neural networks, fungal networks, information flow.
"""

from __future__ import annotations

from typing import Any

from grid.essence.core_state import EssentialState
from grid.patterns.recognition import PatternRecognition


class EmbeddedAgenticDetector:
    """Detects embedded agentic patterns in structures.

    Embedded agentic species are systems where structure reveals behavior:
    - Neural networks: topology reveals learning capabilities
    - Fungal networks: mycelial structure reveals distributed intelligence
    - Information flow: propagation patterns reveal agentic influence
    """

    def __init__(self, base_recognizer: PatternRecognition | None = None):
        """Initialize embedded agentic detector.

        Args:
            base_recognizer: Optional base pattern recognizer to extend
        """
        # Create new instance to avoid recursion if base_recognizer is ExtendedPatternRecognition
        if base_recognizer is None or isinstance(base_recognizer, ExtendedPatternRecognition):
            self.base_recognizer = PatternRecognition()
        else:
            self.base_recognizer = base_recognizer
        self.embedded_patterns: list[str] = []

        # Pattern signatures for embedded agentic species
        self.pattern_signatures = {
            "neural_network": {
                "indicators": ["nodes", "connections", "weights", "layers", "activation"],
                "patterns": ["FLOW_MOTION", "SPATIAL_RELATIONSHIPS", "COMBINATION_PATTERNS"],
            },
            "information_flow": {
                "indicators": ["propagation", "influence", "vector", "pathway", "flow"],
                "patterns": ["FLOW_MOTION", "CAUSE_EFFECT", "TEMPORAL_PATTERNS"],
            },
            "network_structure": {
                "indicators": ["network", "graph", "topology", "connection", "edge"],
                "patterns": ["SPATIAL_RELATIONSHIPS", "COMBINATION_PATTERNS"],
            },
        }

    async def detect_embedded_agentic(self, state: EssentialState) -> dict[str, Any]:
        """Detect embedded agentic patterns in state.

        Args:
            state: Essential state to analyze

        Returns:
            Dictionary with detected embedded agentic patterns and metadata
        """
        # Use base recognizer for standard patterns
        base_patterns = await self.base_recognizer.recognize(state)

        # Analyze quantum state for embedded agentic indicators
        quantum_state = state.quantum_state or {}
        state_str = str(quantum_state).lower()

        detected_species = []
        pattern_matches = {}
        confidence_scores = {}

        # Check for each embedded agentic species type
        for species_type, signature in self.pattern_signatures.items():
            # Count indicator matches
            indicator_matches = sum(1 for indicator in signature["indicators"] if indicator in state_str)

            # Calculate confidence based on indicator matches
            confidence = min(1.0, indicator_matches / len(signature["indicators"]))

            if confidence > 0.3:  # Threshold for detection
                detected_species.append(species_type)
                pattern_matches[species_type] = signature["patterns"]
                confidence_scores[species_type] = confidence

        # Analyze structure for agentic patterns
        structure_analysis = self._analyze_structure(quantum_state)

        # Combine base patterns with embedded agentic patterns
        all_patterns = base_patterns + detected_species

        return {
            "embedded_agentic_species": detected_species,
            "base_patterns": base_patterns,
            "all_patterns": all_patterns,
            "pattern_matches": pattern_matches,
            "confidence_scores": confidence_scores,
            "structure_analysis": structure_analysis,
            "agentic_indicators": {
                "has_structure": structure_analysis.get("has_structure", False),
                "has_flow": structure_analysis.get("has_flow", False),
                "has_connections": structure_analysis.get("has_connections", False),
            },
        }

    def _analyze_structure(self, quantum_state: dict[str, Any]) -> dict[str, Any]:
        """Analyze structure for embedded agentic patterns.

        Args:
            quantum_state: Quantum state dictionary to analyze

        Returns:
            Structure analysis with agentic indicators
        """
        analysis: dict[str, Any] = {
            "has_structure": False,
            "has_flow": False,
            "has_connections": False,
            "structure_type": None,
        }

        # Check for network/graph structures
        if isinstance(quantum_state, dict):
            # Look for graph-like structures (direct keys or nested)
            if "nodes" in quantum_state or "edges" in quantum_state:
                analysis["has_structure"] = True
                analysis["has_connections"] = True
                analysis["structure_type"] = "graph"
            elif "graph" in quantum_state:
                # Check nested graph structure
                graph_data = quantum_state.get("graph", {})
                if isinstance(graph_data, dict):
                    if "nodes" in graph_data or "edges" in graph_data:
                        analysis["has_structure"] = True
                        analysis["has_connections"] = True
                        analysis["structure_type"] = "graph"

            # Look for flow patterns
            if "flow" in quantum_state or "propagation" in quantum_state:
                analysis["has_flow"] = True
                if not analysis["structure_type"]:
                    analysis["structure_type"] = "flow"

            # Look for layer structures (neural networks)
            if "layers" in quantum_state or "weights" in quantum_state:
                analysis["has_structure"] = True
                if not analysis["structure_type"]:
                    analysis["structure_type"] = "neural"

        return analysis

    async def recognize_with_embedded(self, state: EssentialState) -> list[str]:
        """Recognize patterns including embedded agentic patterns.

        This is a convenience method that combines base recognition
        with embedded agentic detection.

        Args:
            state: Essential state to analyze

        Returns:
            List of all detected patterns (base + embedded agentic)
        """
        result = await self.detect_embedded_agentic(state)
        all_patterns: list[str] = result.get("all_patterns", [])
        return all_patterns


# Integration with existing PatternRecognition
class ExtendedPatternRecognition(PatternRecognition):
    """Extended pattern recognition with embedded agentic detection.

    Extends GRID's base PatternRecognition to include embedded agentic
    pattern detection while maintaining backward compatibility.
    """

    def __init__(self) -> None:
        """Initialize extended pattern recognition."""
        super().__init__()
        # Pass None to avoid recursion - detector will create its own base recognizer
        self.embedded_detector = EmbeddedAgenticDetector(base_recognizer=None)

    async def recognize(self, state: EssentialState) -> list[str]:
        """Recognize patterns including embedded agentic patterns.

        Overrides base method to include embedded agentic detection.

        Args:
            state: Essential state to analyze

        Returns:
            List of detected patterns (base + embedded agentic)
        """
        # Get base patterns
        base_patterns = await super().recognize(state)

        # Detect embedded agentic patterns
        embedded_result = await self.embedded_detector.detect_embedded_agentic(state)

        # Combine patterns
        embedded_patterns: list[str] = embedded_result.get("embedded_agentic_species", [])
        all_patterns = base_patterns + embedded_patterns

        # Store embedded patterns for reference
        self.embedded_patterns = embedded_patterns

        return all_patterns

    async def get_embedded_analysis(self, state: EssentialState) -> dict[str, Any]:
        """Get detailed embedded agentic analysis.

        Args:
            state: Essential state to analyze

        Returns:
            Detailed embedded agentic analysis
        """
        return await self.embedded_detector.detect_embedded_agentic(state)
