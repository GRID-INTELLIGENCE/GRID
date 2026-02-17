"""
Parasite Guard Detector Protocol.

Defines the interface for all Parasite Detectors.
"""

from typing import Any, Protocol, runtime_checkable

from .definitions import ParasiteContext


@runtime_checkable
class ParasiteDetector(Protocol):
    """
    Protocol for a Parasite Detector.

    A detector analyzes a request (or event context) and returns a
    ParasiteContext if a parasitic pattern is detected, or None otherwise.
    """

    async def __call__(self, request: Any) -> ParasiteContext | None:
        """
        Analyze the request/context for parasitic patterns.

        Args:
            request: The request object (FastAPI Request, Event, etc.) or context dict.

        Returns:
            ParasiteContext if detected, None otherwise.
        """
        ...
