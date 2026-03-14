"""Unit tests for infrastructure.config.security.redaction module."""

from __future__ import annotations

import pytest

from infrastructure.config.security.redaction import (
    SecretMasker,
    mask_connection_string,
    mask_dict_secrets,
    mask_secret,
    mask_url_secrets,
    redact_token,
)


class TestRedactToken:
    """Tests for redact_token function."""

    def test_short_tokens(self):
        """Test short tokens are fully masked."""
        assert redact_token("abc") == "***"
        assert redact_token("ab") == "***"
        assert redact_token("a") == "***"

    def test_medium_tokens(self):
        """Test medium tokens show partial."""
        assert redact_token("secret123456") == "secr***3456"
        assert redact_token("my-api-key-12345") == "my-a***2345"

    def test_long_tokens(self):
        """Test long tokens show partial."""
        assert redact_token("dapi1234567890abcdef") == "dapi***cdef"
        assert redact_token("super-secret-key-1234567890") == "supe***7890"

    def test_empty_string(self):
        """Test empty string returns mask."""
        assert redact_token("") == "***"

    def test_none_input(self):
        """Test None returns mask."""
        assert redact_token(None) == "***"

    def test_whitespace_handling(self):
        """Test whitespace is trimmed."""
        assert redact_token("  token123456  ") == "toke***3456"

    def test_custom_visible_chars(self):
        """Test custom visible characters count."""
        assert redact_token("secret123456", visible_chars=2) == "se***56"
        assert redact_token("secret123456", visible_chars=6) == "secre***23456"


class TestMaskSecret:
    """Tests for mask_secret function."""

    def test_short_secrets(self):
        """Test short secrets are fully masked."""
        assert mask_secret("abc") == "***"
        assert mask_secret("short") == "***"

    def test_medium_secrets(self):
        """Test medium secrets show partial."""
        assert mask_secret("my-secret-key-12345") == "my-s***2345"
        assert mask_secret("api-key-1234567890") == "api-***7890"

    def test_long_secrets(self):
        """Test long secrets show partial."""
        assert mask_secret("super-long-secret-key-1234567890") == "supe***7890"

    def test_empty_string(self):
        """Test empty string returns mask."""
        assert mask_secret("") == "***"

    def test_none_input(self):
        """Test None returns mask."""
        assert mask_secret(None) == "***"

    def test_custom_visible_prefix_suffix(self):
        """Test custom prefix/suffix visibility."""
        assert mask_secret("my-secret-key", visible_prefix=2, visible_suffix=2) == "my***ey"
        assert mask_secret("my-secret-key", visible_prefix=5, visible_suffix=3) == "my-se***key"


class TestMaskUrlSecrets:
    """Tests for mask_url_secrets function."""

    def test_postgresql_password(self):
        """Test PostgreSQL password is masked."""
        result = mask_url_secrets("postgresql://user:secret123@localhost/db")
        assert result == "postgresql://user:***@localhost/db"

    def test_mysql_password(self):
        """Test MySQL password is masked."""
        result = mask_url_secrets("mysql://user:password@localhost/db")
        assert result == "mysql://user:***@localhost/db"

    def test_databricks_token(self):
        """Test Databricks token is masked."""
        result = mask_url_secrets("databricks://token:dapi1234567890@host")
        assert result == "databricks://token:***@host"

    def test_no_credentials(self):
        """Test URL without credentials is unchanged."""
        result = mask_url_secrets("postgresql://localhost/db")
        assert result == "postgresql://localhost/db"

    def test_query_params_with_secrets(self):
        """Test query parameters with secrets are masked."""
        result = mask_url_secrets("https://api.example.com?key=secret123")
        assert result == "https://api.example.com?key=***"

    def test_multiple_secret_query_params(self):
        """Test multiple secret query parameters."""
        result = mask_url_secrets("https://api.com?token=abc&api_key=xyz&other=value")
        assert "token=***" in result
        assert "api_key=***" in result
        assert "other=value" in result

    def test_case_insensitive_param_names(self):
        """Test case insensitive secret parameter names."""
        result = mask_url_secrets("https://api.com?TOKEN=abc&API_KEY=xyz")
        assert "TOKEN=***" in result
        assert "API_KEY=***" in result

    def test_empty_input(self):
        """Test empty input returns empty string."""
        assert mask_url_secrets("") == ""
        assert mask_url_secrets(None) is None


