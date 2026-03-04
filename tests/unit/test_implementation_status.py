"""Implementation status tests: assert features are active or not enforced as designed."""

from __future__ import annotations

import os
import unittest


class TestEmbeddingsImplementationStatus(unittest.TestCase):
    """Implementation status: embeddings load without numpy for simple/ollama; HuggingFace optional."""

    def test_simple_provider_available_without_numpy(self):
        """Simple embedding provider is available without numpy (implementation: numpy not required)."""
        from tools.rag.embeddings import get_embedding_provider

        provider = get_embedding_provider("simple")
        self.assertIsNotNone(provider)
        emb = provider.embed("hello world")
        self.assertIsInstance(emb, list)
        self.assertEqual(len(emb), provider.dimension)

    def test_huggingface_optional_at_import(self):
        """HuggingFace provider is optional at package load (implementation: deactivation when numpy broken)."""
        from tools.rag import embeddings as emb_mod

        # HuggingFaceEmbeddingProvider is either a class or None when import failed
        self.assertTrue(emb_mod.HuggingFaceEmbeddingProvider is None or callable(emb_mod.HuggingFaceEmbeddingProvider))


class TestDebugEndpointImplementationStatus(unittest.TestCase):
    """Implementation status: debug endpoint returns 404 when DEBUG not set."""

    def test_debug_config_returns_404_when_debug_unset(self):
        """GET /debug/config is NOT active when DEBUG env is unset (returns 404)."""
        orig = os.environ.pop("DEBUG", None)
        try:
            try:
                from fastapi import FastAPI
                from fastapi.testclient import TestClient

                from application.resonance.api.router import router
            except (ImportError, ModuleNotFoundError):
                self.skipTest("resonance router or FastAPI not available")
            app = FastAPI()
            app.include_router(router, prefix="/api/v1/resonance")
            client = TestClient(app)
            response = client.get("/api/v1/resonance/debug/config")
            self.assertEqual(response.status_code, 404)
        finally:
            if orig is not None:
                os.environ["DEBUG"] = orig
