"""Interfaces package (bridges, sensory adapters)."""

from .bridge import QuantumBridge
from .json_parser import JSONParser
from .json_scanner import JSONFileType, JSONScanner
from .metrics_collector import BridgeMetrics, MetricsCollector, SensoryMetrics

try:
    from .sensory import SensoryInput, SensoryProcessor
except ImportError:
    SensoryInput = None  # type: ignore[assignment]
    SensoryProcessor = None  # type: ignore[assignment]

__all__ = [
    "QuantumBridge",
    "SensoryInput",
    "SensoryProcessor",
    "MetricsCollector",
    "BridgeMetrics",
    "SensoryMetrics",
    "JSONScanner",
    "JSONParser",
    "JSONFileType",
]
