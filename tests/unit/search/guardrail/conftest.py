"""Fixtures for guardrail tests."""

from __future__ import annotations

import pytest

from search.guardrail.tools.base import GuardrailContext
from search.models import RequestContext


@pytest.fixture
def request_context() -> RequestContext:
    return RequestContext(
        identity="user-123",
        index_name="products",
        query_text="headphones",
        page=1,
        size=10,
        ip_address="127.0.0.1",
    )


@pytest.fixture
def guardrail_context(request_context, test_config) -> GuardrailContext:
    return GuardrailContext(request=request_context, config=test_config)


@pytest.fixture
def guardrail_config_auth_optional(test_config):
    """Config with auth not required (for tests that want to bypass auth)."""
    from search.config import SearchConfig

    cfg = SearchConfig(
        embedding_provider=test_config.embedding_provider,
        vector_store_backend=test_config.vector_store_backend,
        cross_encoder_enabled=test_config.cross_encoder_enabled,
        guardrail_auth_required=False,
    )
    return cfg


@pytest.fixture
def guardrail_context_no_identity(test_config) -> GuardrailContext:
    ctx = RequestContext(
        identity=None,
        index_name="products",
        query_text="headphones",
        page=1,
        size=10,
    )
    return GuardrailContext(request=ctx, config=test_config)
