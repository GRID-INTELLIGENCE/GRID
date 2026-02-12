"""Recovery Engine for GRID Agentic System.

Executes appropriate recovery strategies for classified errors, including
retries with backoff, model fallbacks, and graceful degradation.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from .error_classifier import ErrorClassifier

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RecoveryStrategy(str, Enum):
    """Available recovery strategies."""

    RETRY_WITH_BACKOFF = "retry_backoff"
    FALLBACK_MODEL = "fallback_model"
    DEGRADE_SERVICE = "degrade_service"
    SKIP_AND_CONTINUE = "skip_continue"
    ABORT = "abort"


class RecoveryResult:
    """Result of a recovery attempt."""

    def __init__(self, success: bool, final_result: Any = None, attempts: int = 0, error: Exception | None = None):
        self.success = success
        self.final_result = final_result
        self.attempts = attempts
        self.error = error


class RecoveryEngine:
    """Orchestrates recovery from execution failures."""

    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0  # seconds

    async def execute_with_recovery(
        self,
        task_fn: Callable[..., T],
        *args: Any,
        max_attempts: int | None = None,
        fallback_fn: Callable[..., T] | None = None,
        **kwargs: Any,
    ) -> T:
        """Execute a function with automatic recovery based on error classification."""
        last_error = None
        attempts = 0
        limit = max_attempts or self.max_retries

        while attempts < limit:
            try:
                attempts += 1
                return await task_fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_context = ErrorClassifier.classify(e)

                logger.warning(
                    f"🔄 Recovery attempt {attempts}/{limit} for error {error_context.error_type} "
                    f"({error_context.category.value}). Strategy: {error_context.fallback_strategy}"
                )

                if not error_context.recoverable or attempts >= limit:
                    break

                # Apply recovery strategy
                if error_context.fallback_strategy in ("retry", "retry_with_backoff"):
                    delay = self.base_delay * (2 ** (attempts - 1))
                    await asyncio.sleep(delay)
                    continue

                elif error_context.fallback_strategy == "fix_and_retry":
                    # Placeholder for intelligent fix logic
                    await asyncio.sleep(self.base_delay)
                    continue

                else:
                    # Strategy not handled here, break and let fallback handle it
                    break

        # If we reach here, all retries failed
        if fallback_fn:
            logger.info("⚡ Executing fallback strategy...")
            return await fallback_fn(*args, **kwargs)

        raise last_error
