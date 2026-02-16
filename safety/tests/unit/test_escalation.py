"""
Unit tests for the escalation handler.

Covers: is_user_suspended, _check_misuse threshold logic.
All Redis calls are mocked. Uses patch on _get_redis so tests are robust
when run after integration tests that set SAFETY_DEGRADED_MODE and patch
is_user_suspended in api/main.py.
"""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import safety.escalation.handler as _handler


def _make_get_redis_mock(mock_redis):
    """Return an async callable that returns mock_redis (for patching _get_redis)."""

    async def _fake():
        return mock_redis

    return _fake


@pytest.fixture(autouse=True)
def _reset_handler_state():
    """Reload the handler module to undo monkey-patching from api/main.py."""
    original_redis = _handler._redis
    importlib.reload(_handler)
    _handler._redis = None
    yield
    _handler._redis = original_redis


# ---------------------------------------------------------------------------
# is_user_suspended
# ---------------------------------------------------------------------------


class TestIsUserSuspended:
    """Tests for is_user_suspended()."""

    @pytest.mark.asyncio
    async def test_not_suspended(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        with patch.object(_handler, "_get_redis", _make_get_redis_mock(mock_redis)):
            result = await _handler.is_user_suspended("user-123")

        assert isinstance(result, _handler.SuspensionStatus)
        assert result.suspended is False
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_suspended_with_reason(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="POLICY_VIOLATION:audit-456")
        with patch.object(_handler, "_get_redis", _make_get_redis_mock(mock_redis)):
            result = await _handler.is_user_suspended("user-bad")

        assert result.suspended is True
        assert result.reason == "POLICY_VIOLATION:audit-456"

    @pytest.mark.asyncio
    async def test_fail_closed_on_redis_error(self):
        """When Redis is unavailable, fail closed (assume suspended)."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))
        with patch.object(_handler, "_get_redis", _make_get_redis_mock(mock_redis)):
            result = await _handler.is_user_suspended("user-unknown")

        assert result.suspended is True
        assert result.reason == "SUSPENSION_CHECK_UNAVAILABLE"


# ---------------------------------------------------------------------------
# _suspend_user
# ---------------------------------------------------------------------------


class TestSuspendUser:
    """Tests for _suspend_user()."""

    @pytest.mark.asyncio
    async def test_suspend_sets_key(self):
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        with patch.object(_handler, "_get_redis", _make_get_redis_mock(mock_redis)):
            await _handler._suspend_user("user-1", "audit-1", "TEST_REASON")

        mock_redis.set.assert_awaited_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "suspended:user-1"
        assert "TEST_REASON" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_suspend_graceful_on_redis_error(self):
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(side_effect=ConnectionError("Redis down"))
        with patch.object(_handler, "_get_redis", _make_get_redis_mock(mock_redis)):
            await _handler._suspend_user("user-1", "audit-1", "TEST")


# ---------------------------------------------------------------------------
# _check_misuse
# ---------------------------------------------------------------------------


class TestCheckMisuse:
    """Tests for _check_misuse() threshold logic."""

    @pytest.mark.asyncio
    async def test_below_threshold_no_suspension(self):
        """When count < threshold, user is NOT suspended."""
        mock_pipe = MagicMock()
        mock_pipe.zremrangebyscore = MagicMock()
        mock_pipe.zadd = MagicMock()
        mock_pipe.zcard = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[0, True, 2, True])

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        with (
            patch.object(_handler, "_get_redis", _make_get_redis_mock(mock_redis)),
            patch.object(_handler, "_suspend_user", new_callable=AsyncMock) as mock_suspend,
        ):
            await _handler._check_misuse("user-good")

        mock_suspend.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_above_threshold_triggers_suspension(self):
        """When count >= threshold, user IS suspended and limits tightened."""
        mock_pipe = MagicMock()
        mock_pipe.zremrangebyscore = MagicMock()
        mock_pipe.zadd = MagicMock()
        mock_pipe.zcard = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[0, True, 10, True])

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        mock_redis.xadd = AsyncMock()
        with (
            patch.object(_handler, "_get_redis", _make_get_redis_mock(mock_redis)),
            patch.object(_handler, "_suspend_user", new_callable=AsyncMock) as mock_suspend,
            patch("safety.api.rate_limiter.tighten_limits", new_callable=AsyncMock),
        ):
            await _handler._check_misuse("user-abuser")

        mock_suspend.assert_awaited_once()
        args = mock_suspend.call_args[0]
        assert args[0] == "user-abuser"

    @pytest.mark.asyncio
    async def test_redis_fallback_in_memory(self):
        """When Redis fails, fall back to in-memory tracking without crashing."""
        mock_pipe = MagicMock()
        mock_pipe.zremrangebyscore = MagicMock()
        mock_pipe.zadd = MagicMock()
        mock_pipe.zcard = MagicMock()
        mock_pipe.expire = MagicMock()
        mock_pipe.execute = AsyncMock(side_effect=ConnectionError("Redis down"))

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        with (
            patch.object(_handler, "_get_redis", _make_get_redis_mock(mock_redis)),
            patch.object(_handler, "_suspend_user", new_callable=AsyncMock),
        ):
            await _handler._check_misuse("user-fallback")
