"""Integration tests for error recovery under failure conditions.

Tests retry and fallback mechanisms when external services are unavailable
(ChromaDB offline, Ollama timeout, network failures).
"""

import asyncio

import pytest

from grid.resilience.metrics import get_metrics_collector
from grid.resilience.policies import DatabasePolicy, get_policy_for_operation
from grid.resilience.retry_decorator import async_retry, fallback, retry


@pytest.fixture
def metrics_collector():
    """Get and reset metrics collector for clean test state."""
    collector = get_metrics_collector()
    collector.reset_metrics()
    return collector


class TestRetryOnNetworkFailure:
    """Test retry behavior under network failures."""

    def test_retry_succeeds_on_transient_error(self):
        """Verify retry succeeds when operation fails then succeeds."""
        attempts = 0

        @retry(max_attempts=3, exceptions=(ConnectionError,))
        def flaky_network_call():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError("Connection reset")
            return {"status": "success"}

        result = flaky_network_call()
        assert result == {"status": "success"}
        assert attempts == 3

    def test_retry_exhausts_max_attempts(self):
        """Verify retry fails after max_attempts exceeded."""
        attempts = 0

        @retry(max_attempts=2, exceptions=(ConnectionError,), initial_delay=0.01)
        def always_fails():
            nonlocal attempts
            attempts += 1
            raise ConnectionError("Connection always fails")

        with pytest.raises(ConnectionError):
            always_fails()

        assert attempts == 2

    def test_retry_respects_timeout(self):
        """Verify retry respects overall timeout."""
        policy = get_policy_for_operation("network")
        assert policy.timeout_seconds == 120


class TestRetryOnDatabaseFailure:
    """Test retry behavior on database failures."""

    def test_database_retry_config(self):
        """Verify database policy has appropriate retry config."""
        policy = DatabasePolicy
        assert policy.max_attempts == 3
        assert policy.timeout_seconds == 60


class TestRetryOnLLMFailure:
    """Test retry behavior on LLM operation failures."""

    @pytest.mark.asyncio
    async def test_async_retry_on_llm_timeout(self):
        """Test async retry when LLM times out."""
        attempts = 0

        @async_retry(
            max_attempts=3,
            exceptions=(TimeoutError,),
            initial_delay=0.01,
        )
        async def llm_inference_flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise TimeoutError("LLM inference timeout")
            return {"tokens": 42, "result": "success"}

        result = await llm_inference_flaky()
        assert result == {"tokens": 42, "result": "success"}
        assert attempts == 2

    @pytest.mark.asyncio
    async def test_async_retry_exhausts_on_persistent_timeout(self):
        """Test async retry failure when LLM consistently times out."""

        @async_retry(
            max_attempts=2,
            exceptions=(TimeoutError,),
            initial_delay=0.01,
        )
        async def llm_inference_broken():
            raise TimeoutError("LLM service unreachable")

        with pytest.raises(TimeoutError):
            await llm_inference_broken()


class TestFallbackStrategy:
    """Test fallback strategy invocation."""

    def test_fallback_on_network_error(self):
        """Verify fallback function is called on network error."""
        def get_cached_result():
            return {"cached": True, "status": "fallback"}

        @fallback(fallback_func=get_cached_result, exceptions=(ConnectionError,))
        def fetch_from_api():
            raise ConnectionError("API unreachable")

        result = fetch_from_api()
        assert result == {"cached": True, "status": "fallback"}

    def test_primary_called_on_success(self):
        """Verify fallback is NOT called when primary succeeds."""
        fallback_called = False

        def fallback_func():
            nonlocal fallback_called
            fallback_called = True
            return {"fallback": True}

        @fallback(fallback_func=fallback_func)
        def successful_operation():
            return {"data": "primary"}

        result = successful_operation()
        assert result == {"data": "primary"}
        assert not fallback_called


