"""Quantized architecture with locomotion support.

This module provides a precise, dynamic, quantized architecture that enables
locomotion and state transitions in discrete steps.
"""

from .locomotion import LocomotionEngine, MovementDirection, MovementResult
from .quantizer import QuantizationLevel, QuantizedState, Quantizer
from .quantum_engine import QuantumEngine

__all__ = [
    "Quantizer",
    "QuantizationLevel",
    "QuantizedState",
    "LocomotionEngine",
    "MovementDirection",
    "MovementResult",
    "QuantumEngine",
]
