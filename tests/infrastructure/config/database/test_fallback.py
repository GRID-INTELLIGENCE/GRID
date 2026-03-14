"""Unit tests for infrastructure.config.database.fallback module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from infrastructure.config.database.fallback import BackendStatus, DatabaseBackend, DatabaseFallbackChain, SimpleBackend


class TestSimpleBackend:
    """Tests for SimpleBackend class."""

    def test_default_healthy(self):
        """Test default backend is considered healthy."""
        backend = SimpleBackend("sqlite", "sqlite:///test.db", lambda: object())
        assert backend.is_healthy() is True

    def test_custom_health_check(self):
        """Test custom health check function."""
        health_check = MagicMock(return_value=False)
        backend = SimpleBackend("sqlite", "sqlite:///test.db", lambda: object(), health_fn=health_check)
        assert backend.is_healthy() is False
        health_check.assert_called_once()

    def test_url_property(self):
        """Test URL is stored correctly."""
        backend = SimpleBackend("sqlite", "sqlite:///test.db", lambda: object())
        assert backend.url == "sqlite:///test.db"

    def test_str_representation(self):
        """Test string representation."""
        backend = SimpleBackend("sqlite", "sqlite:///test.db", lambda: object())
        assert backend.name == "sqlite"
        assert "sqlite:///test.db" in backend.url


class TestDatabaseFallbackChain:
    """Tests for DatabaseFallbackChain class."""

    def test_first_healthy_backend_used(self):
        """Test first healthy backend is returned."""
        backend1 = MagicMock(spec=DatabaseBackend)
        backend1.name = "primary"
        backend1.is_healthy.return_value = True
        backend1.connect.return_value = "conn1"
        backend2 = MagicMock(spec=DatabaseBackend)
        backend2.name = "secondary"
        backend2.is_healthy.return_value = False

        chain = DatabaseFallbackChain([backend1, backend2])
        result = chain.get_connection()

        assert result == "conn1"
        backend1.is_healthy.assert_called_once()
        backend1.connect.assert_called_once()
        backend2.is_healthy.assert_not_called()

    def test_fallback_to_second_backend(self):
        """Test fallback to second backend when first is unhealthy."""
        backend1 = MagicMock(spec=DatabaseBackend)
        backend1.name = "primary"
        backend1.is_healthy.return_value = False
        backend2 = MagicMock(spec=DatabaseBackend)
        backend2.name = "secondary"
        backend2.is_healthy.return_value = True
        backend2.connect.return_value = "conn2"

        chain = DatabaseFallbackChain([backend1, backend2])
        result = chain.get_connection()

        assert result == "conn2"
        backend1.is_healthy.assert_called_once()
        backend2.is_healthy.assert_called_once()
        backend2.connect.assert_called_once()

    def test_all_backends_unhealthy_raises(self):
        """Test exception raised when all backends are unhealthy."""
        backend1 = MagicMock(spec=DatabaseBackend)
        backend1.name = "primary"
        backend1.is_healthy.return_value = False
        backend2 = MagicMock(spec=DatabaseBackend)
        backend2.name = "secondary"
        backend2.is_healthy.return_value = False

        chain = DatabaseFallbackChain([backend1, backend2])

        with pytest.raises(ConnectionError, match="All database backends unavailable"):
            chain.get_connection()

    def test_health_check_all_method(self):
        """Test health_check_all returns BackendStatus by backend name."""
        backend1 = MagicMock(spec=DatabaseBackend)
        backend1.name = "primary"
        backend1.is_healthy.return_value = True
        backend2 = MagicMock(spec=DatabaseBackend)
        backend2.name = "secondary"
        backend2.is_healthy.return_value = False

        chain = DatabaseFallbackChain([backend1, backend2])
        result = chain.health_check_all()

        assert set(result) == {"primary", "secondary"}
        assert isinstance(result["primary"], BackendStatus)
        assert result["primary"].is_healthy is True
        assert result["secondary"].is_healthy is False

    def test_active_backend_tracking(self):
        """Test active backend is tracked."""
        backend1 = MagicMock(spec=DatabaseBackend)
        backend1.name = "primary"
        backend1.is_healthy.return_value = True
        backend1.connect.return_value = "conn1"

        chain = DatabaseFallbackChain([backend1])
        chain.get_connection()

        assert chain._active_backend == backend1

    def test_empty_backends_raises(self):
        """Test exception raised when no backends provided."""
        chain = DatabaseFallbackChain([])

        with pytest.raises(ConnectionError, match="All database backends unavailable"):
            chain.get_connection()

    def test_custom_backend_class(self):
        """Test custom backend class can be used."""
        class CustomBackend(DatabaseBackend):
            def __init__(self, name: str, url: str):
                self._name = name
                self._url = url
                self._healthy = True

            @property
            def name(self) -> str:
                return self._name

            @property
            def url(self) -> str:
                return self._url

            def is_healthy(self) -> bool:
                return self._healthy

            def connect(self) -> bool:
                return self._healthy

        backend = CustomBackend("sqlite", "sqlite:///test.db")
        chain = DatabaseFallbackChain([backend])
        result = chain.get_connection()

        assert result is True
