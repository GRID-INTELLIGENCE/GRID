"""Unit tests for infrastructure.config.database.url_normalizer module."""

from __future__ import annotations

import pytest

from infrastructure.config.database.url_normalizer import (
    ParsedURL,
    build_url,
    mask_url_secrets,
    normalize_async_url,
    parse_database_url,
    supports_async,
)


class TestNormalizeAsyncUrl:
    """Tests for normalize_async_url function."""

    def test_sqlite_normalization(self):
        """Test SQLite URL normalization."""
        assert normalize_async_url("sqlite:///test.db") == "sqlite+aiosqlite:///test.db"
        assert normalize_async_url("sqlite:///:memory:") == "sqlite+aiosqlite:///:memory:"
        assert normalize_async_url("sqlite:///./relative/path.db") == "sqlite+aiosqlite:///./relative/path.db"

    def test_postgresql_normalization(self):
        """Test PostgreSQL URL normalization."""
        assert normalize_async_url("postgresql://localhost/mydb") == "postgresql+asyncpg://localhost/mydb"
        assert normalize_async_url("postgres://localhost/mydb") == "postgresql+asyncpg://localhost/mydb"

    def test_mysql_normalization(self):
        """Test MySQL URL normalization."""
        assert normalize_async_url("mysql://localhost/mydb") == "mysql+aiomysql://localhost/mydb"

    def test_already_normalized(self):
        """Test already normalized URLs stay the same."""
        assert normalize_async_url("sqlite+aiosqlite:///test.db") == "sqlite+aiosqlite:///test.db"
        assert normalize_async_url("postgresql+asyncpg://localhost/mydb") == "postgresql+asyncpg://localhost/mydb"

    def test_sync_only_databases(self):
        """Test sync-only databases are not modified."""
        assert normalize_async_url("databricks://token:abc@host") == "databricks://token:abc@host"
        assert normalize_async_url("oracle://user:pass@host/orcl") == "oracle://user:pass@host/orcl"
        assert normalize_async_url("mssql://user:pass@host/db") == "mssql://user:pass@host/db"

    def test_unknown_scheme(self):
        """Test unknown schemes are not modified."""
        assert normalize_async_url("mongodb://localhost/db") == "mongodb://localhost/db"
        assert normalize_async_url("redis://localhost/0") == "redis://localhost/0"

    def test_empty_input(self):
        """Test empty input returns empty string."""
        assert normalize_async_url("") == ""
        assert normalize_async_url(None) == ""

    def test_force_normalization(self):
        """Test force parameter re-normalizes already normalized URLs."""
        assert normalize_async_url("sqlite+aiosqlite:///test.db", force=True) == "sqlite+aiosqlite:///test.db"

    def test_url_with_credentials(self):
        """Test URLs with credentials are normalized."""
        result = normalize_async_url("postgresql://user:password@host:5432/db")
        assert "postgresql+asyncpg://" in result
        assert "user:password@host:5432/db" in result


class TestParseDatabaseUrl:
    """Tests for parse_database_url function."""

    def test_sqlite_parsing(self):
        """Test SQLite URL parsing."""
        result = parse_database_url("sqlite:///test.db")
        assert result.scheme == "sqlite"
        assert result.driver is None
        assert result.database == "test.db"
        assert result.host is None

    def test_sqlite_memory(self):
        """Test SQLite in-memory database parsing."""
        result = parse_database_url("sqlite:///:memory:")
        assert result.scheme == "sqlite"
        assert result.database == ":memory:"

    def test_postgresql_parsing(self):
        """Test PostgreSQL URL parsing."""
        result = parse_database_url("postgresql://user:pass@localhost:5432/mydb")
        assert result.scheme == "postgresql"
        assert result.driver is None
        assert result.username == "user"
        assert result.password == "pass"
        assert result.host == "localhost"
        assert result.port == 5432
        assert result.database == "mydb"

    def test_postgresql_with_driver(self):
        """Test PostgreSQL URL with driver."""
        result = parse_database_url("postgresql+asyncpg://localhost/mydb")
        assert result.scheme == "postgresql"
        assert result.driver == "asyncpg"

    def test_mysql_parsing(self):
        """Test MySQL URL parsing."""
        result = parse_database_url("mysql://user:pass@localhost:3306/mydb")
        assert result.scheme == "mysql"
        assert result.username == "user"
        assert result.password == "pass"
        assert result.host == "localhost"
        assert result.port == 3306
        assert result.database == "mydb"

    def test_databricks_parsing(self):
        """Test Databricks URL parsing."""
        result = parse_database_url("databricks://token:abc123@host")
        assert result.scheme == "databricks"
        assert result.username == "token"
        assert result.password == "abc123"
        assert result.host == "host"

    def test_query_parameters(self):
        """Test query parameters are parsed."""
        result = parse_database_url("postgresql://localhost/mydb?search_path=public&sslmode=require")
        assert result.query.get("search_path") == "public"
        assert result.query.get("sslmode") == "require"

    def test_empty_input(self):
        """Test empty input returns unknown scheme."""
        result = parse_database_url("")
        assert result.scheme == "unknown"


