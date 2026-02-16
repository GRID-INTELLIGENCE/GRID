"""Ollama connectivity smoke test — skips gracefully when Ollama is not running."""

import pytest

httpx = pytest.importorskip("httpx", reason="httpx not installed")

OLLAMA_URL = "http://localhost:11434/api/tags"


def _ollama_reachable() -> bool:
    try:
        httpx.get(OLLAMA_URL, timeout=2.0)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _ollama_reachable(), reason="Ollama not running")


def test_ollama_tags():
    r = httpx.get(OLLAMA_URL, timeout=10.0)
    assert r.status_code == 200
