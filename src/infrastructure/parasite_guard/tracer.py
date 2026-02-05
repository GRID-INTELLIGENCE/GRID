"""
Source tracing for parasite origin identification.

Walks the call stack to locate the seed function/module
that generated the original parasitic call.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .models import SourceMap, ParasiteContext

logger = logging.getLogger(__name__)


class SourceTraceResolver:
    """
    Resolves the source of a parasitic call.

    Walks the call stack to find:
    - The originating module
    - The function/method that created the request
    - The line number
    - The package name

    Uses heuristics to skip:
    - Library code (site-packages)
    - Framework code
    - Parasite guard internals
    """

    # Patterns to skip when tracing
    SKIP_PATTERNS = [
        "site-packages",
        "dist-packages",
        "parasite_guard",
        "fastapi",
        "starlette",
        "sqlalchemy",
        "uvicorn",
    ]

    def __init__(self, config: Any):
        self.config = config
        self._resolution_cache: Dict[str, SourceMap] = {}

    async def resolve(self, context: ParasiteContext) -> Optional[SourceMap]:
        """
        Resolve the source of the parasitic call.

        Args:
            context: ParasiteContext from detection

        Returns:
            SourceMap if successful, None if unable to resolve
        """
        # Check cache
        cache_key = f"{context.component}:{context.pattern}:{context.rule}"
        if cache_key in self._resolution_cache:
            return self._resolution_cache[cache_key]

        # Extract stack
        stack = traceback.extract_stack()

        # Walk backwards to find source
        for frame in reversed(stack):
            source_map = self._frame_to_source_map(frame)

            if source_map:
                # Cache and return
                self._resolution_cache[cache_key] = source_map
                return source_map

        # Unable to resolve
        logger.warning(
            f"Unable to resolve source for parasite {context.id}",
            extra={"parasite_id": str(context.id)},
        )
        return None

    def _frame_to_source_map(self, frame: traceback.FrameSummary) -> Optional[SourceMap]:
        """
        Convert a stack frame to a SourceMap.

        Returns None if frame should be skipped.
        """
        filename = frame.filename

        # Skip if filename matches skip patterns
        if any(pattern in filename for pattern in self.SKIP_PATTERNS):
            return None

        # Skip if it's a Python standard library file
        if filename.startswith(os.path.dirname(os.__file__)):
            return None

        # Extract package name
        package = self._detect_package(filename)

        # Get class name if this is a method
        class_name = self._detect_class_name(frame)

        return SourceMap(
            module=self._get_module_name(filename),
            function=frame.name,
            line=frame.lineno,
            file=filename,
            package=package,
            class_name=class_name,
        )

    def _get_module_name(self, filename: str) -> str:
        """Extract module name from file path."""
        try:
            path = Path(filename)

            # Remove file extension
            stem = path.stem

            # Get relative path from src if applicable
            parts = path.parts

            # Find index of "src" or similar
            for i, part in enumerate(parts):
                if part in ("src", "lib", "app"):
                    if i + 1 < len(parts):
                        # Reconstruct module from remaining parts
                        module_parts = parts[i + 1 : -1] + [stem]
                        return ".".join(module_parts)

            # Fallback to stem
            return stem

        except Exception:
            return "unknown"

    def _detect_package(self, filename: str) -> Optional[str]:
        """
        Detect the package name from the file path.

        Looks for pyproject.toml or setup.py in parent directories.
        """
        try:
            path = Path(filename).parent

            for _ in range(5):  # Look up 5 levels
                if (path / "pyproject.toml").exists() or (path / "setup.py").exists():
                    return path.name

                path = path.parent
                if path == path.parent:  # Reached root
                    break

            return None

        except Exception:
            return None

    def _detect_class_name(self, frame: traceback.FrameSummary) -> Optional[str]:
        """
        Try to detect the class name if this is a method call.

        This is a heuristic; may not always be accurate.
        """
        try:
            # Get current frame's locals
            current_frame = inspect.currentframe()
            if current_frame:
                # Look for 'self' in locals
                if "self" in current_frame.f_locals:
                    obj = current_frame.f_locals["self"]
                    return obj.__class__.__name__

                # Look for 'cls' in classmethod
                elif "cls" in current_frame.f_locals:
                    obj = current_frame.f_locals["cls"]
                    return obj.__name__

            return None

        except Exception:
            return None

    def clear_cache(self) -> None:
        """Clear the resolution cache."""
        self._resolution_cache.clear()


@asynccontextmanager
async def trace_action(resolver: SourceTraceResolver, phase: str, metadata: Dict[str, Any]):
    """
    Context manager for tracing a phase of parasite handling.

    Usage:
        async with trace_action(resolver, "detection", {"key": "value"}):
            # Do detection work
            pass
    """
    start_time = datetime.now(timezone.utc)

    try:
        logger.debug(f"Starting trace phase: {phase}", extra={"phase": phase, "metadata": metadata})
        yield
    finally:
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        logger.debug(
            f"Completed trace phase: {phase}",
            extra={
                "phase": phase,
                "duration_ms": duration_ms,
                "metadata": metadata,
            },
        )
