"""Cloud Ollama LLM provider."""

from .ollama_local import OllamaLocalLLM


class OllamaCloudLLM(OllamaLocalLLM):
    """Cloud Ollama LLM provider.

    Extends local provider but uses cloud URL.
    """

    def __init__(self, model: str, cloud_url: str, timeout: int = 120):
        """Initialize cloud Ollama LLM provider.

        Args:
            model: Model name
            cloud_url: Cloud Ollama base URL
            timeout: Request timeout in seconds
        """
        super().__init__(model=model, base_url=cloud_url, timeout=timeout)
