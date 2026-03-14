"""Test fixtures for infrastructure.config tests."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest


@pytest.fixture
def clean_env() -> dict[str, str]:
    """Provide a clean environment for testing.
    
    Returns a copy of the current environment that can be modified
    without affecting other tests.
    """
    return os.environ.copy()


@pytest.fixture
def test_env(clean_env: dict[str, str]) -> dict[str, str]:
    """Provide a test environment with common test values.
    
    Sets up typical configuration values for testing without
    affecting the actual system environment.
    """
    test_values = {
        "TEST_BOOL_TRUE": "true",
        "TEST_BOOL_FALSE": "false",
        "TEST_BOOL_ONE": "1",
        "TEST_BOOL_ZERO": "0",
        "TEST_BOOL_YES": "yes",
        "TEST_BOOL_NO": "no",
        "TEST_BOOL_ON": "on",
        "TEST_BOOL_OFF": "off",
        "TEST_BOOL_ENABLED": "enabled",
        "TEST_BOOL_DISABLED": "disabled",
        "TEST_LIST": "a,b,c,d",
        "TEST_LIST_SPACED": "  a , b , c  ",
        "TEST_LIST_PIPED": "a|b|c",
        "TEST_INT": "42",
        "TEST_FLOAT": "3.14",
        "TEST_JSON": '{"key": "value", "number": 123}',
        "TEST_DB_URL": "sqlite:///test.db",
        "TEST_DB_URL_PG": "postgresql://localhost/mydb",
        "TEST_SECRET": "super-secret-key-1234567890",
        "TEST_TOKEN": "dapi1234567890abcdef",
    }
    merged = {**clean_env, **test_values}
    return merged


@pytest.fixture
def mock_env(test_env: dict[str, str]) -> Any:
    """Context manager to temporarily set environment variables.
    
    Usage:
        with mock_env(DEBUG="true", API_KEY="test"):
            # test code
    """
    return patch.dict(os.environ, test_env, clear=True)


@pytest.fixture
def mock_env_partial() -> Any:
    """Context manager to temporarily modify specific environment variables.
    
    Unlike mock_env, this only changes the specified variables
    and leaves others intact.
    
    Usage:
        with mock_env_partial(TEST_DEBUG="true"):
            # test code
    """
    def _mock_env_partial(**kwargs: str) -> Any:
        return patch.dict(os.environ, kwargs)
    return _mock_env_partial


@pytest.fixture
def sample_records() -> list[dict[str, Any]]:
    """Provide sample records for testing."""
    return [
        {"id": 1, "name": "Alice", "active": True, "score": 95.5},
        {"id": 2, "name": "Bob", "active": False, "score": 82.3},
        {"id": 3, "name": "Charlie", "active": True, "score": 77.1},
    ]


@pytest.fixture
def sample_urls() -> list[tuple[str, str]]:
    """Provide sample database URLs for testing normalization.
    
    Returns tuples of (input_url, expected_output_url).
    """
    return [
        # SQLite
        ("sqlite:///test.db", "sqlite+aiosqlite:///test.db"),
        ("sqlite:///:memory:", "sqlite+aiosqlite:///:memory:"),
        ("sqlite:///./relative/path.db", "sqlite+aiosqlite:///./relative/path.db"),
        # Already normalized - should stay same
        ("sqlite+aiosqlite:///test.db", "sqlite+aiosqlite:///test.db"),
        # PostgreSQL
        ("postgresql://localhost/mydb", "postgresql+asyncpg://localhost/mydb"),
        ("postgresql://user:pass@host:5432/db", "postgresql+asyncpg://user:pass@host:5432/db"),
        ("postgres://localhost/mydb", "postgresql+asyncpg://localhost/mydb"),
        # Already normalized
        ("postgresql+asyncpg://localhost/mydb", "postgresql+asyncpg://localhost/mydb"),
        # MySQL
        ("mysql://localhost/mydb", "mysql+aiomysql://localhost/mydb"),
        # Sync-only - should stay same
        ("databricks://token:abc@host", "databricks://token:abc@host"),
        ("oracle://user:pass@host/orcl", "oracle://user:pass@host/orcl"),
        # Unknown scheme - should stay same
        ("mongodb://localhost/db", "mongodb://localhost/db"),
    ]


@pytest.fixture
def sample_secrets() -> list[tuple[str, str]]:
    """Provide sample secrets for testing redaction.
    
    Returns tuples of (input_secret, expected_redacted).
    """
    return [
        # Short - too short to show partial
        ("abc", "***"),
        ("short", "***"),
        # Medium - show partial
        ("secret123456", "secr***3456"),
        ("my-api-key-12345", "my-a***2345"),
        # Long - show more
        ("dapi1234567890abcdef", "dapi***cdef"),
        ("super-secret-key-1234567890", "supe***7890"),
        # Empty
        ("", "***"),
        # Whitespace
        ("  token123  ", "toke***123"),
    ]


@pytest.fixture
def sample_urls_with_secrets() -> list[tuple[str, str]]:
    """Provide sample URLs with credentials for testing masking.
    
    Returns tuples of (input_url, expected_masked_url).
    """
    return [
        # Standard URL with password
        ("postgresql://user:secret123@localhost/db", "postgresql://user:***@localhost/db"),
        # Databricks token
        ("databricks://token:dapi1234567890@host", "databricks://token:***@host"),
        # No credentials
        ("postgresql://localhost/db", "postgresql://localhost/db"),
        # Query params with secrets
        ("https://api.example.com?key=secret123", "https://api.example.com?key=***"),
        ("https://api.example.com?token=abc123&other=value", "https://api.example.com?token=***&other=value"),
    ]


@pytest.fixture
def sample_dicts_with_secrets() -> list[tuple[dict, dict]]:
    """Provide sample dictionaries with secrets for testing masking.
    
    Returns tuples of (input_dict, expected_masked_dict).
    """
    return [
        # Simple case
        ({"api_key": "secret123", "name": "test"}, {"api_key": "***", "name": "test"}),
        # Nested
        ({"config": {"token": "abc123", "enabled": True}}, {"config": {"token": "***", "enabled": True}}),
        # Multiple secrets
        ({"api_key": "key1", "password": "pass2", "data": "ok"}, {"api_key": "***", "password": "***", "data": "ok"}),
        # No secrets
        ({"name": "test", "count": 42}, {"name": "test", "count": 42}),
    ]


@pytest.fixture
def settings_with_env(mock_env_partial: Any) -> Any:
    """Create test settings with environment variables.
    
    Usage:
        with settings_with_env(DEBUG="true", API_KEY="test"):
            settings = MySettings.from_env()
    """
    def _settings_with_env(**kwargs: str) -> Any:
        return mock_env_partial(**kwargs)
    return _settings_with_env
