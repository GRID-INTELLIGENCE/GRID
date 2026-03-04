"""Shared fixtures for search module tests.

Uses lazy imports inside fixtures to avoid conftest load-time import failures
when pytest's --import-mode=importlib processes conftest files before sys.path
is fully configured.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def embedding_provider():
    from tools.rag.embeddings.test_provider import DeterministicEmbeddingProvider

    return DeterministicEmbeddingProvider(dimension=384, seed=42)


@pytest.fixture
def vector_store():
    from tools.rag.vector_store.in_memory_dense import InMemoryDenseStore

    return InMemoryDenseStore()


@pytest.fixture
def test_config():
    from search.config import SearchConfig

    return SearchConfig(
        embedding_provider="simple",
        vector_store_backend="in_memory",
        cross_encoder_enabled=False,
        guardrail_enabled=False,
        guardrail_auth_required=False,
    )


@pytest.fixture
def product_schema():
    from search.models import FieldSchema, FieldType, IndexSchema

    return IndexSchema(
        name="products",
        fields={
            "title": FieldSchema(type=FieldType.TEXT, searchable=True, weight=2.0),
            "description": FieldSchema(type=FieldType.TEXT, searchable=True),
            "price": FieldSchema(type=FieldType.FLOAT, filterable=True, facetable=True),
            "category": FieldSchema(type=FieldType.KEYWORD, filterable=True, facetable=True),
            "in_stock": FieldSchema(type=FieldType.BOOLEAN, filterable=True, facetable=True),
        },
    )


@pytest.fixture
def sample_documents():
    from search.models import Document

    return [
        Document(
            id="p1",
            fields={
                "title": "Wireless Bluetooth Headphones",
                "description": "Noise-cancelling over-ear headphones with 30h battery",
                "price": 79.99,
                "category": "electronics",
                "in_stock": True,
            },
        ),
        Document(
            id="p2",
            fields={
                "title": "USB-C Charging Cable",
                "description": "Fast charging braided cable 2m length",
                "price": 12.99,
                "category": "electronics",
                "in_stock": True,
            },
        ),
        Document(
            id="p3",
            fields={
                "title": "Running Shoes",
                "description": "Lightweight trail running shoes with grip sole",
                "price": 129.99,
                "category": "footwear",
                "in_stock": True,
            },
        ),
        Document(
            id="p4",
            fields={
                "title": "Leather Wallet",
                "description": "Genuine leather bifold wallet with RFID blocking",
                "price": 34.99,
                "category": "accessories",
                "in_stock": False,
            },
        ),
        Document(
            id="p5",
            fields={
                "title": "Mechanical Keyboard",
                "description": "RGB backlit mechanical keyboard with blue switches",
                "price": 89.99,
                "category": "electronics",
                "in_stock": True,
            },
        ),
    ]


@pytest.fixture
def search_engine(test_config):
    from search.engine import SearchEngine

    return SearchEngine(config=test_config)


@pytest.fixture
def indexed_engine(search_engine, product_schema, sample_documents):
    search_engine.create_index(product_schema)
    search_engine.index_documents("products", sample_documents)
    return search_engine
