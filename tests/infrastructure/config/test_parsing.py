"""Unit tests for infrastructure.config.parsing module."""

from __future__ import annotations

import pytest

from infrastructure.config.parsing import (
    EnvParser,
    parse_bool,
    parse_float,
    parse_int,
    parse_json,
    parse_list,
    parse_path,
    parse_url,
)


class TestParseBool:
    """Tests for parse_bool function."""

    def test_true_values(self):
        """Test all true value formats."""
        assert parse_bool("true") is True
        assert parse_bool("True") is True
        assert parse_bool("TRUE") is True
        assert parse_bool("1") is True
        assert parse_bool("yes") is True
        assert parse_bool("Yes") is True
        assert parse_bool("YES") is True
        assert parse_bool("y") is True
        assert parse_bool("Y") is True
        assert parse_bool("on") is True
        assert parse_bool("On") is True
        assert parse_bool("ON") is True
        assert parse_bool("enabled") is True
        assert parse_bool("Enabled") is True

    def test_false_values(self):
        """Test all false value formats."""
        assert parse_bool("false") is False
        assert parse_bool("False") is False
        assert parse_bool("FALSE") is False
        assert parse_bool("0") is False
        assert parse_bool("no") is False
        assert parse_bool("No") is False
        assert parse_bool("NO") is False
        assert parse_bool("n") is False
        assert parse_bool("N") is False
        assert parse_bool("off") is False
        assert parse_bool("Off") is False
        assert parse_bool("OFF") is False
        assert parse_bool("disabled") is False
        assert parse_bool("Disabled") is False
        assert parse_bool("") is False

    def test_none_input(self):
        """Test None input with default."""
        assert parse_bool(None) is False
        assert parse_bool(None, default=True) is True
        assert parse_bool(None, default=False) is False

    def test_unknown_value_returns_default(self):
        """Test unknown values return default with warning."""
        assert parse_bool("maybe") is False
        assert parse_bool("maybe", default=True) is True
        assert parse_bool("unknown") is False

    def test_whitespace_handling(self):
        """Test whitespace is trimmed."""
        assert parse_bool("  true  ") is True
        assert parse_bool("  1  ") is True
        assert parse_bool("  ") is False


class TestParseList:
    """Tests for parse_list function."""

    def test_basic_comma_separated(self):
        """Test basic comma-separated parsing."""
        assert parse_list("a,b,c") == ["a", "b", "c"]
        assert parse_list("a,b") == ["a", "b"]
        assert parse_list("a") == ["a"]

    def test_whitespace_handling(self):
        """Test whitespace is stripped from items."""
        assert parse_list("  a , b , c  ") == ["a", "b", "c"]
        assert parse_list("a ,b,c ") == ["a", "b", "c"]

    def test_empty_values_filtered(self):
        """Test empty strings are filtered out."""
        assert parse_list("a,,b") == ["a", "b"]
        assert parse_list(",a,b,") == ["a", "b"]
        assert parse_list(",,") == []

    def test_none_input(self):
        """Test None returns empty list."""
        assert parse_list(None) == []
        assert parse_list("") == []
        assert parse_list("   ") == []

    def test_custom_separator(self):
        """Test custom separator."""
        assert parse_list("a|b|c", separator="|") == ["a", "b", "c"]
        assert parse_list("a;b;c", separator=";") == ["a", "b", "c"]
        assert parse_list("a:b:c", separator=":") == ["a", "b", "c"]

    def test_no_strip_option(self):
        """Test strip=False preserves whitespace."""
        assert parse_list(" a , b , c ", strip=False) == [" a ", " b ", " c "]


class TestParseInt:
    """Tests for parse_int function."""

    def test_valid_integers(self):
        """Test parsing valid integers."""
        assert parse_int("42") == 42
        assert parse_int("0") == 0
        assert parse_int("-10") == -10
        assert parse_int("  100  ") == 100

    def test_none_input(self):
        """Test None returns default."""
        assert parse_int(None) == 0
        assert parse_int(None, default=10) == 10

    def test_invalid_input(self):
        """Test invalid input returns default."""
        assert parse_int("not-a-number") == 0
        assert parse_int("not-a-number", default=5) == 5

    def test_bounds_checking(self):
        """Test min/max bounds."""
        assert parse_int("5", min_value=1, max_value=10) == 5
        assert parse_int("0", min_value=1, max_value=10) == 1  # clamped
        assert parse_int("15", min_value=1, max_value=10) == 10  # clamped


class TestParseFloat:
    """Tests for parse_float function."""

    def test_valid_floats(self):
        """Test parsing valid floats."""
        assert parse_float("3.14") == 3.14
        assert parse_float("0.0") == 0.0
        assert parse_float("-2.5") == -2.5
        assert parse_float("  1.5  ") == 1.5

    def test_integer_input(self):
        """Test parsing integers as floats."""
        assert parse_float("42") == 42.0

    def test_none_input(self):
        """Test None returns default."""
        assert parse_float(None) == 0.0
        assert parse_float(None, default=1.5) == 1.5

    def test_invalid_input(self):
        """Test invalid input returns default."""
        assert parse_float("not-a-float") == 0.0
        assert parse_float("not-a-float", default=2.5) == 2.5

    def test_bounds_checking(self):
        """Test min/max bounds."""
        assert parse_float("0.5", min_value=0.0, max_value=1.0) == 0.5
        assert parse_float("-0.5", min_value=0.0, max_value=1.0) == 0.0  # clamped
        assert parse_float("1.5", min_value=0.0, max_value=1.0) == 1.0  # clamped


