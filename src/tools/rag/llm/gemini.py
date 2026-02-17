"""Google Gemini LLM provider."""

from typing import Any, AsyncGenerator

from .base import BaseLLMProvider


class GeminiLLM(BaseLLMProvider):
    """Google Gemini LLM provider for Gemini models (Gemini 1.5 Pro, Gemini 1.5 Flash, etc.).

    Uses the official Google Generative AI Python client.
    """

    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        api_key: str | None = None,
        timeout: float = 120.0,
    ):
        """Initialize Gemini LLM provider.

        Args:
            model: Model name (gemini-1.5-pro, gemini-1.5-flash, gemini-1.0-pro, etc.)
            api_key: Google API key (if None, uses GEMINI_API_KEY or GOOGLE_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        """Lazy load Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai

                # Use provided key or fallback to env vars
                api_key = self.api_key or genai.api_key
                if api_key:
                    genai.configure(api_key=api_key)

                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                raise ImportError(
                    "Google Generative AI library not installed. Install with: pip install google-generativeai"
                ) from None
        return self._client

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Gemini API.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        model = self._get_client()

        # Build generation config
        generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens

        try:
            # Gemini uses system instructions differently
            if system:
                # Prepend system to user prompt
                full_prompt = f"System: {system}\n\nUser: {prompt}"
            else:
                full_prompt = prompt

            response = model.generate_content(
                full_prompt,
                generation_config=generation_config,
                **kwargs,
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}") from e

    def stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Stream text generation.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
        """
        model = self._get_client()

        # Build generation config
        generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens

        try:
            if system:
                full_prompt = f"System: {system}\n\nUser: {prompt}"
            else:
                full_prompt = prompt

            response = model.generate_content(
                full_prompt,
                generation_config=generation_config,
                stream=True,
                **kwargs,
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise RuntimeError(f"Gemini streaming error: {e}") from e

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using async Gemini API.

        Note: Gemini's Python SDK doesn't have native async support.
        This runs the sync method in an executor.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            ),
        )

    async def async_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream text generation using async Gemini API.

        Note: Gemini's Python SDK doesn't have native async support.
        This runs the sync method in an executor and yields chunks.

        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
        """
        import asyncio

        loop = asyncio.get_event_loop()

        # Collect all chunks from sync stream
        chunks = []
        for chunk in self.stream(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            chunks.append(chunk)

        # Yield them one by one
        for chunk in chunks:
            yield chunk
            # Small sleep to allow other coroutines to run
            await asyncio.sleep(0)