class TestMaskDictSecrets:
    """Tests for mask_dict_secrets function."""

    def test_simple_dict(self):
        """Test simple dictionary with secrets."""
        data = {"api_key": "secret123", "name": "test"}
        result = mask_dict_secrets(data)
        assert result == {"api_key": "***", "name": "test"}

    def test_nested_dict(self):
        """Test nested dictionary."""
        data = {"config": {"token": "abc123", "enabled": True}}
        result = mask_dict_secrets(data)
        assert result == {"config": {"token": "***", "enabled": True}}

    def test_list_in_dict(self):
        """Test dictionary with list values."""
        data = {"items": [{"api_key": "secret1"}, {"api_key": "secret2"}]}
        result = mask_dict_secrets(data)
        assert result["items"][0]["api_key"] == "***"
        assert result["items"][1]["api_key"] == "***"

    def test_non_string_values_unchanged(self):
        """Test non-string values are unchanged."""
        data = {"count": 42, "active": True, "rate": 3.14}
        result = mask_dict_secrets(data)
        assert result == data

    def test_custom_secret_keys(self):
        """Test custom secret key patterns."""
        data = {"my_secret": "value", "custom_key": "data"}
        result = mask_dict_secrets(data, secret_keys={"my_secret"})
        assert result["my_secret"] == "***"
        assert result["custom_key"] == "data"

    def test_custom_mask_string(self):
        """Test custom mask string."""
        data = {"api_key": "secret"}
        result = mask_dict_secrets(data, mask="[HIDDEN]")
        assert result["api_key"] == "[HIDDEN]"

    def test_non_recursive(self):
        """Test non-recursive masking."""
        data = {"outer": {"inner": {"api_key": "secret"}}}
        result = mask_dict_secrets(data, recursive=False)
        assert result["outer"]["inner"]["api_key"] == "secret"  # Not masked

    def test_no_secrets(self):
        """Test dictionary without secrets."""
        data = {"name": "test", "count": 42}
        result = mask_dict_secrets(data)
        assert result == data


class TestMaskConnectionString:
    """Tests for mask_connection_string function."""

    def test_postgresql_connection_string(self):
        """Test PostgreSQL connection string."""
        result = mask_connection_string("postgresql://user:password@localhost/db")
        assert result == "postgresql://user:***@localhost/db"

    def test_mysql_connection_string(self):
        """Test MySQL connection string."""
        result = mask_connection_string("mysql://user:password@localhost/db")
        assert result == "mysql://user:***@localhost/db"

    def test_databricks_connection_string(self):
        """Test Databricks connection string."""
        result = mask_connection_string("databricks://token:dapi123@host")
        assert result == "databricks://token:***@host"


class TestSecretMasker:
    """Tests for SecretMasker class."""

    @pytest.fixture
    def masker(self) -> SecretMasker:
        """Create SecretMasker with defaults."""
        return SecretMasker()

    def test_mask_token(self, masker: SecretMasker):
        """Test token masking."""
        assert masker.mask_token("dapi1234567890abcdef") == "dapi***cdef"

    def test_mask_secret(self, masker: SecretMasker):
        """Test secret masking."""
        assert masker.mask_secret("my-secret-key-12345") == "my-s***2345"

    def test_mask_url(self, masker: SecretMasker):
        """Test URL masking."""
        result = masker.mask_url("postgresql://user:secret@localhost/db")
        assert result == "postgresql://user:***@localhost/db"

    def test_mask_dict(self, masker: SecretMasker):
        """Test dictionary masking."""
        data = {"api_key": "secret123", "name": "test"}
        result = masker.mask_dict(data)
        assert result["api_key"] == "***"
        assert result["name"] == "test"

    def test_should_mask_key(self, masker: SecretMasker):
        """Test key detection."""
        assert masker.should_mask_key("api_key") is True
        assert masker.should_mask_key("token") is True
        assert masker.should_mask_key("password") is True
        assert masker.should_mask_key("name") is False
        assert masker.should_mask_key("count") is False

    def test_custom_secret_keys(self):
        """Test custom secret key configuration."""
        masker = SecretMasker(secret_keys={"custom_key"})
        assert masker.should_mask_key("custom_key") is True
        assert masker.should_mask_key("api_key") is False

    def test_custom_visible_chars(self):
        """Test custom visible characters."""
        masker = SecretMasker(visible_chars=2)
        assert masker.mask_token("secret123456") == "se***56"
