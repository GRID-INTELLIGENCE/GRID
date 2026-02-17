"""GitHub Copilot CLI LLM provider with web fetching capabilities."""

import asyncio
import logging
import subprocess
from typing import Any, AsyncGenerator, Generator

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class CopilotLLM(BaseLLMProvider):
    """GitHub Copilot CLI LLM provider with integrated web fetching.

    Uses GitHub Copilot CLI for AI responses with web content fetching.
    Requires: copilot CLI installed and authenticated.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        timeout: int = 120,
        enable_web_fetch: bool = True,
        max_web_pages: int = 3,
    ):
        """Initialize Copilot CLI LLM provider."""
        self.model = model
        self.timeout = timeout
        self.enable_web_fetch = enable_web_fetch
        self.max_web_pages = max_web_pages

    def _check_copilot_cli(self) -> bool:
        """Check if Copilot CLI is installed and available."""
        try:
            result = subprocess.run(["copilot", "--version"], capture_output=True, timeout=5)  # noqa: S607 partial path is intentional
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _fetch_web_content(self, urls: list[str]) -> str:
        """Fetch web content for enhanced context."""
        if not self.enable_web_fetch or not urls:
            return ""

        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            return ""

        content_parts = []
        urls = urls[: self.max_web_pages]

        for url in urls:
            try:
                with httpx.Client(timeout=10) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    title = soup.title.string if soup.title else url
                    main_content = ""

                    for tag in ["article", "main", ".content", "body"]:
                        element = soup.select_one(tag)
                        if element:
                            main_content = element.get_text(separator=" ", strip=True)
                            break

                    if not main_content:
                        main_content = soup.get_text(separator=" ", strip=True)

                    if len(main_content) > 2000:
                        main_content = main_content[:2000] + "..."

                    content_parts.append(f"## {title}\nURL: {url}\n\n{main_content}\n")

            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")

        return "\n".join(content_parts)

    def _enhance_prompt_with_web(self, prompt: str) -> str:
        """Enhance prompt with web content if URLs are detected."""
        if not self.enable_web_fetch:
            return prompt

        import re

        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, prompt)

        if urls:
            web_content = self._fetch_web_content(urls)
            if web_content:
                return f"{prompt}\n\n## Web Content Context\n{web_content}"

        return prompt

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using GitHub Copilot CLI."""
        if not self._check_copilot_cli():
            return "[Copilot CLI not found. Install from: https://github.com/github/copilot-cli]"

        enhanced_prompt = self._enhance_prompt_with_web(prompt)

        try:
            result = subprocess.run(  # noqa: S603 subprocess call is intentional
                ["copilot", "chat", "--model", self.model, enhanced_prompt],  # noqa: S607 partial path is intentional
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"[Copilot CLI error] {result.stderr[:200]}"

        except subprocess.TimeoutExpired:
            return "[Request timeout]"
        except Exception as e:
            logger.error(f"Copilot generation failed: {e}")
            return f"[Error] {str(e)[:200]}"

    def stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Generator[str]:
        """Stream text generation."""
        yield self.generate(prompt, system, temperature, **kwargs)

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text completion asynchronously."""
        return await asyncio.to_thread(
            lambda: self.generate(prompt, system, temperature, max_tokens, **kwargs)
        )

    async def async_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str]:
        """Stream text generation asynchronously."""
        result = await self.async_generate(prompt, system, temperature, **kwargs)
        yield result