class TestParsedURL:
    """Tests for ParsedURL dataclass."""

    def test_has_async_driver(self):
        """Test async driver detection."""
        url_with_driver = parse_database_url("sqlite+aiosqlite:///test.db")
        assert url_with_driver.has_async_driver is True

        url_without_driver = parse_database_url("sqlite:///test.db")
        assert url_without_driver.has_async_driver is False

    def test_is_sync_only(self):
        """Test sync-only database detection."""
        assert parse_database_url("databricks://host").is_sync_only is True
        assert parse_database_url("oracle://host").is_sync_only is True
        assert parse_database_url("sqlite:///test.db").is_sync_only is False


class TestSupportsAsync:
    """Tests for supports_async function."""

    def test_sqlite_support(self):
        """Test SQLite async support."""
        assert supports_async("sqlite:///test.db") is True
        assert supports_async("sqlite+aiosqlite:///test.db") is True

    def test_postgresql_support(self):
        """Test PostgreSQL async support."""
        assert supports_async("postgresql://localhost/db") is True
        assert supports_async("postgres://localhost/db") is True

    def test_databricks_no_support(self):
        """Test Databricks has no async support."""
        assert supports_async("databricks://host") is False


class TestMaskUrlSecrets:
    """Tests for mask_url_secrets function."""

    def test_postgresql_password_masking(self):
        """Test PostgreSQL password is masked."""
        result = mask_url_secrets("postgresql://user:secret123@localhost/db")
        assert result == "postgresql://user:***@localhost/db"

    def test_databricks_token_masking(self):
        """Test Databricks token is masked."""
        result = mask_url_secrets("databricks://token:dapi1234567890@host")
        assert result == "databricks://token:***@host"

    def test_no_credentials(self):
        """Test URL without credentials is unchanged."""
        result = mask_url_secrets("postgresql://localhost/db")
        assert result == "postgresql://localhost/db"

    def test_query_param_masking(self):
        """Test query parameters with secrets are masked."""
        result = mask_url_secrets("https://api.example.com?key=secret123")
        assert result == "https://api.example.com?key=***"

    def test_multiple_query_params(self):
        """Test multiple query parameters."""
        result = mask_url_secrets("https://api.example.com?token=abc&api_key=xyz&other=value")
        assert "token=***" in result
        assert "api_key=***" in result
        assert "other=value" in result


class TestBuildUrl:
    """Tests for build_url function."""

    def test_sqlite_url(self):
        """Test SQLite URL building."""
        result = build_url("sqlite", database="test.db")
        assert result == "sqlite:///test.db"

    def test_sqlite_with_path(self):
        """Test SQLite URL with path."""
        result = build_url("sqlite", database="test.db")
        assert result == "sqlite:///test.db"

    def test_postgresql_url(self):
        """Test PostgreSQL URL building."""
        result = build_url("postgresql", host="localhost", database="mydb")
        assert result == "postgresql://localhost/mydb"

    def test_postgresql_with_credentials(self):
        """Test PostgreSQL URL with credentials."""
        result = build_url("postgresql", host="localhost", database="mydb", username="user", password="pass")
        assert result == "postgresql://user:pass@localhost/mydb"

    def test_postgresql_with_port(self):
        """Test PostgreSQL URL with port."""
        result = build_url("postgresql", host="localhost", port=5432, database="mydb")
        assert result == "postgresql://localhost:5432/mydb"

    def test_with_driver(self):
        """Test URL with async driver."""
        result = build_url("postgresql", host="localhost", database="mydb", driver="asyncpg")
        assert result == "postgresql+asyncpg://localhost/mydb"

    def test_with_query_params(self):
        """Test URL with query parameters."""
        result = build_url("postgresql", host="localhost", database="mydb", query={"sslmode": "require"})
        assert "sslmode=require" in result
