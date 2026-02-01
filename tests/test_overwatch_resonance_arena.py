"""Tests for OVERWATCH Resonance Arena integration."""

# Import OVERWATCH components
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Try to import the_chase, skip tests if not available
try:
    # Check if Arena path exists before attempting import
    the_chase_path = Path(__file__).parent.parent / "Arena" / "the_chase" / "python" / "src"
    if not (the_chase_path / "the_chase").exists():
        raise ImportError("the_chase path does not exist")

    # Add the_chase to path
    if str(the_chase_path) not in sys.path:
        sys.path.insert(0, str(the_chase_path))

    from the_chase.overwatch.core import Overwatch, OverwatchConfig
    from the_chase.overwatch.resonance_link_pool import (
        ResonanceLinkPool,
        get_overwatch_resonance_pool,
    )

    HAS_THE_CHASE = True
except (ImportError, ModuleNotFoundError, OSError) as e:
    HAS_THE_CHASE = False
    pytestmark = pytest.mark.skip(reason=f"the_chase module not available: {e}")

    # Create dummy classes to prevent import errors
    class OverwatchConfig:
        pass

    class Overwatch:
        pass

    class ResonanceLinkPool:
        pass

    def get_overwatch_resonance_pool():
        pass


class TestOverwatchConfig:
    """Test OverwatchConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = OverwatchConfig()
        assert config.enable_sustain_decay_compensation is True
        assert config.enable_resonance_link_pooling is True
        assert config.enable_adaptive_attention_spans is True
        assert config.adaptive_attention_base_ms == 200.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = OverwatchConfig(
            attack_energy=0.2,
            sustain_level=0.7,
            adaptive_attention_base_ms=150.0,
        )
        assert config.attack_energy == 0.2
        assert config.sustain_level == 0.7
        assert config.adaptive_attention_base_ms == 150.0

    def test_config_validation(self):
        """Test configuration validation."""
        with pytest.raises(AssertionError):
            OverwatchConfig(attack_energy=1.5)  # Invalid range

        with pytest.raises(AssertionError):
            OverwatchConfig(adaptive_attention_base_ms=-10)  # Invalid value


class TestOverwatch:
    """Test Overwatch class."""

    def test_initialization(self):
        """Test Overwatch initialization."""
        config = OverwatchConfig()
        overwatch = Overwatch(config)
        assert overwatch.config == config
        assert overwatch.timeout_manager is not None
        assert overwatch.circuit_breaker is not None

    def test_adaptive_timeout(self):
        """Test adaptive timeout management."""
        config = OverwatchConfig(adaptive_attention_base_ms=200.0)
        overwatch = Overwatch(config)

        timeout = overwatch.get_adaptive_timeout_ms()
        assert timeout >= 50.0
        assert timeout <= 1000.0

        # Record successes should potentially reduce timeout
        for _ in range(10):
            overwatch.record_success(100.0)

        # Record failures should increase timeout
        for _ in range(5):
            overwatch.record_failure(500.0)

    def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        config = OverwatchConfig(guardian_shield_enabled=True)
        overwatch = Overwatch(config)

        # Circuit should be closed initially
        assert overwatch.is_circuit_open() is False

        # Record failures to open circuit
        for _ in range(6):  # More than threshold (5)
            overwatch.record_failure(500.0)

        # Circuit should be open
        assert overwatch.is_circuit_open() is True


class TestResonanceLinkPool:
    """Test Resonance Link Pool."""

    def test_pool_creation(self):
        """Test pool creation."""
        pool = ResonanceLinkPool(min_pool_size=1, max_pool_size=5)
        assert pool.min_pool_size == 1
        assert pool.max_pool_size == 5

    def test_acquire_link(self):
        """Test acquiring a link from pool."""
        pool = ResonanceLinkPool(min_pool_size=1, max_pool_size=5)
        link = pool.acquire_link()
        assert link is not None
        assert link.link_id is not None

    def test_return_link(self):
        """Test returning a link to pool."""
        pool = ResonanceLinkPool(min_pool_size=1, max_pool_size=5)
        link = pool.acquire_link()

        # Return with success
        pool.return_link(link, success=True, latency_ms=150.0)
        assert link.success_count == 1
        assert link.request_count == 1

        # Return with failure
        pool.return_link(link, success=False, latency_ms=500.0)
        assert link.failure_count == 1
        assert link.request_count == 2

    def test_adaptive_attention_span(self):
        """Test adaptive attention span updates."""
        pool = ResonanceLinkPool(min_pool_size=1, max_pool_size=5)
        link = pool.acquire_link()

        # Record fast successes
        for _ in range(10):
            pool.return_link(link, success=True, latency_ms=100.0)

        # Attention span should adapt
        assert 85.0 <= link.adaptive_attention_span_ms <= 345.0

    def test_global_pool(self):
        """Test global pool access."""
        pool1 = get_overwatch_resonance_pool()
        pool2 = get_overwatch_resonance_pool()
        assert pool1 is pool2  # Should be same instance


class TestOverwatchIntegration:
    """Integration tests for OVERWATCH system."""

    def test_full_workflow(self):
        """Test full OVERWATCH workflow."""
        config = OverwatchConfig(
            enable_resonance_link_pooling=True,
            enable_adaptive_attention_spans=True,
            adaptive_attention_base_ms=200.0,
        )
        overwatch = Overwatch(config)
        pool = get_overwatch_resonance_pool()

        # Simulate API call workflow
        link = pool.acquire_link()
        assert link is not None

        # Simulate successful API call
        start_time = time.time()
        # Simulate API call with adaptive timeout
        link.adaptive_attention_span_ms / 1000
        time.sleep(0.01)  # Simulate 10ms latency
        latency_ms = (time.time() - start_time) * 1000

        # Record success
        pool.return_link(link, success=True, latency_ms=latency_ms)
        overwatch.record_success(latency_ms)

        # Check stats
        stats = pool.get_pool_stats()
        assert stats["pool_size"] > 0

    @patch("requests.get")
    def test_api_call_with_overwatch(self, mock_get):
        """Test API call using OVERWATCH system."""
        from the_chase.overwatch.resonance_link_pool import get_overwatch_resonance_pool

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        config = OverwatchConfig()
        overwatch = Overwatch(config)
        pool = get_overwatch_resonance_pool()

        link = pool.acquire_link()
        assert link is not None

        # Use adaptive timeout
        timeout = link.adaptive_attention_span_ms / 1000

        # Make API call (mocked)
        import requests

        start_time = time.time()
        response = requests.get("http://example.com", timeout=timeout)
        latency_ms = (time.time() - start_time) * 1000

        success = response.status_code == 200
        pool.return_link(link, success, latency_ms)
        overwatch.record_success(latency_ms) if success else overwatch.record_failure(latency_ms)

        assert success is True
        mock_get.assert_called_once()
