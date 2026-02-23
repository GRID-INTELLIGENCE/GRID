"""
Comprehensive XAI Integration Tests
Tests streaming, threading, caching, load balancing, and adaptive processing.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

# Import XAI modules
try:
    from grid.xai.performance_optimizer import (
        XAIAdaptiveProcessor,
        XAICache,
        XAILoadBalancer,
    )
    from grid.xai.stream_adapter import StreamChunk, StreamProgress, XAIStreamAdapter
    from grid.xai.threading_framework import XAIThreadPool

    XAI_AVAILABLE = True
except ImportError as e:
    print(f"XAI modules not available: {e}")
    XAI_AVAILABLE = False


class TestXAIStreamAdapter:
    """Test XAI stream adapter functionality."""

    @pytest.fixture
    def stream_adapter(self):
        """Create stream adapter instance."""
        if XAI_AVAILABLE:
            return XAIStreamAdapter(chunk_size=256)
        return Mock()

    def test_stream_chunk_creation(self, stream_adapter):
        """Test stream chunk creation."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        chunk = StreamChunk(
            chunk_id="test_chunk_1", content="Test content", sequence_number=1, metadata={"type": "test"}
        )

        assert chunk.chunk_id == "test_chunk_1"
        assert chunk.content == "Test content"
        assert chunk.sequence_number == 1
        assert chunk.metadata["type"] == "test"
        assert not chunk.is_complete

    def test_stream_progress_tracking(self, stream_adapter):
        """Test stream progress tracking."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        progress = StreamProgress(
            total_chunks=10, processed_chunks=3, start_time=datetime.now(), estimated_completion=1.0
        )

        assert progress.get_completion_percentage() == 30.0
        assert progress.estimated_completion > 0

        eta = progress.get_eta()
        assert "s" in eta or "m" in eta or "h" in eta

    @pytest.mark.asyncio
    async def test_stream_processing(self, stream_adapter):
        """Test stream processing with mock data."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        # Simulate streaming response with dicts
        async def mock_response():
            for i in range(3):
                yield {"content": f"Content {i}"}

        chunks = await stream_adapter.process_streaming_response(
            response_stream=mock_response(), stream_id="test_stream", progress_callback=AsyncMock()
        )

        assert len(chunks) == 3


@pytest.mark.skipif(not XAI_AVAILABLE, reason="XAI modules not available")
class TestXAIThreadPool:
    """Test XAI thread pool functionality."""

    @pytest.fixture
    def thread_pool(self):
        """Create thread pool instance."""
        if XAI_AVAILABLE:
            return XAIThreadPool(max_workers=5, max_queue_size=50)
        return Mock()

    @pytest.mark.asyncio
    async def test_task_submission(self, thread_pool):
        """Test task submission to thread pool."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        task_id = await thread_pool.submit_task("test_task", priority=1)

        assert task_id.startswith("task_")
        assert thread_pool.task_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_worker_execution(self, thread_pool):
        """Test worker execution."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        # Mock worker task
        async def mock_task():
            await asyncio.sleep(0.1)
            return "test_result"

        await thread_pool.submit_task(task_type="test", task_coroutine=mock_task, priority=1)

        status = thread_pool.get_queue_status()
        assert status["queue_size"] >= 1
        assert status["max_workers"] == 5

    def test_performance_metrics(self, thread_pool):
        """Test performance metrics collection."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        metrics = thread_pool.get_performance_metrics()

        assert "total_workers" in metrics
        assert "total_tasks_completed" in metrics
        assert isinstance(metrics["average_processing_time"], float)


@pytest.mark.skipif(not XAI_AVAILABLE, reason="XAI modules not available")
class TestXAICache:
    """Test XAI cache functionality."""

    @pytest.fixture
    def xai_cache(self):
        """Create cache instance."""
        if XAI_AVAILABLE:
            return XAICache(max_size=100, default_ttl_seconds=1800)
        return Mock()

    @pytest.mark.asyncio
    async def test_cache_operations(self, xai_cache):
        """Test cache get/put operations."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        # Test cache miss
        result = await xai_cache.get("nonexistent_key")
        assert result is None

        # Test cache put
        success = await xai_cache.put("test_key", "test_value")
        assert success

        # Test cache hit
        result = await xai_cache.get("test_key")
        assert result == "test_value"

        # Test cache expiration
        stats = xai_cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_memory_limits(self, xai_cache):
        """Test cache memory limits."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        # Fill cache with entries
        for i in range(150):
            await xai_cache.put(f"key_{i}", "x" * 100)

        stats = xai_cache.get_stats()
        assert stats["cache_size"] > 0
        assert stats["memory_usage_mb"] >= 0


@pytest.mark.skipif(not XAI_AVAILABLE, reason="XAI modules not available")
class TestXAILoadBalancer:
    """Test XAI load balancer functionality."""

    @pytest.fixture
    def load_balancer(self):
        """Create load balancer instance."""
        if XAI_AVAILABLE:
            return XAILoadBalancer()
        return Mock()

    def test_server_management(self, load_balancer):
        """Test server addition and health checking."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        # Add servers
        load_balancer.add_server("server1", capacity=100)
        load_balancer.add_server("server2", capacity=150)

        status = load_balancer.get_server_status()
        assert status["total_servers"] == 2
        assert status["healthy_servers"] == 0  # No health checks yet

        # Update health
        load_balancer.update_server_health("server1", True)
        load_balancer.update_server_health("server2", True)

        status = load_balancer.get_server_status()
        assert status["healthy_servers"] == 2

    def test_server_selection(self, load_balancer):
        """Test server selection algorithms."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        # Add and health-check servers before selecting
        load_balancer.add_server("server1", capacity=100)
        load_balancer.add_server("server2", capacity=150)
        load_balancer.update_server_health("server1", True)
        load_balancer.update_server_health("server2", True)

        # Test round-robin for normal priority
        server = load_balancer.select_server(task_priority=1)
        assert server in ["server1", "server2"]

        # Test load-based for high priority
        # Simulate server1 being loaded
        load_balancer.update_server_load("server1", response_time=0.5, task_complexity=1.0)

        server = load_balancer.select_server(task_priority=10)
        assert server == "server2"  # Should select server2 (less loaded)

    def test_load_balancing_metrics(self, load_balancer):
        """Test load balancing metrics."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        load_balancer.add_server("server1", capacity=100)
        load_balancer.update_server_load("server1", response_time=0.2, task_complexity=1.0)
        load_balancer.update_server_load("server1", response_time=0.1, task_complexity=1.0)

        status = load_balancer.get_server_status()
        server1_stats = status["servers"]["server1"]

        assert server1_stats["active_tasks"] >= 2
        assert server1_stats["load_factor"] > 0


