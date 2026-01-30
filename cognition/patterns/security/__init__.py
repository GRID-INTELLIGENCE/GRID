"""Pattern Security Module.

Provides security monitoring and countermeasures for cognitive patterns.
Implements the "Behind the Curtain" defense system with:
- Cognitive fingerprinting
- Burst pattern detection
- Recursive countermeasures
- Silent failure modes
"""

from cognition.patterns.security.cognitive_fingerprint import (
    ReinforcementSignature,
    get_cognitive_fingerprint,
)
from cognition.patterns.security.null_wrapper import (
    _wrapped_reinforce,
    _wrapped_signal_create,
)
from cognition.patterns.security.pattern_deviation import (
    PatternDeviationMonitor,
    get_pattern_deviation_monitor,
)
from cognition.patterns.security.recursive_countermeasure import (
    RecursiveCountermeasure,
    apply_countermeasure,
)
from cognition.patterns.security.reinforcement_monitor import (
    ReinforcementMonitor,
    get_reinforcement_monitor,
)
from cognition.patterns.security.velocity_anomaly import (
    VelocityAnomalyDetector,
    get_velocity_anomaly_detector,
)

__all__ = [
    # Deception layer (null wrappers)
    "_wrapped_reinforce",
    "_wrapped_signal_create",
    # Cognitive fingerprinting
    "get_cognitive_fingerprint",
    "ReinforcementSignature",
    # Monitoring layer
    "ReinforcementMonitor",
    "get_reinforcement_monitor",
    "PatternDeviationMonitor",
    "get_pattern_deviation_monitor",
    "VelocityAnomalyDetector",
    "get_velocity_anomaly_detector",
    # Countermeasure layer
    "RecursiveCountermeasure",
    "apply_countermeasure",
]
