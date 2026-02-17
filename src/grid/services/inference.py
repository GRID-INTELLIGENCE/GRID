import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any

from ..models.inference import InferenceRequest, InferenceResponse


@dataclass
class ProcessingResult:
    result: str
    tokens_used: int
    processing_time: float
    model: str
    metadata: dict[str, Any] | None = None


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "y", "on"}


def _is_production_environment() -> bool:
    env = (
        os.getenv("MOTHERSHIP_ENVIRONMENT")
        or os.getenv("GRID_ENVIRONMENT")
        or os.getenv("ENVIRONMENT")
        or os.getenv("ENV")
        or "development"
    )
    return env.strip().lower() in {"production", "prod"}


class InferenceService:
    """Service for handling inference requests"""

    def __init__(self, model_loader=None, cache_service=None):
        self.model_loader = model_loader
        self.cache = cache_service
        allow_placeholder_in_production = _parse_bool(
            os.getenv("INFERENCE_ALLOW_PLACEHOLDER_IN_PRODUCTION"),
            False,
        )
        if _is_production_environment() and not allow_placeholder_in_production:
            raise RuntimeError(
                "grid.services.inference uses placeholder providers and is forbidden in production. "
                "Use grid.services.inference_harness or explicitly allow with INFERENCE_ALLOW_PLACEHOLDER_IN_PRODUCTION=true."
            )

        self.models = {
            "default": "gpt-3.5-turbo",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "gpt-4": "gpt-4",
            "claude-2": "claude-2",
            "local-model": "local-model",
        }

    async def process(self, request: InferenceRequest) -> InferenceResponse:
        """Process an inference request"""
        start_time = time.time()

        # Validate input
        if not self._validate_request(request):
            raise ValueError("Invalid inference request")

        # Check cache if available
        if self.cache:
            cache_key = self._generate_cache_key(request)
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return InferenceResponse(**cached_result)

        # Process the request
        try:
            result = await self._call_model(request)
            processing_time = time.time() - start_time

            response_metadata = dict(result.metadata or {})
            response_metadata.setdefault("origin", "placeholder")
            response_metadata.setdefault("simulated", True)

            response = InferenceResponse(
                result=result.result,
                model=result.model,
                tokens_used=result.tokens_used,
                processing_time=processing_time,
                metadata=response_metadata,
            )

            # Cache the result
            if self.cache:
                await self.cache.set(cache_key, response.dict())

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            raise RuntimeError(f"Inference failed after {processing_time:.2f}s: {str(e)}")

    async def _call_model(self, request: InferenceRequest) -> ProcessingResult:
        """Call the appropriate model for inference"""
        model_name = self.models.get(request.model, self.models["default"])

        # Mock implementation - in real system this would call actual models
        if model_name == "local-model":
            result = await self._call_local_model(request)
        elif model_name.startswith("gpt"):
            result = await self._call_openai_model(request)
        elif model_name.startswith("claude"):
            result = await self._call_anthropic_model(request)
        else:
            result = await self._call_default_model(request)

        return result

    async def _call_local_model(self, request: InferenceRequest) -> ProcessingResult:
        """Call local model (placeholder)"""
        await asyncio.sleep(0.5)  # Simulate processing time
        return ProcessingResult(
            result=f"Local model response to: {request.prompt[:50]}...",
            tokens_used=len(request.prompt.split()) * 2,
            processing_time=0.5,
            model="local-model",
            metadata={
                "origin": "placeholder",
                "provider": "local-model",
                "simulated": True,
            },
        )

    async def _call_openai_model(self, request: InferenceRequest) -> ProcessingResult:
        """Call OpenAI model (placeholder)"""
        await asyncio.sleep(1.0)  # Simulate API call
        return ProcessingResult(
            result=f"OpenAI {request.model} response to: {request.prompt[:50]}...",
            tokens_used=len(request.prompt.split()) * 3,
            processing_time=1.0,
            model=request.model,
            metadata={
                "origin": "placeholder",
                "provider": "openai",
                "simulated": True,
            },
        )

    async def _call_anthropic_model(self, request: InferenceRequest) -> ProcessingResult:
        """Call Anthropic model (placeholder)"""
        await asyncio.sleep(0.8)  # Simulate API call
        return ProcessingResult(
            result=f"Anthropic Claude response to: {request.prompt[:50]}...",
            tokens_used=len(request.prompt.split()) * 2,
            processing_time=0.8,
            model=request.model,
            metadata={
                "origin": "placeholder",
                "provider": "anthropic",
                "simulated": True,
            },
        )

    async def _call_default_model(self, request: InferenceRequest) -> ProcessingResult:
        """Call default model (placeholder)"""
        await asyncio.sleep(0.3)  # Simulate processing time
        return ProcessingResult(
            result=f"Default model response to: {request.prompt[:50]}...",
            tokens_used=len(request.prompt.split()) * 2,
            processing_time=0.3,
            model="default",
            metadata={
                "origin": "placeholder",
                "provider": "default",
                "simulated": True,
            },
        )

    def _validate_request(self, request: InferenceRequest) -> bool:
        """Validate inference request"""
        if not request.prompt or len(request.prompt.strip()) == 0:
            return False
        if request.max_tokens and request.max_tokens > 4000:
            return False
        if request.temperature and not (0.0 <= request.temperature <= 2.0):
            return False
        return True

    def _generate_cache_key(self, request: InferenceRequest) -> str:
        """Generate cache key for request"""
        key_parts = [request.prompt, str(request.model), str(request.max_tokens), str(request.temperature)]
        return "|".join(key_parts)