@pytest.mark.skipif(not XAI_AVAILABLE, reason="XAI modules not available")
class TestXAIAdaptiveProcessor:
    """Test XAI adaptive processor functionality."""

    @pytest.fixture
    def adaptive_processor(self):
        """Create adaptive processor instance."""
        if XAI_AVAILABLE:
            return XAIAdaptiveProcessor()
        return Mock()

    def test_load_adaptation(self, adaptive_processor):
        """Test load adaptation based on system performance."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        # Simulate sustained high load (EMA smoothing requires multiple updates)
        for _ in range(20):
            adaptive_processor.update_load(0.95)
        adaptive_processor.record_performance(0.15)

        config = adaptive_processor.get_adaptive_config()
        assert config["processing_mode"] == "fast"
        assert config["config"]["batch_size"] == 32  # Smaller batches for fast mode
        assert config["config"]["timeout_seconds"] == 10  # Shorter timeouts

    def test_performance_tracking(self, adaptive_processor):
        """Test performance tracking and adaptation."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        # Record multiple performance metrics
        for i in range(5):
            adaptive_processor.record_performance(0.1 + i * 0.02)  # Improving performance

        config = adaptive_processor.get_adaptive_config()
        avg_performance = config["average_performance"]

        assert avg_performance > 0.1  # Should reflect improvement
        assert "processing_mode" in config


@pytest.mark.skipif(not XAI_AVAILABLE, reason="XAI modules not available")
class TestXAIIntegration:
    """Test integration between XAI components."""

    @pytest.fixture
    def xai_components(self):
        """Create XAI components for integration testing."""
        if XAI_AVAILABLE:
            from grid.xai.threading_framework import XAIResourceManager

            return {
                "stream_adapter": XAIStreamAdapter(),
                "thread_pool": XAIThreadPool(max_workers=3),
                "cache": XAICache(max_size=50),
                "load_balancer": XAILoadBalancer(),
                "adaptive_processor": XAIAdaptiveProcessor(),
                "resource_manager": XAIResourceManager(),
            }
        return Mock()

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, xai_components):
        """Test complete workflow from streaming to adaptive processing."""
        if not XAI_AVAILABLE:
            pytest.skip("XAI modules not available")
            return

        # Mock streaming response
        async def mock_stream():
            for i in range(5):
                yield {"content": f"Chunk {i}", "done": i == 4}

        # Process with adaptive configuration
        xai_components["adaptive_processor"].get_adaptive_config()

        # Should adapt to fast mode under sustained load (EMA smoothing)
        for _ in range(20):
            xai_components["adaptive_processor"].update_load(0.95)

        await xai_components["stream_adapter"].process_streaming_response(
            response_stream=mock_stream(), stream_id="integration_test", progress_callback=None
        )

        # Verify adaptation occurred
        new_config = xai_components["adaptive_processor"].get_adaptive_config()
        assert new_config["processing_mode"] == "fast"

        # Check resource management
        xai_components["resource_manager"].allocate_resources("test_task")
        resource_status = xai_components["resource_manager"].get_resource_status()
        assert resource_status["current_usage"]["active_explanations"] >= 1


if __name__ == "__main__":
    print("Running XAI integration tests...")

    # Run basic smoke tests
    pytest.main([__file__])
