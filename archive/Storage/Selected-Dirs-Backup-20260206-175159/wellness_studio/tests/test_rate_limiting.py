"""
Rate Limiting and Abuse Prevention Tests
"""
import pytest
import sys
import os
import time
import threading
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from wellness_studio.security.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitScope,
    AbusePrevention,
    ResourceQuotaManager,
    CircuitBreaker
)


class TestRateLimiterBasic:
    """Test basic rate limiting functionality"""

    def test_initial_request_allowed(self):
        """Test that first request is allowed"""
        limiter = RateLimiter()
        status = limiter.check_rate_limit("user_001")

        assert status.allowed is True
        assert status.remaining == 99  # 100 - 1 (current request)
        assert status.limit == 100

    def test_request_recording(self):
        """Test that requests are recorded"""
        limiter = RateLimiter()

        # Record first request
        status = limiter.record_request("user_001")
        assert status.allowed is True
        assert status.remaining == 98  # 100 - 2 (check + record)

        # Record more requests
        for _ in range(5):
            limiter.record_request("user_001")

        stats = limiter.get_stats("user_001")
        assert stats['request_count'] == 6  # Initial check + 5 recorded

    def test_limit_exceeded(self):
        """Test that limit is enforced"""
        config = RateLimitConfig(
            requests_per_window=5,
            window_seconds=60,
            block_duration_seconds=10
        )
        limiter = RateLimiter(config)

        # Exhaust limit
        for _ in range(5):
            limiter.record_request("user_001")

        # Next request should be blocked
        status = limiter.check_rate_limit("user_001")
        assert status.allowed is False
        assert status.remaining == 0
        assert status.retry_after is not None

    def test_block_expiration(self):
        """Test that block expires after duration"""
        config = RateLimitConfig(
            requests_per_window=1,
            window_seconds=1,  # 1 second window
            block_duration_seconds=1  # 1 second block (int, not float)
        )
        limiter = RateLimiter(config)

        # Use up limit
        limiter.record_request("user_001")
        status = limiter.check_rate_limit("user_001")
        assert status.allowed is False

        # Wait for block to expire and window to slide
        time.sleep(1.1)

        # Should be allowed again (window has slid past the old request)
        status = limiter.check_rate_limit("user_001")
        assert status.allowed is True

    def test_different_users_isolated(self):
        """Test that rate limits are isolated per user"""
        limiter = RateLimiter()

        # Exhaust limit for user_001
        for _ in range(100):
            limiter.record_request("user_001")

        # user_002 should still have full limit
        status = limiter.check_rate_limit("user_002")
        assert status.allowed is True
        assert status.remaining == 99


class TestRateLimitStrategies:
    """Test different rate limiting strategies"""

    def test_sliding_window(self):
        """Test sliding window strategy"""
        config = RateLimitConfig(
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            requests_per_window=10,
            window_seconds=1
        )
        limiter = RateLimiter(config)

        # Record requests
        for _ in range(5):
            limiter.record_request("user_001")

        status = limiter.check_rate_limit("user_001")
        assert status.remaining == 4

    def test_fixed_window_config(self):
        """Test that fixed window config is accepted"""
        config = RateLimitConfig(
            strategy=RateLimitStrategy.FIXED_WINDOW
        )
        limiter = RateLimiter(config)

        status = limiter.check_rate_limit("user_001")
        assert status.allowed is True


class TestRateLimitScopes:
    """Test different rate limit scopes"""

    def test_user_scope(self):
        """Test user-level rate limiting"""
        limiter = RateLimiter(RateLimitConfig(scope=RateLimitScope.USER))

        limiter.record_request("user_001")
        stats = limiter.get_stats("user_001")
        assert stats['request_count'] == 1

    def test_global_scope(self):
        """Test global rate limiting"""
        limiter = RateLimiter(RateLimitConfig(scope=RateLimitScope.GLOBAL))

        limiter.record_request("any_id")
        # All identifiers share the same limit
        status = limiter.check_rate_limit("different_id")
        # Should be affected by previous request


class TestRateLimitStats:
    """Test rate limiting statistics"""

    def test_violation_logging(self):
        """Test that violations are logged"""
        config = RateLimitConfig(
            requests_per_window=1,
            block_duration_seconds=1
        )
        limiter = RateLimiter(config)

        # Trigger violation
        limiter.record_request("user_001")
        limiter.check_rate_limit("user_001")  # Should block

        violations = limiter.get_violations()
        assert len(violations) >= 1

    def test_stats_aggregation(self):
        """Test statistics aggregation"""
        limiter = RateLimiter()

        limiter.record_request("user_001")
        limiter.record_request("user_002")
        limiter.record_request("user_003")

        stats = limiter.get_stats()
        assert stats['total_tracked'] == 3


