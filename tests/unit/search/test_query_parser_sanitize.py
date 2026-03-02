"""Tests for query parser sanitize function."""

import pytest

from search.query.parser import sanitize


class TestSanitize:
    def test_valid_query(self):
        valid, msg = sanitize("headphones wireless")
        assert valid is True
        assert msg is None

    def test_oversized_query(self):
        valid, msg = sanitize("x" * 15_000)
        assert valid is False
        assert "max length" in (msg or "")

    def test_non_string_rejected(self):
        valid, msg = sanitize(123)
        assert valid is False
        assert "string" in (msg or "")

    def test_dangerous_pattern_rejected(self):
        valid, msg = sanitize("test; drop table users")
        assert valid is False
        assert msg is not None
