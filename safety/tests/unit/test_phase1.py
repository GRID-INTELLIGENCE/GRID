import asyncio
import threading
import time
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from safety.api.rate_limiter import IPRateLimiter, ExponentialBackoff, _get_redis
from safety.observability.risk_score import RiskScoreManager, SecurityEvent, SecurityEventSeverity

@pytest.mark.asyncio
async def test_ip_rate_limiter_concurrency():
    limiter = IPRateLimiter()

    def worker():
        for _ in range(100):
            limiter.add_suspicious_activity("1.2.3.4", 0.1)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    is_suspicious, risk = limiter.is_ip_suspicious("1.2.3.4")
    # Expected risk: 10 threads * 100 increments * 0.1 = 100.0
    # Without locks, this might be less due to lost updates.
    # Use approx for float precision issues
    assert risk >= 100.0 or pytest.approx(risk) == 100.0
    assert limiter.is_ip_blocked("1.2.3.4")

@pytest.mark.asyncio
async def test_exponential_backoff_concurrency():
    backoff = ExponentialBackoff()

    def worker():
        for _ in range(100):
            backoff.record_violation("user1")

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Expected count: 10 * 100 = 1000
    assert backoff.violation_counts["user1"] == 1000

@pytest.mark.asyncio
async def test_redis_pool_singleton():
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_from_url.return_value = MagicMock()

        # Reset global
        import safety.api.rate_limiter
        safety.api.rate_limiter._redis_pool = None

        # Call _get_redis concurrently
        tasks = [asyncio.create_task(_get_redis()) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Verify only one call to from_url
        mock_from_url.assert_called_once()
        assert all(r is results[0] for r in results)

@pytest.mark.asyncio
async def test_risk_score_manager_lua():
    manager = RiskScoreManager()
    mock_redis = MagicMock()

    # Mock script_load as an async function
    async def async_script_load(*args, **kwargs):
        return "sha123"
    mock_redis.script_load = MagicMock(side_effect=async_script_load)

    # Mock evalsha as an async function
    async def async_evalsha(*args, **kwargs):
        return "0.5"
    mock_redis.evalsha = MagicMock(side_effect=async_evalsha)

    # Mock get_redis
    with patch("safety.observability.risk_score.get_redis", return_value=mock_redis):
        # We need a SecurityEvent object. We'll mock it enough.
        event = MagicMock(spec=SecurityEvent)
        event.user_id = "user1"
        event.severity = SecurityEventSeverity.MEDIUM
        event.timestamp = datetime.now().isoformat()

        await manager.record_violation(event)

        # Verify evalsha called with correct arguments
        mock_redis.evalsha.assert_called_once()
        args = mock_redis.evalsha.call_args[0]
        assert args[0] == "sha123"
        assert args[1] == 2 # keys
        assert args[2] == "risk:score:user1"
        assert args[3] == "risk:last_update:user1"
        assert args[4] == str(manager.SEVERITY_WEIGHTS[SecurityEventSeverity.MEDIUM])
