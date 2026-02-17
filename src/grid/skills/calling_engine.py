"""Automated skill calling with intelligent routing."""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CallStrategy(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


@dataclass
class SkillCallResult:
    skill_id: str
    result: Any
    error: str | None
    execution_time_ms: float
    confidence: float | None


class SkillCallingEngine:
    """Automated skill calling with intelligent routing."""

    def __init__(self, registry: Any | None = None) -> None:
        self._logger = logging.getLogger(__name__)
        if registry is None:
            from .registry import default_registry

            self._registry = default_registry
        else:
            self._registry = registry

    async def call_skill(
        self, skill_id: str, args: dict[str, Any], timeout_ms: int = 30000, retry: bool = True
    ) -> SkillCallResult:
        """Call a single skill with timeout and retry."""
        skill = self._registry.get(skill_id)
        if not skill:
            return SkillCallResult(
                skill_id=skill_id,
                result=None,
                error=f"Skill {skill_id} not found",
                execution_time_ms=0,
                confidence=None,
            )

        start_time = time.time()
        try:
            # Execute with timeout
            # Note: skill.run might be synchronous, so we run in thread
            async with asyncio.timeout(timeout_ms / 1000):
                result = await asyncio.to_thread(skill.run, args)

            return SkillCallResult(
                skill_id=skill_id,
                result=result,
                error=None,
                execution_time_ms=result.get("execution_time_ms", (time.time() - start_time) * 1000),
                confidence=result.get("confidence", None),
            )

        except TimeoutError:
            return SkillCallResult(
                skill_id=skill_id,
                result=None,
                error=f"Timeout after {timeout_ms}ms",
                execution_time_ms=timeout_ms,
                confidence=None,
            )

        except Exception as e:
            if retry:
                self._logger.warning(f"Retrying {skill_id} after error: {e}")
                return await self.call_skill(skill_id, args, timeout_ms, False)
            return SkillCallResult(
                skill_id=skill_id,
                result=None,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
                confidence=None,
            )

    async def call_multiple_skills(
        self, skill_ids: list[str], args: dict[str, Any], strategy: CallStrategy = CallStrategy.PARALLEL
    ) -> dict[str, SkillCallResult]:
        """Call multiple skills with intelligent routing."""
        if strategy == CallStrategy.SEQUENTIAL:
            sequential_results: dict[str, SkillCallResult] = {}
            for skill_id in skill_ids:
                sequential_results[skill_id] = await self.call_skill(skill_id, args)
            return sequential_results

        elif strategy == CallStrategy.PARALLEL:
            tasks = [self.call_skill(skill_id, args) for skill_id in skill_ids]
            parallel_results: list[SkillCallResult] = await asyncio.gather(*tasks)
            return {skill_id: result for skill_id, result in zip(skill_ids, parallel_results, strict=False)}

        else:  # ADAPTIVE
            # Start with parallel, fall back to sequential if needed
            try:
                return await self.call_multiple_skills(skill_ids, args, CallStrategy.PARALLEL)
            except Exception as e:
                self._logger.warning(f"Parallel execution failed, falling back to sequential: {e}")
                return await self.call_multiple_skills(skill_ids, args, CallStrategy.SEQUENTIAL)
