"""
GRID Inference Harness
Tiered inference provider with automated fallback and environment awareness.
Part of the Sovereign Tier architecture.
"""

import asyncio
import logging
import os
import shlex
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

        # LlamaCPP (EUFLE Sync)
        eufle_root = Path(r"E:\EUFLE")
        gguf_path = eufle_root / "models" / "TinyLlama-1.1B-32k-f16.gguf"
        cli_path = "/home/irfan/eufle_work/llama.cpp/build/bin/llama-cli"
        self.providers[ProviderType.LLAMACPP] = LlamaCPPProvider(str(gguf_path), cli_path)

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

        raise RuntimeError("No available inference providers found.")


# Concrete Implementation: Transformers
class TransformersProvider:
    """Fallback via local HuggingFace Transformers (CPU/GPU)."""

    def __init__(self, model_id: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0") -> None:
        self.model_id = model_id
        self._model: Any | None = None
        self._tokenizer: Any | None = None

    def is_available(self) -> bool:
        """Checks if transformers library is installed."""
        try:
            import transformers

            return True
        except ImportError:
            return False

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult:
        """Executes generation using local transformers library."""
        import time

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        start_time = time.perf_counter()

        # Lazy load to save memory
        if not self._model:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_id, torch_dtype=torch.float16, device_map="auto"
            )

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        outputs = self._model.generate(
            **inputs, max_new_tokens=kwargs.get("max_tokens", 256), temperature=kwargs.get("temperature", 0.7)
        )

        content = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        latency = (time.perf_counter() - start_time) * 1000

        return InferenceResult(
            content=content,
            model=self.model_id,
            provider=ProviderType.TRANSFORMERS,
            latency_ms=latency,
            usage={"n_tokens": len(outputs[0])},
        )


# Concrete Implementation: Mock
class MockProvider:
    """Mock provider for CI/CD and rapid prototyping."""

    def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult:
        import time

        start_time = time.perf_counter()
        content = f"[MOCK RESPONSE] I am a holographic simulation of GRID. You asked: {prompt[:30]}..."
        latency = (time.perf_counter() - start_time) * 1000
        return InferenceResult(
            content=content, model="mock-v1", provider=ProviderType.MOCK, latency_ms=latency, usage={"tokens": 42}
        )


# Concrete Implementation: Ollama
class OllamaProvider:
    """Inference via local Ollama API."""

    def __init__(self, model: str = "mistral-nemo:latest") -> None:
        self.model = model
        self.base_url = "http://localhost:11434/api/generate"

    def is_available(self) -> bool:
        """Checks if Ollama service is reachable."""
        try:
            import requests

            response = requests.get("http://localhost:11434/api/tags", timeout=1)
            return response.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult:
        """Executes generation against Ollama."""
        import time

        import aiohttp

        start_time = time.perf_counter()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": kwargs.get("temperature", 0.7), "num_predict": kwargs.get("max_tokens", 256)},
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, json=payload) as resp:
                data = await resp.json()
                content = data.get("response", "")

        latency = (time.perf_counter() - start_time) * 1000
        return InferenceResult(
            content=content,
            model=self.model,
            provider=ProviderType.OLLAMA,
            latency_ms=latency,
            usage={"prompt_tokens": -1, "completion_tokens": -1},  # Ollama usage mapping needed
        )


# Concrete Implementation: LlamaCPP (WSL Bridge)
class LlamaCPPProvider:
    """Inference via llama-cli in WSL (EUFLE Legacy)."""

    def __init__(self, model_path: str, cli_path: str) -> None:
        self.model_path = model_path
        self.cli_path = cli_path

    def is_available(self) -> bool:
        """Checks if WSL and model file are available."""
        if not Path(self.model_path).exists():
            return False
        try:
            res = subprocess.run(["wsl", "ls", "/"], capture_output=True, timeout=2)
            return res.returncode == 0
        except Exception:
            return False

    def _win_to_wsl(self, path: str) -> str:
        """Converts Windows path to WSL mount path."""
        p = Path(path).resolve()
        drive = p.drive.lower().rstrip(":")
        rest = str(p)[2:].lstrip("\\/").replace("\\", "/")
        return f"/mnt/{drive}/{rest}"

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
            "bash",
            "-lc",
            f"{self.cli_path} -m {shlex.quote(wsl_model)} -f {shlex.quote(wsl_prompt)} "
            f"-n {kwargs.get('max_tokens', 256)} --temp {kwargs.get('temperature', 0.7)} "
            "--simple-io --no-display-prompt --single-turn --log-disable",
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
            model=Path(self.model_path).name,
            provider=ProviderType.LLAMACPP,
            latency_ms=latency,
            usage={"n_predict": kwargs.get("max_tokens", 256)},
        )
