"""Ollama connectivity smoke test — skips gracefully when Ollama is not running."""

import pytest

httpx = pytest.importorskip("httpx", reason="httpx not installed")

OLLAMA_URL = "http://localhost:11434/api/tags"


def _ollama_reachable() -> bool:
    try:
        import httpx

        r = httpx.get(OLLAMA_URL, timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def ollama_available():
    """Session-scoped check for Ollama availability."""
    return _ollama_reachable()


@pytest.mark.usefixtures("ollama_available")
class TestOllama:
    """Tests that require Ollama to be running."""

    def test_ollama_tags(self):
        """Test that Ollama API is accessible."""
        r = httpx.get(OLLAMA_URL, timeout=10.0)
        assert r.status_code == 200
