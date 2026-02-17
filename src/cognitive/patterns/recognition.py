"""Complete implementation of the 9 cognition patterns.

Each pattern has:
- Recognizer: Detect pattern in data
- Analyzer: Extract pattern features
- Recommender: Suggest actions based on pattern

The 9 Cognition Patterns:
1. Flow - Continuous motion/progression
2. Spatial - Geometric relationships
3. Rhythm - Temporal regularity
4. Color - Multidimensional attributes
5. Repetition - Reoccurring patterns
6. Deviation - Unexpected changes
7. Cause - Causal relationships
8. Time - Temporal evolution
9. Combination - Composite patterns
"""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from collections import Counter, deque
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)


class PatternConfidence(StrEnum):
    """Confidence levels for pattern detection."""

    LOW = "low"  # 0.0 - 0.3
    MEDIUM = "medium"  # 0.3 - 0.7
    HIGH = "high"  # 0.7 - 1.0


@dataclass
class PatternDetection:
    """Result of pattern detection."""

    pattern_name: str
    detected: bool
    confidence: float  # 0.0 - 1.0
    features: dict[str, Any]
    explanation: str
    recommendations: list[str]

    def get_confidence_level(self) -> PatternConfidence:
        """Get confidence level as enum."""
        if self.confidence < 0.3:
            return PatternConfidence.LOW
        elif self.confidence < 0.7:
            return PatternConfidence.MEDIUM
        return PatternConfidence.HIGH


@dataclass
class PatternFeatures:
    """Features extracted from pattern analysis."""

    intensity: float  # How strong/intense the pattern is
    stability: float  # How stable the pattern is over time
    frequency: float  # How often the pattern occurs
    duration: float  # How long the pattern lasts
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intensity": self.intensity,
            "stability": self.stability,
            "frequency": self.frequency,
            "duration": self.duration,
            "metadata": self.metadata,
        }


T = TypeVar("T")


class PatternRecognizer[T](ABC):
    """Base class for pattern recognizers.

    Each pattern recognizer must implement:
    - recognize(): Detect if pattern is present
    - analyze(): Extract features from pattern
    - recommend(): Suggest actions based on pattern
    """

    def __init__(self, name: str):
        """Initialize pattern recognizer.

        Args:
            name: Pattern name
        """
        self.name = name
        self.detection_threshold = 0.5
        self.history_size = 50

    @abstractmethod
    async def recognize(self, data: T) -> PatternDetection:
        """Detect if pattern is present in data.

        Args:
            data: Input data to analyze

        Returns:
            PatternDetection with detection results
        """
        pass

    @abstractmethod
    def analyze(self, data: T) -> PatternFeatures:
        """Extract features from pattern in data.

        Args:
            data: Input data to analyze

        Returns:
            PatternFeatures with extracted features
        """
        pass

    @abstractmethod
    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate recommendations based on pattern detection.

        Args:
            detection: Pattern detection result

        Returns:
            List of recommendation strings
        """
        pass


@dataclass
class CoffeeMode:
    """Coffee shop metaphor for cognitive state (Coffee House concept).

    Coffee modes represent different cognitive processing styles:
    - Espresso: Ultra-focused, precision, 32-char chunks
    - Americano: Balanced, flow state, 64-char chunks
    - Cold Brew: Comprehensive, deliberate, 128-char chunks

    Attributes:
        name: Coffee mode name
        chunk_size: Recommended chunk size for this mode
        cognitive_load_range: (min, max) cognitive load for this mode
        processing_mode: System 1 (fast) or System 2 (slow)
        momentum: Momentum level (high, balanced, low)
        description: Human-readable description
    """

    name: str
    chunk_size: int
    cognitive_load_range: tuple[float, float]
    processing_mode: str  # "system_1" or "system_2"
    momentum: str  # "high", "balanced", "low"
    description: str


# Coffee mode definitions from Coffee House canon
COFFEE_MODES = {
    "espresso": CoffeeMode(
        name="Espresso",
        chunk_size=32,
        cognitive_load_range=(0.0, 3.0),
        processing_mode="system_1",
        momentum="high",
        description="Ultra-focused precision mode - quick, concentrated processing",
    ),
    "americano": CoffeeMode(
        name="Americano",
        chunk_size=64,
        cognitive_load_range=(3.0, 7.0),
        processing_mode="balanced",
        momentum="balanced",
        description="Balanced flow state - optimal cognitive balance",
    ),
    "cold_brew": CoffeeMode(
        name="Cold Brew",
        chunk_size=128,
        cognitive_load_range=(7.0, 10.0),
        processing_mode="system_2",
        momentum="low",
        description="Comprehensive analysis mode - deep, deliberate processing",
    ),
}


class FlowPattern(PatternRecognizer):
    """Detects flow states with coffee shop metaphors (Coffee House concept).

    Flow characteristics:
    - High engagement, balanced cognitive load
    - Clear goals and immediate feedback
    - Sense of control and focus
    - Loss of self-consciousness
    - Distorted sense of time

    Coffee modes (Coffee House):
    - Espresso: Ultra-focused, low load (0-3), high momentum
    - Americano: Balanced flow, medium load (3-7), balanced momentum
    - Cold Brew: Comprehensive, high load (7-10), low momentum
    """

    def __init__(self):
        super().__init__("flow")
        self.detection_threshold = 0.6

    async def recognize(self, data: dict[str, Any]) -> PatternDetection:
        """Detect flow state from cognitive data.

        Args:
            data: Dictionary with cognitive state metrics

        Returns:
            PatternDetection for flow
        """
        cognitive_load = data.get("cognitive_load", 5.0)
        engagement = data.get("engagement", 0.5)
        focus_score = data.get("focus", 0.5)
        time_distortion = data.get("time_distortion", 0.0)

        # Flow indicators: moderate load (not too high/low), high engagement
        load_score = 1.0 - abs(cognitive_load - 5.0) / 5.0  # Optimal at 5.0
        flow_score = (load_score + engagement + focus_score + time_distortion) / 4.0

        features = {
            "load_balance": load_score,
            "engagement_level": engagement,
            "focus_depth": focus_score,
            "time_distortion": time_distortion,
        }

        explanation = self._generate_explanation(flow_score, features)

        recommendations = []
        if flow_score > 0.7:
            recommendations.append("Maintain current environment to preserve flow state")
            recommendations.append("Minimize interruptions during flow")
        elif flow_score > 0.4:
            recommendations.append("Adjust challenge level slightly to reach optimal flow")
        else:
            recommendations.append("Reduce distractions and increase engagement")

        return PatternDetection(
            pattern_name=self.name,
            detected=flow_score >= self.detection_threshold,
            confidence=flow_score,
            features=features,
            explanation=explanation,
            recommendations=recommendations,
        )

    def analyze(self, data: dict[str, Any]) -> PatternFeatures:
        """Analyze flow features from data."""
        return PatternFeatures(
            intensity=data.get("engagement", 0.5),
            stability=data.get("stability", 0.7),
            frequency=data.get("flow_frequency", 0.5),
            duration=data.get("session_duration", 0.0),
            metadata={
                "flow_triggers": data.get("triggers", []),
                "flow_breakers": data.get("breakers", []),
            },
        )

    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate flow-based recommendations."""
        return detection.recommendations

    def _generate_explanation(self, score: float, features: dict[str, Any]) -> str:
        """Generate human-readable explanation."""
        if score > 0.8:
            return "You are in deep flow - fully engaged with optimal cognitive load."
        elif score > 0.6:
            return "Flow state detected - balanced engagement and challenge."
        elif score > 0.4:
            return "Approaching flow - adjust challenge to reach optimal state."
        else:
            return "Not in flow - consider reducing distractions or adjusting difficulty."

    # ========== Coffee House Coffee Metaphor Concepts ==========

    def detect_coffee_mode(self, cognitive_load: float) -> CoffeeMode:
        """Detect coffee mode based on cognitive load (Coffee House concept).

        Maps cognitive load to coffee preparation modes:
        - Load < 3.0: Espresso (precision mode)
        - Load 3.0-7.0: Americano (balanced mode)
        - Load > 7.0: Cold Brew (comprehensive mode)

        Args:
            cognitive_load: Current cognitive load (0-10)

        Returns:
            CoffeeMode for the current cognitive state
        """
        if cognitive_load < 3.0:
            return COFFEE_MODES["espresso"]
        elif cognitive_load < 7.0:
            return COFFEE_MODES["americano"]
        else:
            return COFFEE_MODES["cold_brew"]

    async def recognize_with_coffee_mode(self, data: dict[str, Any]) -> PatternDetection:
        """Detect flow state with coffee mode information (Coffee House concept).

        Extends the base recognize() method to include coffee mode analysis.

        Args:
            data: Dictionary with cognitive state metrics

        Returns:
            PatternDetection for flow with coffee mode features
        """
        # Get base detection
        detection = await self.recognize(data)

        # Add coffee mode information
        cognitive_load = data.get("cognitive_load", 5.0)
        coffee_mode = self.detect_coffee_mode(cognitive_load)

        # Update features with coffee mode information
        detection.features["coffee_mode"] = coffee_mode.name
        detection.features["recommended_chunk_size"] = coffee_mode.chunk_size
        detection.features["processing_mode"] = coffee_mode.processing_mode
        detection.features["momentum"] = coffee_mode.momentum

        # Update explanation with coffee metaphor
        base_explanation = detection.explanation
        coffee_explanation = self._generate_coffee_explanation(detection.confidence, coffee_mode)
        detection.explanation = f"{base_explanation} {coffee_explanation}"

        # Add coffee-specific recommendations
        coffee_recommendations = self._get_coffee_recommendations(coffee_mode)
        detection.recommendations.extend(coffee_recommendations)

        return detection

    def _generate_coffee_explanation(self, flow_score: float, coffee_mode: CoffeeMode) -> str:
        """Generate coffee-themed explanation (Coffee House concept).

        Args:
            flow_score: Flow detection confidence
            coffee_mode: Detected coffee mode

        Returns:
            Coffee-themed explanation string
        """
        if flow_score > 0.7:
            return f"Decision made in {coffee_mode.name} mode - {coffee_mode.description.lower()}."
        elif flow_score > 0.4:
            return f"Transitioning toward {coffee_mode.name} mode for optimal processing."
        else:
            return f"Consider {coffee_mode.name} mode approach: {coffee_mode.description.lower()}."

    def _get_coffee_recommendations(self, coffee_mode: CoffeeMode) -> list[str]:
        """Get recommendations based on coffee mode (Coffee House concept).

        Args:
            coffee_mode: Current coffee mode

        Returns:
            List of coffee-themed recommendations
        """
        if coffee_mode.name == "Espresso":
            return [
                "Espresso mode: Focus on precision with quick, targeted actions.",
                "Use small chunks (32 chars) for maximum clarity.",
                "High momentum enabled - rapid fire decisions appropriate.",
            ]
        elif coffee_mode.name == "Americano":
            return [
                "Americano mode: Maintain balanced cognitive flow.",
                "Use medium chunks (64 chars) for optimal comprehension.",
                "Sustained momentum - steady progress through tasks.",
            ]
        else:  # Cold Brew
            return [
                "Cold Brew mode: Comprehensive analysis for complex decisions.",
                "Use large chunks (128 chars) for deep understanding.",
                "Low momentum - take time for thorough deliberation.",
            ]

    def calculate_momentum(self, data: dict[str, Any]) -> dict[str, Any]:
        """Calculate cognitive momentum (Coffee House concept).

        Momentum represents the energy and pace of cognitive processing.

        Args:
            data: Dictionary with cognitive state metrics

        Returns:
            Dictionary with momentum information
        """
        cognitive_load = data.get("cognitive_load", 5.0)
        engagement = data.get("engagement", 0.5)
        data.get("focus", 0.5)

        coffee_mode = self.detect_coffee_mode(cognitive_load)

        # Calculate momentum score based on mode and engagement
        if coffee_mode.name == "Espresso":
            # High momentum: quick, focused
            momentum_score = 0.8 + (engagement * 0.2)
        elif coffee_mode.name == "Americano":
            # Balanced momentum: steady flow
            momentum_score = 0.5 + (engagement * 0.3)
        else:  # Cold Brew
            # Low momentum: deliberate
            momentum_score = 0.3 + (engagement * 0.2)

        return {
            "momentum_score": momentum_score,
            "momentum_type": coffee_mode.momentum,
            "coffee_mode": coffee_mode.name,
            "recommended_pace": "fast" if momentum_score > 0.7 else "steady" if momentum_score > 0.4 else "deliberate",
        }