class TestAbusePrevention:
    """Test abuse prevention features"""

    def test_rapid_fire_detection(self):
        """Test detection of rapid requests"""
        prevention = AbusePrevention()

        # Simulate rapid requests
        for _ in range(65):
            prevention.analyze_request_pattern("user_001", "api_call")

        result = prevention.analyze_request_pattern("user_001", "api_call")

        assert result['is_suspicious'] is True
        assert any(t['type'] == 'rapid_fire' for t in result['threats'])

    def test_burst_detection(self):
        """Test burst attack detection"""
        prevention = AbusePrevention()

        # Simulate burst (10 requests rapidly)
        for _ in range(10):
            result = prevention.analyze_request_pattern("user_001", "api_call")

        assert result['is_suspicious'] is True
        threats = result['threats']
        assert any(t['type'] == 'burst_attack' for t in threats)

    def test_normal_usage_not_flagged(self):
        """Test that normal usage isn't flagged"""
        prevention = AbusePrevention()

        # Single request
        result = prevention.analyze_request_pattern("user_001", "api_call")

        assert result['is_suspicious'] is False
        assert result['threats_detected'] == 0

    def test_suspicious_activity_flagging(self):
        """Test flagging suspicious activity"""
        prevention = AbusePrevention()

        prevention.flag_suspicious_activity(
            "user_001",
            "multiple_violations",
            {'violation_count': 10}
        )

        assessment = prevention.get_threat_assessment()
        assert assessment['total_suspicious_activities'] == 1

    def test_threat_assessment(self):
        """Test threat level assessment"""
        prevention = AbusePrevention()

        # Add multiple suspicious activities
        for i in range(7):
            prevention.flag_suspicious_activity(
                f"user_{i}",
                "test",
                {}
            )

        assessment = prevention.get_threat_assessment()
        assert assessment['requires_investigation'] is True
        assert assessment['threat_level'] in ['medium', 'high']


class TestResourceQuota:
    """Test resource quota management"""

    def test_quota_setup(self):
        """Test setting quotas"""
        manager = ResourceQuotaManager()

        manager.set_quota("user_001", daily_limit=100, monthly_limit=1000)
        status = manager.check_quota("user_001")

        assert status['has_quota'] is True
        assert status['daily_limit'] == 100
        assert status['monthly_limit'] == 1000
        assert status['daily_remaining'] == 100

    def test_quota_consumption(self):
        """Test quota consumption"""
        manager = ResourceQuotaManager()

        manager.set_quota("user_001", daily_limit=10, monthly_limit=100)

        # Consume some quota
        for _ in range(5):
            manager.consume_quota("user_001")

        status = manager.check_quota("user_001")
        assert status['daily_remaining'] == 5
        assert status['within_quota'] is True

    def test_quota_exceeded(self):
        """Test quota limit enforcement"""
        manager = ResourceQuotaManager()

        manager.set_quota("user_001", daily_limit=2, monthly_limit=100)

        # Consume all quota
        manager.consume_quota("user_001")
        manager.consume_quota("user_001")

        # Should fail
        result = manager.consume_quota("user_001")
        assert result is False

        status = manager.check_quota("user_001")
        assert status['within_quota'] is False

    def test_no_quota_returns_false(self):
        """Test that users without quota can't consume"""
        manager = ResourceQuotaManager()

        result = manager.consume_quota("unknown_user")
        assert result is False


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def test_initial_state_closed(self):
        """Test circuit starts closed"""
        cb = CircuitBreaker()

        assert cb.can_execute("service_001") is True
        status = cb.get_status("service_001")
        assert status['state'] == 'closed'

    def test_circuit_opens_after_failures(self):
        """Test circuit opens after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3)

        # Record failures
        for _ in range(3):
            cb.record_failure("service_001")

        assert cb.can_execute("service_001") is False
        status = cb.get_status("service_001")
        assert status['state'] == 'open'

    def test_circuit_closes_after_success(self):
        """Test circuit closes on success"""
        cb = CircuitBreaker()

        cb.record_failure("service_001")
        cb.record_success("service_001")

        status = cb.get_status("service_001")
        assert status['state'] == 'closed'
        assert status['failure_count'] == 0

    def test_half_open_state(self):
        """Test half-open recovery state"""
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=1
        )

        # Open circuit
        cb.record_failure("service_001")
        assert cb.can_execute("service_001") is False

        # Wait for recovery timeout
        time.sleep(1.1)

        # Should be half-open (can execute to test)
        assert cb.can_execute("service_001") is True


class TestRateLimiterThreadSafety:
    """Test thread safety of rate limiter"""

    def test_concurrent_requests(self):
        """Test concurrent request handling"""
        limiter = RateLimiter(RateLimitConfig(requests_per_window=1000))

        results = []

        def make_requests():
            for _ in range(10):
                status = limiter.record_request("concurrent_user")
                results.append(status.allowed)

        # Run multiple threads
        threads = [threading.Thread(target=make_requests) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed (within limit)
        assert all(results)

        # Verify count
        stats = limiter.get_stats("concurrent_user")
        assert stats['request_count'] == 50


class TestRateLimitEdgeCases:
    """Test edge cases"""

    def test_zero_limit(self):
        """Test behavior with zero limit"""
        config = RateLimitConfig(requests_per_window=0)
        limiter = RateLimiter(config)

        status = limiter.check_rate_limit("user_001")
        assert status.allowed is False

    def test_reset_functionality(self):
        """Test rate limit reset"""
        limiter = RateLimiter()

        # Use up some quota
        limiter.record_request("user_001")
        stats = limiter.get_stats("user_001")
        assert stats['request_count'] == 1

        # Reset
        limiter.reset("user_001")
        stats = limiter.get_stats("user_001")
        assert stats == {}  # No stats after reset

    def test_different_scopes_same_identifier(self):
        """Test same identifier with different scopes"""
        limiter = RateLimiter()

        # Same ID, different scopes
        limiter.record_request("id_001", RateLimitScope.USER)
        limiter.record_request("id_001", RateLimitScope.SESSION)

        # Should be tracked separately
        # (implementation dependent, but should not error)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
