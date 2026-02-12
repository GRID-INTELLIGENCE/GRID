"""Tests for crypto module."""

import pytest

from coinbase.crypto import CryptoScope


def test_crypto_scope_initial_state() -> None:
    """Test initial state of CryptoScope."""
    scope = CryptoScope()
    assert not scope.is_enabled()


def test_crypto_scope_enable() -> None:
    """Test enabling crypto scope."""
    scope = CryptoScope()
    scope.enable()
    assert scope.is_enabled()


def test_crypto_scope_disable() -> None:
    """Test disabling crypto scope."""
    scope = CryptoScope()
    scope.enable()
    scope.disable()
    assert not scope.is_enabled()


def test_crypto_scope_set_get_data() -> None:
    """Test setting and getting crypto data."""
    scope = CryptoScope()
    scope.enable()
    scope.set_data("key1", "value1")
    assert scope.get_data("key1") == "value1"


def test_crypto_scope_get_nonexistent_key() -> None:
    """Test getting nonexistent key returns None."""
    scope = CryptoScope()
    scope.enable()
    assert scope.get_data("nonexistent") is None


def test_crypto_scope_set_data_when_disabled() -> None:
    """Test setting data when disabled raises error."""
    scope = CryptoScope()
    with pytest.raises(RuntimeError, match="Crypto scope is not enabled"):
        scope.set_data("key", "value")


def test_crypto_scope_get_data_when_disabled() -> None:
    """Test getting data when disabled raises error."""
    scope = CryptoScope()
    scope.enable()
    scope.set_data("key", "value")
    scope.disable()
    with pytest.raises(RuntimeError, match="Crypto scope is not enabled"):
        scope.get_data("key")


def test_crypto_scope_clear_data() -> None:
    """Test clearing all crypto data."""
    scope = CryptoScope()
    scope.enable()
    scope.set_data("key1", "value1")
    scope.set_data("key2", "value2")
    scope.clear_data()
    assert scope.get_data("key1") is None
    assert scope.get_data("key2") is None