class TestParseJson:
    """Tests for parse_json function."""

    def test_valid_json_objects(self):
        """Test parsing JSON objects."""
        result = parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_valid_json_arrays(self):
        """Test parsing JSON arrays."""
        result = parse_json('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_valid_json_primitives(self):
        """Test parsing JSON primitives."""
        assert parse_json('"string"') == "string"
        assert parse_json("42") == 42
        assert parse_json("3.14") == 3.14
        assert parse_json("true") is True
        assert parse_json("null") is None

    def test_none_input(self):
        """Test None returns default."""
        assert parse_json(None) is None
        assert parse_json(None, default={"default": True}) == {"default": True}

    def test_invalid_json(self):
        """Test invalid JSON returns default."""
        assert parse_json("not-json") is None
        assert parse_json("not-json", default=[]) == []

    def test_empty_input(self):
        """Test empty string returns default."""
        assert parse_json("") is None
        assert parse_json("   ") is None


class TestParseUrl:
    """Tests for parse_url function."""

    def test_valid_urls(self):
        """Test parsing valid URLs."""
        assert parse_url("https://example.com") == "https://example.com"
        assert parse_url("http://localhost:8080") == "http://localhost:8080"
        assert parse_url("  https://example.com  ") == "https://example.com"

    def test_none_input(self):
        """Test None returns default."""
        assert parse_url(None) == ""
        assert parse_url(None, default="http://localhost") == "http://localhost"

    def test_require_scheme(self):
        """Test scheme requirement."""
        assert parse_url("https://example.com", require_scheme=True) == "https://example.com"
        assert parse_url("example.com", require_scheme=True) == ""
        assert parse_url("example.com", require_scheme=True, default="http://default") == "http://default"


class TestParsePath:
    """Tests for parse_path function."""

    def test_valid_paths(self):
        """Test parsing valid paths."""
        assert parse_path("/home/user/config") == "/home/user/config"
        assert parse_path("relative/path") == "relative/path"
        assert parse_path("  /some/path  ") == "/some/path"

    def test_none_input(self):
        """Test None returns default."""
        assert parse_path(None) == ""
        assert parse_path(None, default="./config") == "./config"

    def test_must_exist_validation(self):
        """Test path existence validation."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            # Existing path should return itself
            result = parse_path(temp_path, must_exist=True)
            assert temp_path in result or result == temp_path
            
            # Non-existing path should return default
            result = parse_path("C:\\nonexistent\\path\\that\\does\\not\\exist\\file.txt", must_exist=True, default="./config")
            assert result == "./config"
        finally:
            os.unlink(temp_path)


class TestEnvParser:
    """Tests for EnvParser class."""

    @pytest.fixture
    def env_dict(self) -> dict[str, str]:
        """Provide test environment dictionary."""
        return {
            "MYAPP_DEBUG": "true",
            "MYAPP_PORT": "8080",
            "MYAPP_RATE": "3.14",
            "MYAPP_HOSTS": "host1,host2,host3",
            "MYAPP_CONFIG": '{"key": "value"}',
            "MYAPP_URL": "https://example.com",
            "MYAPP_PATH": "/data/config",
            "MYAPP_NAME": "test-app",
        }

    @pytest.fixture
    def parser(self, env_dict: dict[str, str]) -> EnvParser:
        """Create EnvParser with test data."""
        return EnvParser("MYAPP_", env_dict)

    def test_bool_parsing(self, parser: EnvParser):
        """Test boolean parsing."""
        assert parser.bool("DEBUG") is True
        assert parser.bool("DEBUG", default=False) is True

    def test_int_parsing(self, parser: EnvParser):
        """Test integer parsing."""
        assert parser.int("PORT") == 8080
        assert parser.int("PORT", default=3000) == 8080

    def test_float_parsing(self, parser: EnvParser):
        """Test float parsing."""
        assert parser.float("RATE") == 3.14
        assert parser.float("RATE", default=1.0) == 3.14

    def test_list_parsing(self, parser: EnvParser):
        """Test list parsing."""
        assert parser.list("HOSTS") == ["host1", "host2", "host3"]

    def test_json_parsing(self, parser: EnvParser):
        """Test JSON parsing."""
        assert parser.json("CONFIG") == {"key": "value"}

    def test_url_parsing(self, parser: EnvParser):
        """Test URL parsing."""
        assert parser.url("URL") == "https://example.com"

    def test_path_parsing(self, parser: EnvParser):
        """Test path parsing."""
        assert parser.path("PATH") == "/data/config"

    def test_str_parsing(self, parser: EnvParser):
        """Test string parsing."""
        assert parser.str("NAME") == "test-app"
        assert parser.str("MISSING", default="default") == "default"

    def test_missing_key(self, parser: EnvParser):
        """Test handling of missing keys."""
        assert parser.bool("MISSING") is False
        assert parser.bool("MISSING", default=True) is True
        assert parser.int("MISSING") == 0
        assert parser.str("MISSING") == ""

    def test_custom_separator(self, parser: EnvParser):
        """Test custom separator."""
        assert parser.list("HOSTS", separator=",") == ["host1", "host2", "host3"]

    def test_prefix_behavior(self):
        """Test that prefix is applied correctly."""
        env = {"APP_DEBUG": "true", "OTHER_DEBUG": "false"}
        parser = EnvParser("APP_", env)
        assert parser.bool("DEBUG") is True
        assert parser.bool("OTHER_DEBUG", default=True) is True  # prefix not applied to OTHER_
