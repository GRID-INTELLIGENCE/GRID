"""
Entity-Attribute Classification System
Integrates audio engineering signal vs noise classification patterns.

References:
- AUDIO_ENGINEERING_CASE_STUDIES.md (e:/grid/docs/skills/)
- AUDIO_ENGINEERING_GUIDE.md (e:/grid/docs/skills/)

Signal Classification Patterns:
1. Timeout spike detection
2. Transient error filtering
3. Performance regression detection
4. Valid execution signal
5. Low confidence outlier filtering
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SignalClassification(Enum):
    """Signal vs Noise classification types from audio engineering."""

    VALID_SIGNAL = "valid_execution_signal"
    TIMEOUT_SPIKE = "timeout_spike_detection"
    TRANSIENT_ERROR = "transient_error_filtering"
    REGRESSION = "performance_regression_detection"
    OUTLIER = "low_confidence_outlier_filtering"
    NOISE = "noise"


class ConfidenceLevel(Enum):
    """Confidence levels for signal classification (NSR-based)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Category:
    """
    Represents a category or type of entity.

    Audio Engineering Context:
    - Maps to classification domains (signal, noise, anomaly)
    - Determines NSR (Noise-to-Signal Ratio) tracking strategy
    """

    name: str
    description: str = ""
    signal_class: SignalClassification | None = None


@dataclass
class Attribute:
    """
    Represents an attribute or property of an entity.

    Audio Engineering Context:
    - key: Signal characteristic (amplitude, frequency, duration)
    - value: Measured/detected value
    - confidence: Signal reliability metric (0.0 to 1.0)
    """

    key: str
    value: Any
    description: str = ""
    confidence: float = 1.0  # NSR-based confidence score

    def is_valid_signal(self) -> bool:
        """Determine if attribute represents valid signal vs noise."""
        return self.confidence >= 0.7  # Threshold for valid execution signal


@dataclass
class Entity:
    """
    Represents an entity with categories and attributes.

    Audio Engineering Integration:
    - Applies signal filtering logic to entity classification
    - Tracks performance metrics and regression detection
    - Filters outliers based on confidence thresholds
    """

    name: str
    categories: list[Category] = field(default_factory=list)
    attributes: list[Attribute] = field(default_factory=list)
    nsr_ratio: float = 0.0  # Noise-to-Signal Ratio tracking

    def add_category(self, category: Category):
        """Add category with signal classification context."""
        self.categories.append(category)

    def add_attribute(self, attribute: Attribute):
        """
        Add attribute with signal validity check.
        Filters low confidence outliers.
        """
        if attribute.is_valid_signal():
            self.attributes.append(attribute)
        else:
            # Low confidence outlier filtering case study pattern
            print(
                f"⚠️ Low confidence attribute filtered: {attribute.key}={attribute.value} (confidence: {attribute.confidence})"
            )

    def classify_signals(self) -> dict[SignalClassification, list[Attribute]]:
        """
        Classify entity attributes using audio engineering patterns.

        Implements case study patterns:
        1. Valid execution signal: high confidence attributes
        2. Timeout spike detection: anomalous amplitude values
        3. Transient error filtering: temporary inconsistencies
        4. Performance regression: degradation trends
        5. Outlier filtering: low confidence values
        """
        classification = {cls: [] for cls in SignalClassification}

        for attr in self.attributes:
            if attr.confidence >= 0.85:
                classification[SignalClassification.VALID_SIGNAL].append(attr)
            elif isinstance(attr.value, (int, float)) and attr.value > 1000:
                # Case study: timeout spike detection pattern
                classification[SignalClassification.TIMEOUT_SPIKE].append(attr)
            elif attr.confidence < 0.7:
                # Case study: low confidence outlier filtering pattern
                classification[SignalClassification.OUTLIER].append(attr)
            else:
                classification[SignalClassification.VALID_SIGNAL].append(attr)

        return classification

    def calculate_nsr(self) -> float:
        """
        Calculate Noise-to-Signal Ratio (NSR).
        NSR tracking from AUDIO_ENGINEERING_GUIDE.md
        """
        if not self.attributes:
            return 0.0

        noise_count = sum(1 for attr in self.attributes if attr.confidence < 0.7)
        signal_count = len(self.attributes) - noise_count

        self.nsr_ratio = noise_count / (signal_count or 1)
        return self.nsr_ratio

    def detect_regression(self, baseline: "Entity") -> bool:
        """
        Detect performance regression (case study pattern).
        Compares current entity metrics against baseline.
        """
        current_nsr = self.calculate_nsr()
        baseline_nsr = baseline.calculate_nsr()

        regression_detected = current_nsr > (baseline_nsr * 1.1)  # 10% threshold

        if regression_detected:
            print(f"📉 Performance regression detected: NSR increased from {baseline_nsr:.2f} to {current_nsr:.2f}")

        return regression_detected


# Example Usage integrating audio engineering patterns
if __name__ == "__main__":
    # Define Categories with signal classification
    pokemon_category = Category(
        name="Pokémon",
        description="A creature with unique abilities in the Pokémon world.",
        signal_class=SignalClassification.VALID_SIGNAL,
    )

    # Define Attributes with confidence scores (NSR-based)
    time_travel_attr = Attribute(
        key="ability",
        value="time travel",
        description="Can travel through time.",
        confidence=0.95,  # High confidence: valid signal
    )
    grass_type_attr = Attribute(
        key="type",
        value="Grass",
        description="Primary type of the Pokémon.",
        confidence=0.92,  # High confidence: valid signal
    )
    psychic_type_attr = Attribute(
        key="type",
        value="Psychic",
        description="Secondary type of the Pokémon.",
        confidence=0.88,  # High confidence: valid signal
    )

    # Low confidence attribute (outlier filtering case study)
    anomaly_attr = Attribute(
        key="unknown_metric",
        value=9999,
        description="Anomalous reading",
        confidence=0.45,  # Low confidence: will be filtered as outlier
    )

    # Create baseline entity
    celebi_baseline = Entity(name="Celebi (Baseline)")
    celebi_baseline.add_category(pokemon_category)
    celebi_baseline.add_attribute(time_travel_attr)
    celebi_baseline.add_attribute(grass_type_attr)
    celebi_baseline.add_attribute(psychic_type_attr)

    # Create current entity with low confidence attributes
    celebi_current = Entity(name="Celebi (Current)")
    celebi_current.add_category(pokemon_category)
    celebi_current.add_attribute(time_travel_attr)
    celebi_current.add_attribute(grass_type_attr)
    celebi_current.add_attribute(psychic_type_attr)
    celebi_current.add_attribute(anomaly_attr)  # Will be filtered

    # Demonstrate audio engineering patterns
    print("=" * 60)
    print("Entity: Celebi (Pokémon Classification)")
    print("=" * 60)

    print(f"/n✅ Entity created with {len(celebi_current.attributes)} valid attributes")

    # Signal classification (case study patterns)
    classifications = celebi_current.classify_signals()
    print("/n📊 Signal Classification:")
    for signal_type, attrs in classifications.items():
        if attrs:
            print(f"   {signal_type.value}: {len(attrs)} attributes")

    # NSR calculation
    nsr = celebi_current.calculate_nsr()
    print(f"/n📈 Noise-to-Signal Ratio (NSR): {nsr:.2f}")

    # Regression detection
    print("/n🔍 Performance Regression Analysis:")
    celebi_current.detect_regression(celebi_baseline)

    print(f"\n{celebi_current}")