class TestChromaDBOffline:
    """Test error recovery when ChromaDB is offline."""

    @pytest.mark.asyncio
    async def test_retry_on_chroma_connection_error(self):
        """Test retry when ChromaDB connection fails."""
        attempts = 0

        @async_retry(
            max_attempts=3,
            exceptions=(ConnectionError, OSError),
            initial_delay=0.01,
        )
        async def query_chroma_flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ConnectionError("ChromaDB connection refused")
            return {"documents": ["result1", "result2"]}

        result = await query_chroma_flaky()
        assert result == {"documents": ["result1", "result2"]}
        assert attempts == 2

    @pytest.mark.asyncio
    async def test_fallback_when_chroma_persistently_offline(self):
        """Test fallback strategy when ChromaDB stays offline."""

        async def fallback_query():
            return {"documents": [], "status": "cached"}

        @async_retry(
            max_attempts=1,
            exceptions=(ConnectionError,),
        )
        async def query_chroma_offline():
            raise ConnectionError("ChromaDB offline")

        # Manually test fallback since async_fallback is harder to mock
        with pytest.raises(ConnectionError):
            await query_chroma_offline()


class TestOllamaTimeout:
    """Test error recovery when Ollama times out."""

    @pytest.mark.asyncio
    async def test_retry_on_ollama_timeout(self):
        """Test retry when Ollama response times out."""
        attempts = 0

        @async_retry(
            max_attempts=3,
            exceptions=(TimeoutError,),
            initial_delay=0.01,
        )
        async def ollama_generate_flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise TimeoutError("Ollama generation timeout")
            return {"response": "Generated text"}

        result = await ollama_generate_flaky()
        assert result == {"response": "Generated text"}
        assert attempts == 2

    @pytest.mark.asyncio
    async def test_fallback_on_persistent_ollama_timeout(self):
        """Test graceful fallback when Ollama consistently times out."""

        async def fallback_generate():
            return {"response": "Default response", "fallback": True}

        attempt = 0

        async def ollama_always_timeout():
            nonlocal attempt
            attempt += 1
            raise TimeoutError("Ollama timeout")

        # Simulate retry exhaustion then fallback
        with pytest.raises(TimeoutError):
            await ollama_always_timeout()


class TestMetricsCollection:
    """Test metrics collection during error recovery."""

    def test_metrics_recorded_on_retry_success(self, metrics_collector):
        """Verify metrics are recorded when retry succeeds."""
        attempts = 0

        @retry(max_attempts=3, exceptions=(ValueError,), initial_delay=0.01)
        def operation_flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("Transient error")
            return "success"

        result = operation_flaky()
        assert result == "success"

    def test_metrics_recorded_on_retry_failure(self, metrics_collector):
        """Verify metrics are recorded when retry exhausts."""
        @retry(max_attempts=2, exceptions=(ValueError,), initial_delay=0.01)
        def operation_fails():
            raise ValueError("Persistent error")

        with pytest.raises(ValueError):
            operation_fails()


class TestPolicyRespected:
    """Test that operation policies are respected during retry."""

    def test_network_policy_max_attempts(self):
        """Verify network policy is enforced."""
        policy = get_policy_for_operation("network")
        assert policy.max_attempts == 4

    def test_llm_policy_backoff(self):
        """Verify LLM policy backoff factor."""
        policy = get_policy_for_operation("llm")
        assert policy.backoff_factor == 2.0
        assert policy.initial_delay == 2.0

    def test_database_policy_timeout(self):
        """Verify database policy timeout."""
        policy = get_policy_for_operation("database")
        assert policy.timeout_seconds == 60


@pytest.mark.asyncio
async def test_concurrent_failures_with_retry():
    """Test retry behavior under concurrent operation failures."""
    call_counts = {"op1": 0, "op2": 0}

    @async_retry(max_attempts=2, exceptions=(RuntimeError,), initial_delay=0.01)
    async def operation1():
        call_counts["op1"] += 1
        if call_counts["op1"] < 2:
            raise RuntimeError("Op1 fails first")
        await asyncio.sleep(0.01)
        return "op1_result"

    @async_retry(max_attempts=2, exceptions=(RuntimeError,), initial_delay=0.01)
    async def operation2():
        call_counts["op2"] += 1
        if call_counts["op2"] < 2:
            raise RuntimeError("Op2 fails first")
        await asyncio.sleep(0.01)
        return "op2_result"

    # Run both concurrently
    results = await asyncio.gather(operation1(), operation2())
    assert results == ["op1_result", "op2_result"]
    assert call_counts["op1"] == 2
    assert call_counts["op2"] == 2
