"""Extended cognitive sensory support.

This module provides support for extended cognitive senses beyond visual and audio,
including smell, touch, and taste.
"""

from .sensory_input import SensoryInput, SensoryType
from .sensory_processor import SensoryProcessor
from .sensory_store import SensoryStore

__all__ = [
    "SensoryInput",
    "SensoryType",
    "SensoryProcessor",
    "SensoryStore",
]
