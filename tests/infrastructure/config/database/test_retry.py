"""Unit tests for infrastructure.config.database.retry module."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.config.database.retry import ConnectionRetry, RetryConfig, RetryResult


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay_seconds == 2.0
        assert config.max_delay_seconds == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.jitter_factor == 0.1

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            base_delay_seconds=2.0,
            max_delay_seconds=60.0,
            exponential_base=3.0,
            jitter=False,
            jitter_factor=0.2,
        )
        assert config.max_retries == 5
        assert config.base_delay_seconds == 2.0
        assert config.max_delay_seconds == 60.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.jitter_factor == 0.2


class TestConnectionRetry:
    """Tests for ConnectionRetry class."""

    @pytest.fixture
    def default_retry(self) -> ConnectionRetry:
        """Create retry with default config."""
        return ConnectionRetry()

    @pytest.fixture
    def no_jitter_retry(self) -> ConnectionRetry:
        """Create retry without jitter."""
        return ConnectionRetry(RetryConfig(jitter=False))

    def test_successful_first_attempt(self, default_retry: ConnectionRetry):
        """Test successful operation on first attempt."""
        operation = MagicMock(return_value="success")

        result = default_retry.execute(operation)

        assert result.success is True
        assert result.attempts == 1
        assert result.last_error is None
        operation.assert_called_once()

    def test_retry_on_failure(self, default_retry: ConnectionRetry):
        """Test retry on failure."""
        operation = MagicMock(side_effect=[Exception("fail"), "success"])

        result = default_retry.execute(operation)

        assert result.success is True
        assert result.attempts == 2
        assert result.last_error is None

    def test_max_attempts_exceeded(self, default_retry: ConnectionRetry):
        """Test max attempts exceeded."""
        operation = MagicMock(side_effect=Exception("always fails"))

        result = default_retry.execute(operation)

        assert result.success is False
        assert str(result.last_error) == "always fails"
        assert result.attempts == 3

    def test_custom_retry_on_exception(self, default_retry: ConnectionRetry):
        """Test retry only on specific exceptions."""
        operation = MagicMock(side_effect=[ValueError("retry me"), "success"])

        result = default_retry.execute(operation, retry_on=(ValueError,))

        assert result.success is True
        assert result.attempts == 2

    def test_no_retry_on_non_matching_exception(self, default_retry: ConnectionRetry):
        """Test no retry on non-matching exception."""
        operation = MagicMock(side_effect=[TypeError("don't retry")])

        with pytest.raises(TypeError, match="don't retry"):
            default_retry.execute(operation, retry_on=(ValueError,))

    def test_delay_calculation(self, no_jitter_retry: ConnectionRetry):
        """Test delay calculation between attempts."""
        operation = MagicMock(side_effect=[Exception("fail1"), Exception("fail2"), "success"])

        delays = []
        with patch("time.sleep", side_effect=lambda d: delays.append(d)):
            no_jitter_retry.execute(operation)

        assert len(delays) == 2
        assert delays[0] == 2.0
        assert delays[1] == 4.0

    def test_max_delay_cap(self):
        """Test delay is capped at max_delay_seconds."""
        retry = ConnectionRetry(RetryConfig(max_delay_seconds=5.0, jitter=False))
        operation = MagicMock(side_effect=[Exception("fail"), "success"])

        delays = []
        with patch("time.sleep", side_effect=lambda d: delays.append(d)):
            retry.execute(operation)

        # All delays should be capped at 5.0
        for delay in delays:
            assert delay <= 5.0

    def test_result_object(self, default_retry: ConnectionRetry):
        """Test RetryResult object attributes."""
        operation = MagicMock(return_value="result")

        result = default_retry.execute(operation)

        assert hasattr(result, "success")
        assert hasattr(result, "attempts")
        assert hasattr(result, "total_delay_seconds")
        assert hasattr(result, "last_error")


class TestRetryResult:
    """Tests for RetryResult dataclass."""

    def test_successful_result(self):
        """Test successful result object."""
        result = RetryResult(
            success=True,
            attempts=1,
            total_delay_seconds=0.0,
            last_error=None,
        )
        assert result.success is True
        assert result.last_error is None

    def test_failed_result(self):
        """Test failed result object."""
        exc = Exception("Something went wrong")
        result = RetryResult(
            success=False,
            attempts=3,
            total_delay_seconds=6.0,
            last_error=exc,
        )
        assert result.success is False
        assert result.last_error is exc
        assert result.attempts == 3
