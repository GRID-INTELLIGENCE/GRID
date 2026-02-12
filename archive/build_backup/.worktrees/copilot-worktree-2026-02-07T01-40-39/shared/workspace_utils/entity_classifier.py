"""
Entity Classification Module

Migrated from code_local.py - provides entity-attribute classification
with signal vs noise patterns from audio engineering.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


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
    signal_class: Optional[SignalClassification] = None


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
    categories: List[Category] = field(default_factory=list)
    attributes: List[Attribute] = field(default_factory=list)
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
            print(f"⚠️ Low confidence attribute filtered: {attribute.key}={attribute.value} (confidence: {attribute.confidence})")

    def classify_signals(self) -> Dict[SignalClassification, List[Attribute]]:
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

    def to_dict(self) -> Dict:
        """Convert entity to dictionary for JSON serialization (Cascade-friendly)."""
        return {
            'name': self.name,
            'categories': [
                {
                    'name': cat.name,
                    'description': cat.description,
                    'signal_class': cat.signal_class.value if cat.signal_class else None
                }
                for cat in self.categories
            ],
            'attributes': [
                {
                    'key': attr.key,
                    'value': attr.value,
                    'description': attr.description,
                    'confidence': attr.confidence
                }
                for attr in self.attributes
            ],
            'nsr_ratio': self.nsr_ratio,
            'signal_classification': {
                sig_type.value: [attr.key for attr in attrs]
                for sig_type, attrs in self.classify_signals().items()
                if attrs
            }
        }