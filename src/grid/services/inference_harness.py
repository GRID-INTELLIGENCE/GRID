"""
GRID Inference Harness
Tiered inference provider with automated fallback and environment awareness.
Part of the Sovereign Tier architecture.
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# Configure logger
logger = logging.getLogger("grid.inference")


class ProviderType(Enum):
    """Supported inference providers."""

    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"
    TRANSFORMERS = "transformers"
    MOCK = "mock"


@dataclass
class InferenceResult:
    """Standardized result from any inference provider."""

    content: str
    model: str
    provider: ProviderType
    latency_ms: float
    usage: dict[str, int]


@runtime_checkable
class InferenceProvider(Protocol):
    """Protocol defining the interface for inference providers."""

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult: ...
    def is_available(self) -> bool: ...


class InferenceHarness:
    """
    Tiered orchestrator for model inference.
    Implements the Mastication Protocol's Elasticity requirement.
    """

    def __init__(self) -> None:
        """Initialize the harness with default priorities."""
        self.providers: dict[ProviderType, InferenceProvider] = {}
        self.priority: list[ProviderType] = [ProviderType.OLLAMA, ProviderType.LLAMACPP, ProviderType.TRANSFORMERS]
        self._setup_defaults()

    def _setup_defaults(self) -> None:
        """Configures default providers based on environment."""
        # Ollama
        self.providers[ProviderType.OLLAMA] = OllamaProvider()

        # LlamaCPP (EUFLE Sync) - configured via environment variables
        # Required env vars: EUFLE_ROOT or LLAMACPP_MODEL_PATH, and LLAMACPP_CLI_PATH
        eufle_root_str = os.environ.get("EUFLE_ROOT", "")
        gguf_model = os.environ.get("LLAMACPP_MODEL_PATH", "")
        cli_path = os.environ.get("LLAMACPP_CLI_PATH", "")

        gguf_path = ""
        if eufle_root_str:
            eufle_root = Path(eufle_root_str)
            if eufle_root.exists():
                # Use EUFLE root to find model
                default_gguf = eufle_root / "models" / "TinyLlama-1.1B-32k-f16.gguf"
                gguf_path = gguf_model if gguf_model else str(default_gguf)
        elif gguf_model:
            gguf_path = gguf_model
        else:
            logger.debug("LlamaCPP not configured. Set EUFLE_ROOT or LLAMACPP_MODEL_PATH environment variable.")

        if gguf_path and cli_path:
            self.providers[ProviderType.LLAMACPP] = LlamaCPPProvider(gguf_path, cli_path)
        elif gguf_path or cli_path:
            logger.warning("LlamaCPP partially configured. Need both LLAMACPP_MODEL_PATH and LLAMACPP_CLI_PATH.")

        # Mock (Always available for testing)
        self.providers[ProviderType.MOCK] = MockProvider()

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult:
        """
        Generates a response using the best available provider.

        Args:
            prompt: The text prompt for the model.
            **kwargs: Additional generation parameters (max_tokens, temperature, etc.)

        Returns:
            InferenceResult from the first successful provider.
        """
        for provider_type in self.priority:
            provider = self.providers.get(provider_type)
            if provider and provider.is_available():
                try:
                    logger.info(f"Attempting generation with {provider_type.value}...")
                    return await provider.generate(prompt, **kwargs)
                except Exception as e:
                    logger.warning(f"Provider {provider_type.value} failed: {e}")
                    continue

        # Ultimate fallback to Mock if all else fails (for dev stability)
        mock = self.providers.get(ProviderType.MOCK)
        if mock:
            return await mock.generate(prompt, **kwargs)

        raise RuntimeError("No inference providers available")


class OllamaProvider:
    """Ollama-based inference provider."""

    def __init__(self, model: str = "llama3.2:3b") -> None:
        self.model = model
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/api/generate")

    def is_available(self) -> bool:
        try:
            import requests  # type: ignore[import-untyped]

            health_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/tags"
            response = requests.get(health_url, timeout=1)
            return response.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult:
        """Executes generation via Ollama REST API."""
        import time

        import requests  # type: ignore[import-untyped]

        start_time = time.perf_counter()

        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 512),
            },
        }

        response = requests.post(self.base_url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()

        latency = (time.perf_counter() - start_time) * 1000

        return InferenceResult(
            content=data.get("response", ""),
            model=self.model,
            provider=ProviderType.OLLAMA,
            latency_ms=latency,
            usage={"prompt_tokens": data.get("prompt_eval_count", 0), "completion_tokens": data.get("eval_count", 0)},
        )


class LlamaCPPProvider:
    """LlamaCPP-based inference provider using CLI bridge."""

    def __init__(self, model_path: str, cli_path: str) -> None:
        self.model_path = model_path
        self.cli_path = cli_path

    def is_available(self) -> bool:
        return Path(self.model_path).exists() and Path(self.cli_path).exists()

    def _win_to_wsl(self, path: str) -> str:
        """Convert Windows path to WSL path if needed."""
        if os.name == "nt" and path and path[1] == ":":
            drive = path[0].lower()
            rest = path[2:].replace("\\", "/")
            return f"/mnt/{drive}{rest}"
        return path

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult:
        """Executes generation via llama-cli bridge."""
        import time

        start_time = time.perf_counter()

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as tf:
            tf.write(prompt)
            prompt_file = tf.name

        wsl_model = self._win_to_wsl(self.model_path)
        wsl_prompt = self._win_to_wsl(prompt_file)

        cmd = [
            "wsl",
            self.cli_path,
            "-m",
            wsl_model,
            "-f",
            wsl_prompt,
            "-n",
            str(kwargs.get("max_tokens", 256)),
            "--temp",
            str(kwargs.get("temperature", 0.7)),
        ]

        try:
            process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = await process.communicate()
            content = stdout.decode().strip()
        finally:
            os.unlink(prompt_file)

        latency = (time.perf_counter() - start_time) * 1000

        return InferenceResult(
            content=content,
            model=Path(self.model_path).stem,
            provider=ProviderType.LLAMACPP,
            latency_ms=latency,
            usage={"prompt_tokens": len(prompt.split()), "completion_tokens": len(content.split())},
        )


class TransformersProvider:
    """HuggingFace Transformers-based inference provider."""

    def __init__(self, model_name: str = "microsoft/phi-2") -> None:
        self.model_name = model_name
        self._pipeline = None
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import transformers  # noqa: F401

            self._available = True
        except ImportError:
            self._available = False
        return self._available

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult:
        """Executes generation via Transformers pipeline."""
        import time

        from transformers import pipeline

        start_time = time.perf_counter()

        if self._pipeline is None:
            self._pipeline = pipeline("text-generation", model=self.model_name, device_map="auto")

        outputs = self._pipeline(
            prompt,
            max_new_tokens=kwargs.get("max_tokens", 256),
            temperature=kwargs.get("temperature", 0.7),
            do_sample=True,
        )

        content = outputs[0]["generated_text"][len(prompt) :]
        latency = (time.perf_counter() - start_time) * 1000

        return InferenceResult(
            content=content.strip(),
            model=self.model_name,
            provider=ProviderType.TRANSFORMERS,
            latency_ms=latency,
            usage={"prompt_tokens": len(prompt.split()), "completion_tokens": len(content.split())},
        )


class MockProvider:
    """Mock provider for testing and development."""

    def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult:
        """Returns a mock response for testing."""
        await asyncio.sleep(0.05)  # Simulate latency
        return InferenceResult(
            content=f"[MOCK] Response to: {prompt[:50]}...",
            model="mock-model",
            provider=ProviderType.MOCK,
            latency_ms=50.0,
            usage={"prompt_tokens": len(prompt.split()), "completion_tokens": 10},
        )


# Singleton harness instance
_harness: InferenceHarness | None = None


def get_harness() -> InferenceHarness:
    """Get or create the global inference harness."""
    global _harness
    if _harness is None:
        _harness = InferenceHarness()
    return _harness


async def quick_generate(prompt: str, **kwargs: Any) -> str:
    """Quick helper for simple generation tasks."""
    harness = get_harness()
    result = await harness.generate(prompt, **kwargs)
    return result.content