class SpatialPattern(PatternRecognizer):
    """Detects geometric relationships and spatial shifts.

    Spatial patterns involve:
    - Positioning and arrangement
    - Distance and proximity
    - Direction and orientation
    - Spatial transformations
    """

    def __init__(self):
        super().__init__("spatial")

    async def recognize(self, data: dict[str, Any]) -> PatternDetection:
        """Detect spatial patterns in data.

        Args:
            data: Dictionary with spatial coordinates or relationships

        Returns:
            PatternDetection for spatial
        """
        # Extract spatial features
        coordinates = data.get("coordinates", [])
        distances = data.get("distances", [])
        directions = data.get("directions", [])

        # Calculate spatial consistency
        if coordinates and len(coordinates) > 2:
            # Check for clustering or regular spacing
            consistency = self._calculate_spatial_consistency(coordinates)
        elif distances:
            # Check distance patterns
            avg_dist = sum(distances) / len(distances)
            variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances)
            consistency = 1.0 - min(variance / (avg_dist**2 + 1), 1.0)
        else:
            consistency = 0.0

        # Direction consistency
        direction_consistency = 0.0
        if directions:
            # Check if directions are clustered
            direction_consistency = self._calculate_direction_consistency(directions)

        spatial_score = (consistency + direction_consistency) / 2.0

        features = {
            "spatial_consistency": consistency,
            "direction_consistency": direction_consistency,
            "coordination_level": spatial_score,
        }

        explanation = self._generate_explanation(spatial_score, features)

        recommendations = [
            "Leverage spatial relationships for better organization",
            "Consider spatial metaphors for complex concepts",
        ]

        return PatternDetection(
            pattern_name=self.name,
            detected=spatial_score >= self.detection_threshold,
            confidence=spatial_score,
            features=features,
            explanation=explanation,
            recommendations=recommendations,
        )

    def analyze(self, data: dict[str, Any]) -> PatternFeatures:
        """Analyze spatial features."""
        return PatternFeatures(
            intensity=data.get("spatial_intensity", 0.5),
            stability=data.get("spatial_stability", 0.7),
            frequency=data.get("pattern_frequency", 0.5),
            duration=data.get("spatial_duration", 0.0),
            metadata={
                "dominant_direction": data.get("dominant_direction"),
                "clustering_degree": data.get("clustering"),
            },
        )

    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate spatial-based recommendations."""
        return detection.recommendations

    def _calculate_spatial_consistency(self, coordinates: list[tuple[float, float]]) -> float:
        """Calculate how consistent spatial arrangement is."""
        if len(coordinates) < 3:
            return 0.0

        # Calculate variance in positions
        x_vals = [c[0] for c in coordinates]
        y_vals = [c[1] for c in coordinates]

        x_var = sum((x - sum(x_vals) / len(x_vals)) ** 2 for x in x_vals) / len(x_vals)
        y_var = sum((y - sum(y_vals) / len(y_vals)) ** 2 for y in y_vals) / len(y_vals)

        # Normalize (high variance can indicate spread, low variance indicates cluster)
        return 1.0 / (1 + math.sqrt(x_var + y_var))

    def _calculate_direction_consistency(self, directions: list[float]) -> float:
        """Calculate consistency of directional vectors."""
        if not directions:
            return 0.0

        # Use vector sum to check if directions are clustered
        x_sum = sum(math.cos(d) for d in directions)
        y_sum = sum(math.sin(d) for d in directions)

        magnitude = math.sqrt(x_sum**2 + y_sum**2)
        return magnitude / len(directions)

    def _generate_explanation(self, score: float, features: dict[str, Any]) -> str:
        """Generate human-readable explanation."""
        if score > 0.7:
            return "Strong spatial patterns detected - clear geometric relationships."
        elif score > 0.4:
            return "Moderate spatial organization - some regular structure."
        else:
            return "Weak spatial patterns - relationships are scattered."


class RhythmPattern(PatternRecognizer):
    """Detects temporal regularity and cadence.

    Rhythm patterns involve:
    - Regular intervals between events
    - Consistent pacing
    - Predictable timing patterns
    - Temporal cycles
    """

    def __init__(self):
        super().__init__("rhythm")
        self.timestamp_history: deque[float] = deque(maxlen=100)

    async def recognize(self, data: dict[str, Any]) -> PatternDetection:
        """Detect rhythmic patterns in temporal data.

        Args:
            data: Dictionary with timestamps or timing information

        Returns:
            PatternDetection for rhythm
        """
        timestamps = data.get("timestamps", [])
        intervals = data.get("intervals", [])

        if intervals:
            # Direct intervals provided
            interval_data = intervals
        elif timestamps and len(timestamps) > 2:
            # Calculate intervals from timestamps
            parsed_timestamps = []
            for ts in timestamps:
                if isinstance(ts, str):
                    try:
                        parsed_timestamps.append(datetime.fromisoformat(ts).timestamp())
                    except ValueError:
                        continue
                elif isinstance(ts, datetime):
                    parsed_timestamps.append(ts.timestamp())
                elif isinstance(ts, (int, float)):
                    parsed_timestamps.append(float(ts))

            if len(parsed_timestamps) > 1:
                interval_data = [
                    (parsed_timestamps[i] - parsed_timestamps[i - 1]) for i in range(1, len(parsed_timestamps))
                ]
            else:
                interval_data = []
        else:
            interval_data = []

        # Update history
        if interval_data:
            self.timestamp_history.extend(interval_data)

        # Calculate rhythm metrics
        if len(self.timestamp_history) > 5:
            rhythm_score = self._calculate_rhythm_score(list(self.timestamp_history))
        else:
            rhythm_score = 0.0

        features = {
            "interval_consistency": rhythm_score,
            "average_interval": sum(interval_data) / len(interval_data) if interval_data else 0.0,
            "interval_variance": self._calculate_variance(interval_data) if interval_data else 0.0,
        }

        explanation = self._generate_explanation(rhythm_score, features)

        recommendations = []
        if rhythm_score > 0.7:
            recommendations.append("Maintain current rhythm for optimal engagement")
        elif rhythm_score > 0.4:
            recommendations.append("Consider establishing more consistent timing")
        else:
            recommendations.append("Work on establishing predictable patterns")

        return PatternDetection(
            pattern_name=self.name,
            detected=rhythm_score >= self.detection_threshold,
            confidence=rhythm_score,
            features=features,
            explanation=explanation,
            recommendations=recommendations,
        )

    def analyze(self, data: dict[str, Any]) -> PatternFeatures:
        """Analyze rhythm features."""
        return PatternFeatures(
            intensity=data.get("rhythm_intensity", 0.5),
            stability=data.get("rhythm_stability", 0.7),
            frequency=data.get("beat_frequency", 0.5),
            duration=data.get("cycle_duration", 0.0),
            metadata={
                "tempo": data.get("tempo"),
                "complexity": data.get("rhythm_complexity"),
            },
        )

    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate rhythm-based recommendations."""
        return detection.recommendations

    def _calculate_rhythm_score(self, intervals: list[float]) -> float:
        """Calculate how rhythmic the intervals are."""
        if len(intervals) < 3:
            return 0.0

        # Calculate coefficient of variation
        mean = sum(intervals) / len(intervals)
        std_dev = math.sqrt(sum((x - mean) ** 2 for x in intervals) / len(intervals))

        if mean == 0:
            return 0.0

        cv = std_dev / mean
        return 1.0 - min(cv, 1.0)

    def _calculate_variance(self, values: list[float]) -> float:
        """Calculate variance of values."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _generate_explanation(self, score: float, features: dict[str, Any]) -> str:
        """Generate human-readable explanation."""
        if score > 0.8:
            return "Strong rhythmic pattern - very consistent timing detected."
        elif score > 0.6:
            return "Good rhythm established - predictable cadence present."
        elif score > 0.4:
            return "Moderate rhythm - some consistency with minor variations."
        else:
            return "Weak rhythm - timing is irregular and unpredictable."


class ColorPattern(PatternRecognizer):
    """Fuses multidimensional attributes into color metaphors.

    Color patterns represent:
    - Multivariate data fusion
    - Attribute combinations
    - Dimensional relationships
    - Metaphorical color mapping
    """

    def __init__(self):
        super().__init__("color")

    async def recognize(self, data: dict[str, Any]) -> PatternDetection:
        """Detect color patterns in multivariate data.

        Args:
            data: Dictionary with multiple dimensions/attributes

        Returns:
            PatternDetection for color
        """
        # Extract multidimensional attributes
        dimensions = data.get("dimensions", {})
        attributes = data.get("attributes", {})

        # Calculate color metaphor based on dimensions
        if dimensions:
            color_score, color_name = self._calculate_color_from_dimensions(dimensions)
        elif attributes:
            color_score, color_name = self._calculate_color_from_attributes(attributes)
        else:
            color_score = 0.0
            color_name = "gray"

        features = {
            "color_metaphor": color_name,
            "dimension_count": len(dimensions) + len(attributes),
            "fusion_quality": color_score,
            "hue": data.get("hue", 0.0),
            "saturation": data.get("saturation", 0.0),
            "luminance": data.get("luminance", 0.5),
        }

        explanation = self._generate_explanation(color_score, color_name, features)

        recommendations = [
            "Use color coding to organize related concepts",
            "Consider multidimensional visualization",
        ]

        return PatternDetection(
            pattern_name=self.name,
            detected=color_score >= self.detection_threshold,
            confidence=color_score,
            features=features,
            explanation=explanation,
            recommendations=recommendations,
        )

    def analyze(self, data: dict[str, Any]) -> PatternFeatures:
        """Analyze color features."""
        return PatternFeatures(
            intensity=data.get("saturation", 0.5),
            stability=data.get("color_stability", 0.7),
            frequency=data.get("color_frequency", 0.5),
            duration=data.get("color_duration", 0.0),
            metadata={
                "dominant_hue": data.get("dominant_hue"),
                "palette": data.get("palette", []),
            },
        )

    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate color-based recommendations."""
        return detection.recommendations

    def _calculate_color_from_dimensions(self, dimensions: dict[str, float]) -> tuple[float, str]:
        """Calculate color from dimensional values."""
        if not dimensions:
            return 0.0, "gray"

        # Map dimensions to color space
        # First dimension -> hue
        # Second dimension -> saturation
        # Third dimension -> luminance

        values = list(dimensions.values())

        if len(values) >= 3:
            hue = values[0] % 1.0
            sat = max(0, min(1, values[1]))
            lum = max(0, min(1, values[2]))
            color_name = self._hsl_to_color_name(hue, sat, lum)
        elif len(values) >= 2:
            hue = values[0] % 1.0
            sat = max(0, min(1, values[1]))
            color_name = self._hsl_to_color_name(hue, sat, 0.5)
        else:
            color_name = "gray"

        # Color score based on variance across dimensions
        if len(values) > 1:
            variance = sum((v - sum(values) / len(values)) ** 2 for v in values) / len(values)
            color_score = min(1.0, variance * 2)
        else:
            color_score = 0.0

        return color_score, color_name

    def _calculate_color_from_attributes(self, attributes: dict[str, Any]) -> tuple[float, str]:
        """Calculate color from categorical attributes."""
        # Hash attributes to determine color
        attr_str = str(sorted(attributes.items()))
        hash_val = hash(attr_str) % (360 * 256 * 256)

        hue = (hash_val % 360) / 360.0
        sat = ((hash_val // 360) % 256) / 255.0
        color_name = self._hsl_to_color_name(hue, sat, 0.5)

        # Score based on number of distinct attributes
        color_score = min(1.0, len(attributes) / 5.0)

        return color_score, color_name

    def _hsl_to_color_name(self, hue: float, sat: float, lum: float) -> str:
        """Convert HSL to a basic color name."""
        if sat < 0.1:
            return "white" if lum > 0.9 else "light gray" if lum > 0.5 else "dark gray" if lum > 0.1 else "black"

        # Simple hue mapping
        hue_deg = hue * 360
        if hue_deg < 30 or hue_deg >= 330:
            return "red"
        elif hue_deg < 90:
            return "yellow"
        elif hue_deg < 150:
            return "green"
        elif hue_deg < 210:
            return "cyan"
        elif hue_deg < 270:
            return "blue"
        else:
            return "magenta"

    def _generate_explanation(self, score: float, color: str, features: dict[str, Any]) -> str:
        """Generate human-readable explanation."""
        if score > 0.7:
            return (
                f"Rich {color} pattern - strong multidimensional fusion with {features['dimension_count']} dimensions."
            )
        elif score > 0.4:
            return f"Moderate {color} pattern - some dimensional interplay."
        else:
            return f"Weak color pattern - limited dimensional structure ({color})."


class RepetitionPattern(PatternRecognizer):
    """Detects reoccurring patterns and loops.

    Repetition involves:
    - Repeated sequences or elements
    - Cyclic behavior
    - Recurring patterns
    - Loop detection
    """

    def __init__(self):
        super().__init__("repetition")
        self.pattern_history: deque[str] = deque(maxlen=50)
        self.loop_threshold = 3  # Minimum occurrences for repetition

    async def recognize(self, data: dict[str, Any]) -> PatternDetection:
        """Detect repetitive patterns in data.

        Args:
            data: Dictionary with sequence or pattern data

        Returns:
            PatternDetection for repetition
        """
        sequence = data.get("sequence", [])
        actions = data.get("actions", [])
        patterns = data.get("patterns", [])

        # Use available data source
        if sequence:
            elements = [str(item) for item in sequence]
        elif actions:
            elements = actions
        elif patterns:
            elements = patterns
        else:
            elements = []

        # Update history
        if elements:
            self.pattern_history.extend(elements)

        # Detect repetitions
        repetition_score = self._calculate_repetition_score(list(self.pattern_history))

        # Find specific repeating sequences
        repeating_sequences = self._find_repeating_sequences(list(self.pattern_history))

        features = {
            "repetition_score": repetition_score,
            "unique_elements": len(set(self.pattern_history)),
            "total_elements": len(self.pattern_history),
            "repeating_sequences": repeating_sequences,
        }

        explanation = self._generate_explanation(repetition_score, features)

        recommendations = []
        if repetition_score > 0.7:
            recommendations.append("Strong repetition detected - consider automation")
            recommendations.append("Patterns suggest potential for optimization")
        elif repetition_score > 0.4:
            recommendations.append("Moderate repetition - look for automation opportunities")
        else:
            recommendations.append("Low repetition - diverse behavior detected")

        return PatternDetection(
            pattern_name=self.name,
            detected=repetition_score >= self.detection_threshold,
            confidence=repetition_score,
            features=features,
            explanation=explanation,
            recommendations=recommendations,
        )

    def analyze(self, data: dict[str, Any]) -> PatternFeatures:
        """Analyze repetition features."""
        return PatternFeatures(
            intensity=data.get("repetition_intensity", 0.5),
            stability=data.get("repetition_stability", 0.7),
            frequency=data.get("pattern_frequency", 0.5),
            duration=data.get("loop_duration", 0.0),
            metadata={
                "loop_count": data.get("loop_count", 0),
                "pattern_length": data.get("pattern_length", 0),
            },
        )

    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate repetition-based recommendations."""
        return detection.recommendations

    def _calculate_repetition_score(self, elements: list[str]) -> float:
        """Calculate how repetitive the sequence is."""
        if len(elements) < 3:
            return 0.0

        # Count element frequencies
        counts = Counter(elements)

        # Calculate repetition based on frequency distribution
        most_common = counts.most_common(1)[0] if counts else (None, 0)
        repetition_ratio = most_common[1] / len(elements) if most_common[1] else 0

        # Adjust for number of unique elements
        unique_ratio = 1.0 - (len(counts) / len(elements))

        return (repetition_ratio + unique_ratio) / 2.0

    def _find_repeating_sequences(self, elements: list[str]) -> list[dict[str, Any]]:
        """Find sequences that repeat."""
        if len(elements) < 4:
            return []

        repeating = []

        # Check for sequences of length 2 and 3
        for seq_len in [2, 3]:
            if len(elements) < seq_len * 2:
                continue

            for i in range(len(elements) - seq_len + 1):
                seq = tuple(elements[i : i + seq_len])

                # Look for this sequence elsewhere
                for j in range(i + seq_len, len(elements) - seq_len + 1):
                    if tuple(elements[j : j + seq_len]) == seq:
                        repeating.append(
                            {
                                "sequence": " ".join(seq),
                                "start_indices": [i, j],
                                "length": seq_len,
                            }
                        )
                        break

        return repeating[:10]  # Limit results

    def _generate_explanation(self, score: float, features: dict[str, Any]) -> str:
        """Generate human-readable explanation."""
        if score > 0.8:
            return f"Strong repetition - {features['total_elements'] - features['unique_elements']} of {features['total_elements']} elements are repeats."
        elif score > 0.6:
            return "Moderate repetition - some patterns repeating regularly."
        elif score > 0.4:
            return "Mild repetition - occasional patterns detected."
        else:
            return "Low repetition - behavior is mostly unique."


class DeviationPattern(PatternRecognizer):
    """Detects unexpected changes and anomalies.

    Deviation involves:
    - Unexpected values or events
    - Anomalies in patterns
    - Statistical outliers
    - Behavioral shifts
    """

    def __init__(self):
        super().__init__("deviation")
        self.baseline_window = 20
        self.value_history: deque[float] = deque(maxlen=self.baseline_window * 2)

    async def recognize(self, data: dict[str, Any]) -> PatternDetection:
        """Detect deviations from expected patterns.

        Args:
            data: Dictionary with value or sequence data

        Returns:
            PatternDetection for deviation
        """
        values = data.get("values", [])
        current_value = data.get("current_value")
        sequence = data.get("sequence", [])

        # Get values to analyze
        if values:
            analysis_values = values
        elif current_value is not None:
            analysis_values = [current_value]
        elif sequence:
            # Try to extract numeric values
            try:
                analysis_values = [float(x) for x in sequence if isinstance(x, (int, float))]
            except (ValueError, TypeError):
                analysis_values = []
        else:
            analysis_values = []

        # Update history
        if analysis_values:
            self.value_history.extend(analysis_values)

        # Detect deviations
        deviation_score, anomalies = self._detect_deviations(list(self.value_history))

        features = {
            "deviation_score": deviation_score,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "baseline_mean": (
                sum(list(self.value_history)[-self.baseline_window :])
                / min(self.baseline_window, len(self.value_history))
                if self.value_history
                else 0.0
            ),
        }

        explanation = self._generate_explanation(deviation_score, features)

        recommendations = []
        if deviation_score > 0.7:
            recommendations.append("Significant deviation detected - investigate anomalies")
            recommendations.append("Consider whether this represents a new pattern or error")
        elif deviation_score > 0.4:
            recommendations.append("Mild deviation - monitor for consistency")
        else:
            recommendations.append("No significant deviations - behavior is stable")

        return PatternDetection(
            pattern_name=self.name,
            detected=deviation_score >= self.detection_threshold,
            confidence=deviation_score,
            features=features,
            explanation=explanation,
            recommendations=recommendations,
        )

    def analyze(self, data: dict[str, Any]) -> PatternFeatures:
        """Analyze deviation features."""
        return PatternFeatures(
            intensity=data.get("deviation_intensity", 0.5),
            stability=data.get("deviation_stability", 0.7),
            frequency=data.get("anomaly_frequency", 0.5),
            duration=data.get("deviation_duration", 0.0),
            metadata={
                "anomaly_type": data.get("anomaly_type"),
                "shift_direction": data.get("shift_direction"),
            },
        )

    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate deviation-based recommendations."""
        return detection.recommendations

    def _detect_deviations(self, values: list[float]) -> tuple[float, list[dict[str, Any]]]:
        """Detect deviations using statistical methods."""
        if len(values) < self.baseline_window:
            return 0.0, []

        # Use first half as baseline
        baseline = values[: self.baseline_window]
        test_values = values[self.baseline_window :]

        # Calculate baseline statistics
        mean = sum(baseline) / len(baseline)
        std_dev = math.sqrt(sum((x - mean) ** 2 for x in baseline) / len(baseline))

        # Detect anomalies (more than 2 standard deviations)
        anomalies = []
        for i, val in enumerate(test_values):
            z_score = abs((val - mean) / std_dev) if std_dev > 0 else 0
            if z_score > 2.0:
                anomalies.append(
                    {
                        "index": self.baseline_window + i,
                        "value": val,
                        "expected": mean,
                        "z_score": z_score,
                    }
                )

        # Deviation score based on anomaly proportion
        deviation_score = min(1.0, len(anomalies) / len(test_values) * 3) if len(test_values) > 0 else 0.0

        return deviation_score, anomalies

    def _generate_explanation(self, score: float, features: dict[str, Any]) -> str:
        """Generate human-readable explanation."""
        if score > 0.8:
            return f"Major deviation - {features['anomaly_count']} significant anomalies detected."
        elif score > 0.6:
            return "Moderate deviation - some unexpected behavior."
        elif score > 0.4:
            return "Minor deviation - slight variations from baseline."
        else:
            return "No significant deviation - behavior consistent with baseline."


class CausePattern(PatternRecognizer):
    """Infers causal relationships from event sequences.

    Causal patterns involve:
    - Event causation (A causes B)
    - Chain reactions
    - Root cause analysis
    - Causal inference
    """

    def __init__(self):
        super().__init__("cause")
        self.event_graph: dict[str, dict[str, int]] = {}

    async def recognize(self, data: dict[str, Any]) -> PatternDetection:
        """Detect causal patterns in event sequences.

        Args:
            data: Dictionary with event sequence or causal data

        Returns:
            PatternDetection for cause
        """
        events = data.get("events", [])
        causal_links = data.get("causal_links", [])
        data.get("before_after", {})

        # Build causal graph
        if causal_links:
            for link in causal_links:
                cause = link.get("cause")
                effect = link.get("effect")
                if cause and effect:
                    if cause not in self.event_graph:
                        self.event_graph[cause] = {}
                    self.event_graph[cause][effect] = self.event_graph[cause].get(effect, 0) + 1

        elif events and len(events) > 1:
            # Infer causality from sequence
            for i in range(len(events) - 1):
                cause = str(events[i])
                effect = str(events[i + 1])
                if cause not in self.event_graph:
                    self.event_graph[cause] = {}
                self.event_graph[cause][effect] = self.event_graph[cause].get(effect, 0) + 1

        # Calculate causal strength
        causal_score = self._calculate_causal_strength()

        # Find strongest causal chains
        chains = self._find_causal_chains()

        features = {
            "causal_score": causal_score,
            "total_links": sum(len(targets) for targets in self.event_graph.values()),
            "strongest_chains": chains[:5],
        }

        explanation = self._generate_explanation(causal_score, features)

        recommendations = [
            "Analyze causal chains to understand system behavior",
            "Consider interventions at key causal points",
        ]

        return PatternDetection(
            pattern_name=self.name,
            detected=causal_score >= self.detection_threshold,
            confidence=causal_score,
            features=features,
            explanation=explanation,
            recommendations=recommendations,
        )

    def analyze(self, data: dict[str, Any]) -> PatternFeatures:
        """Analyze cause features."""
        return PatternFeatures(
            intensity=data.get("causal_intensity", 0.5),
            stability=data.get("causal_stability", 0.7),
            frequency=data.get("causal_frequency", 0.5),
            duration=data.get("causal_duration", 0.0),
            metadata={
                "root_causes": data.get("root_causes", []),
                "causal_depth": data.get("causal_depth", 0),
            },
        )

    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate cause-based recommendations."""
        return detection.recommendations

    def _calculate_causal_strength(self) -> float:
        """Calculate strength of causal relationships."""
        if not self.event_graph:
            return 0.0

        total_links = sum(len(targets) for targets in self.event_graph.values())
        if total_links == 0:
            return 0.0

        # Calculate link strength based on consistency
        strong_links = 0
        for targets in self.event_graph.values():
            for count in targets.values():
                if count >= 3:  # Strong causation
                    strong_links += 1
                elif count >= 2:  # Moderate causation
                    strong_links += 0.5

        return min(1.0, strong_links / total_links)

    def _find_causal_chains(self, max_length: int = 5) -> list[dict[str, Any]]:
        """Find causal chains in the event graph."""
        chains = []

        # Find starting points (events that are not effects)
        all_effects = set()
        for targets in self.event_graph.values():
            all_effects.update(targets.keys())

        start_events = set(self.event_graph.keys()) - all_effects

        for start in start_events:
            chain = self._build_chain(start, max_length)
            if len(chain) > 1:
                chains.append({"chain": chain, "length": len(chain)})

        # Sort by strength
        chains.sort(key=lambda c: c["length"], reverse=True)

        return chains

    def _build_chain(self, start: str, max_length: int) -> list[str]:
        """Build a causal chain starting from an event."""
        chain = [start]
        current = start

        for _ in range(max_length - 1):
            if current not in self.event_graph:
                break

            # Get most likely next event
            targets = self.event_graph[current]
            if not targets:
                break

            next_event = max(targets.items(), key=lambda x: x[1])[0]
            chain.append(next_event)
            current = next_event

        return chain

    def _generate_explanation(self, score: float, features: dict[str, Any]) -> str:
        """Generate human-readable explanation."""
        if score > 0.7:
            return f"Strong causal patterns - {features['total_links']} causal links detected with clear chains."
        elif score > 0.4:
            return "Moderate causal structure - some predictable relationships."
        else:
            return "Weak causal patterns - relationships are unclear or random."


@dataclass
class TemporalIntent:
    """Parsed temporal intent from a query or context.

    Attributes:
        query: Original temporal query text
        era_type: Type of era (modern, historical, specific_year, range)
        start_year: Start year of the temporal range (if specified)
        end_year: End year of the temporal range (if specified)
        confidence: Confidence in the temporal intent detection (0-1)
    """

    query: str
    era_type: str  # "modern", "historical", "specific_year", "range", "none"
    start_year: int | None
    end_year: int | None
    confidence: float


@dataclass
class TemporalResonance:
    """Temporal resonance between query intent and document.

    Inspired by audio engineering resonance:
    - Q factor: Width of resonance (narrow = specific, wide = general)
    - Damping: How quickly resonance fades (temporal decay)

    Attributes:
        score: Overall resonance score (0-1)
        q_factor: Width of resonance peak (0.1 = narrow, 0.9 = wide)
        distance: Temporal distance from query peak
        decay: Temporal decay factor
        explanation: Human-readable explanation of resonance
    """

    score: float
    q_factor: float
    distance: float
    decay: float
    explanation: str


class TimePattern(PatternRecognizer):
    """Analyzes temporal evolution and trends with Coffee House temporal concepts.

    Time patterns involve:
    - Trends over time
    - Seasonal patterns
    - Growth/decay cycles
    - Temporal dependencies
    - Temporal intent detection (Coffee House concept)
    - Era-based relevance scoring (Coffee House concept)
    - Temporal resonance with Q factor (Coffee House concept)
    """

    # Era-based relevance scores from Coffee House canon
    ERA_RELEVANCE_SCORES = {
        "modern": 0.8,  # Contemporary era
        "historical": 0.9,  # Historical period range
        "specific_year": 0.95,  # Single year match
        "range": 0.85,  # Specific range match
    }

    # Temporal theme detection keywords
    TEMPORAL_KEYWORDS = {
        "history",
        "timeline",
        "evolution",
        "past",
        "future",
        "time",
        "era",
        "period",
        "century",
        "decade",
        "year",
        "chronology",
        "historical",
        "ancient",
        "modern",
        "contemporary",
        "retro",
    }

    def __init__(self):
        super().__init__("time")
        self.time_series: deque[tuple[datetime, float]] = deque(maxlen=100)

    async def recognize(self, data: dict[str, Any]) -> PatternDetection:
        """Detect temporal patterns in time series data.

        Args:
            data: Dictionary with time series or temporal data

        Returns:
            PatternDetection for time
        """
        timestamps = data.get("timestamps", [])
        values = data.get("values", [])
        time_series = data.get("time_series", [])

        # Process input
        if time_series:
            # Already a list of (time, value) tuples
            series = time_series
        elif timestamps and values and len(timestamps) == len(values):
            # Combine timestamps and values
            if isinstance(timestamps[0], str):
                series = [(datetime.fromisoformat(ts), v) for ts, v in zip(timestamps, values, strict=False)]
            else:
                series = [(ts, v) for ts, v in zip(timestamps, values, strict=False)]
        else:
            series = []

        # Update history
        if series:
            self.time_series.extend(series)

        # Analyze temporal patterns
        trend, volatility, seasonality = self._analyze_temporal_patterns(list(self.time_series))

        # Calculate overall time pattern score
        time_score = (abs(trend) + (1 - volatility) + seasonality) / 3.0

        features = {
            "trend": trend,
            "trend_direction": "increasing" if trend > 0.1 else "decreasing" if trend < -0.1 else "stable",
            "volatility": volatility,
            "seasonality": seasonality,
            "time_score": time_score,
        }

        explanation = self._generate_explanation(time_score, features)

        recommendations = []
        if features["trend_direction"] == "increasing":
            recommendations.append("Upward trend detected - plan for growth")
        elif features["trend_direction"] == "decreasing":
            recommendations.append("Downward trend detected - investigate causes")

        if volatility > 0.5:
            recommendations.append("High volatility - consider stabilization strategies")

        if seasonality > 0.5:
            recommendations.append("Seasonal pattern detected - adjust for cycles")

        return PatternDetection(
            pattern_name=self.name,
            detected=time_score >= self.detection_threshold,
            confidence=time_score,
            features=features,
            explanation=explanation,
            recommendations=recommendations,
        )

    def analyze(self, data: dict[str, Any]) -> PatternFeatures:
        """Analyze time features."""
        return PatternFeatures(
            intensity=data.get("trend_intensity", 0.5),
            stability=1.0 - data.get("volatility", 0.3),
            frequency=data.get("seasonal_frequency", 0.5),
            duration=data.get("time_span", 0.0),
            metadata={
                "trend_direction": data.get("trend_direction"),
                "seasonal_period": data.get("seasonal_period"),
            },
        )

    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate time-based recommendations."""
        return detection.recommendations

    def _analyze_temporal_patterns(self, series: list[tuple[datetime, float]]) -> tuple[float, float, float]:
        """Analyze temporal patterns in time series.

        Returns:
            Tuple of (trend, volatility, seasonality)
        """
        if len(series) < 3:
            return 0.0, 0.5, 0.0

        # Extract values
        values = [v for _, v in series]

        # Calculate trend (linear regression slope)
        n = len(values)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(xi * yi for xi, yi in zip(x, values, strict=False))
        sum_x2 = sum(xi * xi for xi in x)

        if sum_x2 - (sum_x**2) / n != 0:
            slope = (sum_xy - (sum_x * sum_y) / n) / (sum_x2 - (sum_x**2) / n)
            # Normalize trend
            trend = math.tanh(slope * 10)  # Scale and normalize to [-1, 1]
        else:
            trend = 0.0

        # Calculate volatility (coefficient of variation)
        mean = sum(values) / n
        std_dev = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if mean != 0 else 0
        volatility = min(1.0, (std_dev / abs(mean)) if mean != 0 else std_dev)

        # Simple seasonality detection (check for periodicity)
        seasonality = self._detect_seasonality(values)

        return trend, volatility, seasonality

    def _detect_seasonality(self, values: list[float], max_period: int = 10) -> float:
        """Detect seasonal patterns using autocorrelation."""
        if len(values) < max_period * 2:
            return 0.0

        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n

        if variance == 0:
            return 0.0

        # Calculate autocorrelation for different periods
        max_autocorr = 0.0
        for period in range(1, min(max_period, n // 2)):
            autocorr = 0.0
            count = 0
            for i in range(n - period):
                autocorr += (values[i] - mean) * (values[i + period] - mean)
                count += 1

            if count > 0:
                autocorr = autocorr / (count * variance)
                max_autocorr = max(max_autocorr, abs(autocorr))

        return max_autocorr

    def _generate_explanation(self, score: float, features: dict[str, Any]) -> str:
        """Generate human-readable explanation."""
        parts = []

        if features["trend_direction"] == "increasing":
            parts.append("Upward trend")
        elif features["trend_direction"] == "decreasing":
            parts.append("Downward trend")
        else:
            parts.append("Stable trend")

        if features["volatility"] > 0.5:
            parts.append("high volatility")
        else:
            parts.append("low volatility")

        if features["seasonality"] > 0.5:
            parts.append("seasonal patterns detected")

        if score > 0.6:
            prefix = "Strong temporal patterns:"
        elif score > 0.3:
            prefix = "Moderate temporal patterns:"
        else:
            prefix = "Weak temporal patterns:"

        return f"{prefix} {', '.join(parts)}."

    # ========== Coffee House Temporal Concepts ==========

    def parse_temporal_intent(self, query: str) -> TemporalIntent:
        """Parse temporal intent from a query (Coffee House concept).

        Detects temporal constraints like:
        - "1950-1960" -> range era
        - "the 80s" -> range era (1980-1989)
        - "2020" -> specific year
        - "modern" or "recent" -> modern era
        - "historical" or "ancient" -> historical era

        Args:
            query: Query text that may contain temporal constraints

        Returns:
            TemporalIntent with parsed temporal information
        """
        import re

        query_lower = query.lower()

        # Check for temporal theme keywords
        has_temporal_theme = any(kw in query_lower for kw in self.TEMPORAL_KEYWORDS)

        if not has_temporal_theme:
            return TemporalIntent(
                query=query,
                era_type="none",
                start_year=None,
                end_year=None,
                confidence=0.0,
            )

        # Pattern 1: Specific year "1950", "2023", etc.
        year_match = re.search(r"\b(19|20)\d{2}\b", query)
        if year_match and not ("-" in query and re.search(r"\b(19|20)\d{2}\s*-\s*(19|20)\d{2}\b", query)):
            year = int(year_match.group())
            return TemporalIntent(
                query=query,
                era_type="specific_year",
                start_year=year,
                end_year=year,
                confidence=0.9 if str(year) in query else 0.7,
            )

        # Pattern 2: Year range "1950-1960", "1980s"
        range_match = re.search(r"\b(19|20)\d{2}\s*-\s*(19|20)\d{2}\b", query)
        if range_match:
            start_year = int(range_match.group().split("-")[0])
            end_year = int(range_match.group().split("-")[1])
            return TemporalIntent(
                query=query,
                era_type="range",
                start_year=start_year,
                end_year=end_year,
                confidence=0.85,
            )

        # Pattern 3: Decade "the 80s", "90s", "00s"
        decade_match = re.search(r"\b(the\s+)?(\d{2})s\b", query_lower)
        if decade_match:
            decade = int(decade_match.group(2))
            if decade < 30:
                # 2000s
                start_year = 2000 + decade
            else:
                # 1900s
                start_year = 1900 + decade
            end_year = start_year + 9
            return TemporalIntent(
                query=query,
                era_type="range",
                start_year=start_year,
                end_year=end_year,
                confidence=0.8,
            )

        # Pattern 4: Modern/contemporary
        if any(kw in query_lower for kw in ["modern", "recent", "current", "today", "nowadays"]):
            return TemporalIntent(
                query=query,
                era_type="modern",
                start_year=2010,
                end_year=2030,
                confidence=0.75,
            )

        # Pattern 5: Historical/ancient
        if any(kw in query_lower for kw in ["historical", "ancient", "past", "old", "vintage"]):
            return TemporalIntent(
                query=query,
                era_type="historical",
                start_year=None,
                end_year=2000,
                confidence=0.7,
            )

        return TemporalIntent(
            query=query,
            era_type="none",
            start_year=None,
            end_year=None,
            confidence=0.5,
        )

    def calculate_era_relevance(
        self,
        temporal_intent: TemporalIntent,
        document_metadata: dict[str, Any],
    ) -> float:
        """Calculate era-based relevance score (Coffee House concept).

        Scores documents based on temporal alignment with query intent.

        Args:
            temporal_intent: Parsed temporal intent from query
            document_metadata: Document metadata with temporal information

        Returns:
            Relevance score (0.0 - 1.0)
        """
        if temporal_intent.era_type == "none":
            return 1.0  # No temporal constraint

        # Extract temporal metadata from document
        doc_year = document_metadata.get("year")
        doc_era = document_metadata.get("era", "unknown")

        # Modern era: documents from last ~15 years
        if temporal_intent.era_type == "modern":
            if doc_year:
                return self.ERA_RELEVANCE_SCORES["modern"] if doc_year >= temporal_intent.start_year else 0.5
            return 0.6 if doc_era == "modern" else 0.3

        # Historical era: older documents
        if temporal_intent.era_type == "historical":
            if doc_year and doc_year < temporal_intent.end_year:
                return self.ERA_RELEVANCE_SCORES["historical"]
            return 0.7 if doc_era in ["historical", "ancient"] else 0.3

        # Specific year: exact match
        if temporal_intent.era_type == "specific_year":
            if doc_year == temporal_intent.start_year:
                return self.ERA_RELEVANCE_SCORES["specific_year"]
            return 0.4  # Partial credit for nearby years

        # Range: documents within range
        if temporal_intent.era_type == "range":
            if doc_year:
                if temporal_intent.start_year <= doc_year <= temporal_intent.end_year:
                    return self.ERA_RELEVANCE_SCORES["range"]
                # Decay for nearby years
                distance = min(
                    abs(doc_year - temporal_intent.start_year),
                    abs(doc_year - temporal_intent.end_year),
                )
                if distance <= 5:
                    return 0.7 - (distance * 0.05)
            return 0.5

        return 0.5  # Default moderate relevance

    def calculate_temporal_resonance(
        self,
        temporal_intent: TemporalIntent,
        document_metadata: dict[str, Any],
        q_factor: float = 0.5,
        damping: float = 0.3,
    ) -> TemporalResonance:
        """Calculate temporal resonance between query and document (Coffee House concept).

        Inspired by audio engineering resonance curves:
        - Resonance Peak: Maximum response at a specific frequency/temporal point
        - Q Factor: Width of resonance (narrow = specific, wide = general)
        - Damping: How quickly resonance fades (temporal decay)

        Args:
            temporal_intent: Parsed temporal intent from query
            document_metadata: Document metadata with temporal information
            q_factor: Width of resonance (0.1 = narrow, 0.9 = wide)
            damping: Damping factor (0.1 = slow decay, 0.5 = fast decay)

        Returns:
            TemporalResonance with score and explanation
        """
        # Extract document temporal information
        doc_year = document_metadata.get("year")
        current_year = datetime.now(UTC).year

        if temporal_intent.era_type == "none" or doc_year is None:
            return TemporalResonance(
                score=1.0,
                q_factor=0.5,
                distance=0.0,
                decay=1.0,
                explanation="No temporal constraints - full resonance.",
            )

        # Calculate temporal distance
        if temporal_intent.era_type == "specific_year":
            target_year = temporal_intent.start_year
        elif temporal_intent.era_type == "range":
            target_year = (temporal_intent.start_year + temporal_intent.end_year) / 2
        elif temporal_intent.era_type == "modern":
            target_year = current_year - 5  # Recent past
        else:  # historical
            target_year = 1990  # Approximate historical peak

        # Normalize distance to 0-1 range (0-100 years span)
        distance = min(abs(doc_year - target_year) / 100.0, 1.0)

        # Resonance curve: Gaussian e^(-distance^2 / (2 * Q_factor^2))
        # Higher Q = narrower resonance peak (more specific)
        resonance = math.exp(-(distance**2) / (2 * (q_factor**2)))

        # Apply damping based on recency for modern queries
        decay = 1.0
        if temporal_intent.era_type == "modern":
            # Recent documents have higher resonance
            years_from_now = current_year - doc_year
            decay = math.exp(-damping * years_from_now / 10.0)
        elif temporal_intent.era_type == "historical":
            # Older documents maintain resonance better
            decay = 1.0 - (damping * 0.2)  # Less decay for historical

        score = resonance * decay

        # Generate explanation
        q_desc = "narrow (specific)" if q_factor < 0.3 else "wide (general)" if q_factor > 0.7 else "moderate"
        explanation = f"Temporal resonance: {score:.2f}. Q-factor: {q_factor:.2f} ({q_desc})."

        if score > 0.8:
            explanation += " Strong temporal alignment."
        elif score > 0.5:
            explanation += " Moderate temporal relevance."
        else:
            explanation += " Low temporal alignment."

        return TemporalResonance(
            score=score,
            q_factor=q_factor,
            distance=distance,
            decay=decay,
            explanation=explanation,
        )

    def filter_by_temporal_relevance(
        self,
        documents: list[dict[str, Any]],
        temporal_intent: TemporalIntent,
        threshold: float = 0.8,
    ) -> list[dict[str, Any]]:
        """Filter documents by temporal relevance (Coffee House concept).

        Removes documents below the temporal relevance threshold.

        Args:
            documents: List of documents with metadata
            temporal_intent: Parsed temporal intent from query
            threshold: Minimum relevance score (default 0.8 from Coffee House)

        Returns:
            Filtered list of documents
        """
        if temporal_intent.era_type == "none":
            return documents  # No filtering needed

        filtered = []
        for doc in documents:
            relevance = self.calculate_era_relevance(temporal_intent, doc.get("metadata", {}))
            if relevance >= threshold:
                filtered.append(doc)

        return filtered

    def detect_temporal_theme(self, text: str) -> dict[str, Any]:
        """Detect if text has temporal themes (Coffee House concept).

        Args:
            text: Text to analyze for temporal content

        Returns:
            Dictionary with temporal theme information
        """
        text_lower = text.lower()

        # Count temporal keywords
        keyword_matches = [kw for kw in self.TEMPORAL_KEYWORDS if kw in text_lower]

        # Detect temporal expressions
        import re

        years = re.findall(r"\b(19|20)\d{2}\b", text)
        decades = re.findall(r"\b(\d{2})s\b", text)
        era_terms = [term for term in ["modern", "historical", "ancient", "contemporary"] if term in text_lower]

        # Calculate theme score
        theme_score = min(1.0, (len(keyword_matches) + len(years) + len(decades) + len(era_terms)) / 5.0)

        return {
            "has_temporal_theme": theme_score > 0.3,
            "theme_score": theme_score,
            "keywords_found": keyword_matches,
            "years_found": years,
            "decades_found": decades,
            "era_terms_found": era_terms,
        }


class CombinationPattern(PatternRecognizer):
    """Composes multiple patterns into composite insights.

    Combination patterns involve:
    - Pattern composition
    - Multi-pattern analysis
    - Pattern interactions
    - Hierarchical pattern structure
    """

    def __init__(self):
        super().__init__("combination")

    async def recognize(self, data: dict[str, Any]) -> PatternDetection:
        """Detect composite patterns from multiple pattern detections.

        Args:
            data: Dictionary with multiple pattern detection results

        Returns:
            PatternDetection for combination
        """
        patterns = data.get("patterns", [])
        pattern_scores = data.get("pattern_scores", {})
        interactions = data.get("interactions", {})

        # Analyze pattern combinations
        if patterns:
            combo_score = self._analyze_combinations(patterns)
        elif pattern_scores:
            combo_score = self._analyze_scores(pattern_scores)
        else:
            combo_score = 0.0

        # Find dominant pattern combinations
        combos = self._find_dominant_combinations(patterns, pattern_scores)

        features = {
            "combination_score": combo_score,
            "pattern_count": len(patterns) or len(pattern_scores),
            "dominant_combinations": combos,
            "interactions": interactions,
        }

        explanation = self._generate_explanation(combo_score, features)

        recommendations = [
            "Consider how patterns interact and reinforce each other",
            "Look for emergent behavior from pattern combinations",
        ]

        return PatternDetection(
            pattern_name=self.name,
            detected=combo_score >= self.detection_threshold,
            confidence=combo_score,
            features=features,
            explanation=explanation,
            recommendations=recommendations,
        )

    def analyze(self, data: dict[str, Any]) -> PatternFeatures:
        """Analyze combination features."""
        return PatternFeatures(
            intensity=data.get("combination_intensity", 0.5),
            stability=data.get("combination_stability", 0.7),
            frequency=data.get("combo_frequency", 0.5),
            duration=data.get("combo_duration", 0.0),
            metadata={
                "pattern_types": data.get("pattern_types", []),
                "emergent_properties": data.get("emergent_properties", []),
            },
        )

    def recommend(self, detection: PatternDetection) -> list[str]:
        """Generate combination-based recommendations."""
        return detection.recommendations

    def _analyze_combinations(self, patterns: list[str]) -> float:
        """Analyze strength of pattern combinations."""
        if not patterns:
            return 0.0

        # More patterns = stronger combination signal
        base_score = min(1.0, len(patterns) / 5.0)

        # Check for diverse pattern types
        pattern_types = {p.split("_")[0] for p in patterns if "_" in p}
        diversity = len(pattern_types) / 9.0  # 9 total patterns

        return (base_score + diversity) / 2.0

    def _analyze_scores(self, scores: dict[str, float]) -> float:
        """Analyze pattern scores."""
        if not scores:
            return 0.0

        # Average of top scores
        sorted_scores = sorted(scores.values(), reverse=True)
        top_scores = sorted_scores[:3]

        return sum(top_scores) / len(top_scores)

    def _find_dominant_combinations(
        self,
        patterns: list[str],
        scores: dict[str, float],
    ) -> list[dict[str, Any]]:
        """Find dominant pattern combinations."""
        combos = []

        # Look for commonly co-occurring patterns
        if patterns:
            from collections import Counter

            pairs = [(patterns[i], patterns[i + 1]) for i in range(len(patterns) - 1)]

            pair_counts = Counter(pairs)
            for (p1, p2), count in pair_counts.most_common(5):
                combos.append(
                    {
                        "patterns": [p1, p2],
                        "frequency": count,
                    }
                )

        # Look for high-score combinations
        if scores:
            high_scores = {k: v for k, v in scores.items() if v > 0.7}
            if len(high_scores) >= 2:
                combos.append(
                    {
                        "patterns": list(high_scores.keys()),
                        "strength": sum(high_scores.values()) / len(high_scores),
                    }
                )

        return combos

    def _generate_explanation(self, score: float, features: dict[str, Any]) -> str:
        """Generate human-readable explanation."""
        if score > 0.7:
            return f"Strong composite patterns - {features['pattern_count']} patterns interacting."
        elif score > 0.4:
            return "Moderate pattern combinations - some emergent behavior."
        else:
            return "Weak pattern interactions - patterns mostly independent."


class PatternMatcher:
    """Orchestrates all 9 pattern recognizers."""

    def __init__(self):
        """Initialize the pattern matcher."""
        self.patterns: dict[str, PatternRecognizer] = {
            "flow": FlowPattern(),
            "spatial": SpatialPattern(),
            "rhythm": RhythmPattern(),
            "color": ColorPattern(),
            "repetition": RepetitionPattern(),
            "deviation": DeviationPattern(),
            "cause": CausePattern(),
            "time": TimePattern(),
            "combination": CombinationPattern(),
        }
        logger.info(f"PatternMatcher initialized with {len(self.patterns)} patterns")

    async def recognize_all(
        self,
        data: dict[str, Any],
        patterns_to_run: list[str] | None = None,
    ) -> dict[str, PatternDetection]:
        """Run all or specified pattern recognizers.

        Args:
            data: Input data for pattern recognition
            patterns_to_run: Optional list of specific patterns to run

        Returns:
            Dictionary mapping pattern names to detection results
        """
        results = {}

        pattern_names = patterns_to_run or list(self.patterns.keys())

        for pattern_name in pattern_names:
            if pattern_name in self.patterns:
                try:
                    result = await self.patterns[pattern_name].recognize(data)
                    results[pattern_name] = result
                except Exception as e:
                    logger.error(f"Error running {pattern_name} pattern: {e}")
                    # Create a fallback detection
                    results[pattern_name] = PatternDetection(
                        pattern_name=pattern_name,
                        detected=False,
                        confidence=0.0,
                        features={},
                        explanation=f"Error: {str(e)}",
                        recommendations=[],
                    )

        return results

    def analyze_pattern(
        self,
        pattern_name: str,
        data: dict[str, Any],
    ) -> PatternFeatures:
        """Analyze features for a specific pattern.

        Args:
            pattern_name: Name of pattern to analyze
            data: Input data

        Returns:
            PatternFeatures for the pattern
        """
        if pattern_name not in self.patterns:
            raise ValueError(f"Unknown pattern: {pattern_name}")

        return self.patterns[pattern_name].analyze(data)

    def get_recommendations(
        self,
        detection: PatternDetection,
    ) -> list[str]:
        """Get recommendations for a pattern detection.

        Args:
            detection: Pattern detection result

        Returns:
            List of recommendations
        """
        pattern_name = detection.pattern_name
        if pattern_name not in self.patterns:
            return detection.recommendations

        return self.patterns[pattern_name].recommend(detection)

    def get_pattern_summary(self, results: dict[str, PatternDetection]) -> dict[str, Any]:
        """Get a summary of pattern detection results.

        Args:
            results: Dictionary of pattern detection results

        Returns:
            Summary dictionary
        """
        detected = [name for name, det in results.items() if det.detected]
        high_confidence = [
            name for name, det in results.items() if det.get_confidence_level() == PatternConfidence.HIGH
        ]

        avg_confidence = sum(det.confidence for det in results.values()) / len(results) if results else 0.0

        return {
            "total_patterns_analyzed": len(results),
            "patterns_detected": len(detected),
            "detected_patterns": detected,
            "high_confidence_patterns": high_confidence,
            "average_confidence": avg_confidence,
            "dominant_pattern": max(results.items(), key=lambda x: x[1].confidence)[0] if results else None,
        }


# Global instance for convenience
_pattern_matcher: PatternMatcher | None = None


def get_pattern_matcher() -> PatternMatcher:
    """Get the global pattern matcher instance.

    Returns:
        Pattern matcher singleton
    """
    global _pattern_matcher
    if _pattern_matcher is None:
        _pattern_matcher = PatternMatcher()
    return _pattern_matcher
