"""llama.cpp (GGUF) LLM provider."""

from __future__ import annotations

from typing import Any

from .base import BaseLLMProvider


class LlamaCppLLM(BaseLLMProvider):
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_threads: int | None = None,
        n_gpu_layers: int = 0,
    ) -> None:
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as e:
            raise ImportError("llama-cpp-python not installed. Install it to use GGUF models.") from e

        self._llama = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        full_prompt = prompt
        if system:
            full_prompt = f"System:\n{system}\n\nUser:\n{prompt}\n\nAssistant:\n"

        out = self._llama(
            full_prompt,
            temperature=temperature,
            max_tokens=max_tokens or 512,
            stop=kwargs.get("stop"),
        )
        choices = out.get("choices") or []
        if not choices:
            return ""
        return str(choices[0].get("text", ""))

    def stream(self, prompt: str, system: str | None = None, temperature: float = 0.7, **kwargs: Any) -> Any:
        full_prompt = prompt
        if system:
            full_prompt = f"System:\n{system}\n\nUser:\n{prompt}\n\nAssistant:\n"

        for chunk in self._llama(
            full_prompt,
            temperature=temperature,
            max_tokens=kwargs.get("max_tokens", 512),
            stream=True,
            stop=kwargs.get("stop"),
        ):
            choices = chunk.get("choices") or []
            if not choices:
                continue
            text = choices[0].get("text")
            if text:
                yield str(text)
