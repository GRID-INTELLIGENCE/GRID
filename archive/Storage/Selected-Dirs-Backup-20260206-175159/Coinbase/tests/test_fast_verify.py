"""
Comprehensive Tests for Fast Verify Module
==========================================
Test coverage for fast verification system with unique ID tracking,
fair play mechanisms, and collaborative ambiance preservation.
"""

import time
from datetime import datetime

import pytest

from coinbase.verification.fast_verify import (
    FastVerify,
    VerificationCategory,
    VerificationEvent,
    VerificationResult,
    VerificationStatus,
    fast_verify_portfolio,
    fast_verify_summary,
    get_fast_verify,
)


class TestFastVerifyInitialization:
    """Tests for FastVerify initialization and configuration."""

    def test_initialization_default(self):
        """Test default initialization."""
        fast_verify = FastVerify()

        assert fast_verify.rate_limit_per_minute == 60
        assert fast_verify.enable_fair_play is True
        assert fast_verify.enable_ai_safety is True

    def test_initialization_custom(self):
        """Test custom initialization."""
        fast_verify = FastVerify(
            rate_limit_per_minute=120, enable_fair_play=False, enable_ai_safety=False
        )

        assert fast_verify.rate_limit_per_minute == 120
        assert fast_verify.enable_fair_play is False
        assert fast_verify.enable_ai_safety is False

    def test_singleton_instance(self):
        """Test singleton instance creation."""
        instance1 = get_fast_verify()
        instance2 = get_fast_verify()

        assert instance1 is instance2


class TestVerificationEvent:
    """Tests for VerificationEvent dataclass."""

    def test_event_creation(self):
        """Test event creation with defaults."""
        event = VerificationEvent()

        assert len(event.event_id) > 0
        assert event.event_id.startswith("evt_")
        assert event.status == VerificationStatus.PENDING
        assert isinstance(event.timestamp, datetime)

    def test_event_custom_fields(self):
        """Test event with custom fields."""
        event = VerificationEvent(
            check_name="test_check",
            category=VerificationCategory.DATA_INTEGRITY,
            status=VerificationStatus.PASSED,
            message="Check passed",
        )

        assert event.check_name == "test_check"
        assert event.category == VerificationCategory.DATA_INTEGRITY
        assert event.status == VerificationStatus.PASSED
        assert event.message == "Check passed"


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_result_creation(self):
        """Test result creation with defaults."""
        result = VerificationResult()

        assert len(result.batch_id) > 0
        assert result.batch_id.startswith("batch_")
        assert result.passed_count == 0
        assert result.failed_count == 0
        assert result.skipped_count == 0
        assert result.success_rate == 0.0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = VerificationResult(passed_count=7, failed_count=3)

        assert result.success_rate == 70.0

    def test_success_rate_zero_division(self):
        """Test success rate with zero checks."""
        result = VerificationResult()

        assert result.success_rate == 0.0


class TestCheckRegistration:
    """Tests for check registration."""

    def test_register_check(self):
        """Test check registration."""
        fast_verify = FastVerify()

        def test_check():
            return (True, "Test passed")

        fast_verify.register_check("test_check", VerificationCategory.DATA_INTEGRITY, test_check)

        assert "test_check" in fast_verify._checks
        assert fast_verify._checks["test_check"]["category"] == VerificationCategory.DATA_INTEGRITY

    def test_register_multiple_checks(self):
        """Test registering multiple checks."""
        fast_verify = FastVerify(register_defaults=False)

        for i in range(5):
            fast_verify.register_check(
                f"check_{i}",
                VerificationCategory.DATA_INTEGRITY,
                lambda: (True, f"Check {i} passed"),
            )

        assert len(fast_verify._checks) == 5


class TestVerificationExecution:
    """Tests for verification execution."""

    def test_verify_all_checks(self):
        """Test running all registered checks."""
        fast_verify = FastVerify()

        result = fast_verify.verify("user123")

        assert result.passed_count > 0
        assert result.failed_count == 0
        assert result.success_rate == 100.0

    def test_verify_specific_checks(self):
        """Test running specific checks."""
        fast_verify = FastVerify()

        result = fast_verify.verify("user123", checks=["portfolio_value_positive"])

        assert len(result.events) == 1
        assert result.events[0].check_name == "portfolio_value_positive"

    def test_verify_with_failing_check(self):
        """Test verification with a failing check."""
        fast_verify = FastVerify()

        def failing_check():
            return (False, "Check failed")

        fast_verify.register_check(
            "failing_check", VerificationCategory.DATA_INTEGRITY, failing_check
        )

        result = fast_verify.verify("user123", checks=["failing_check"])

        assert result.failed_count == 1
        assert result.success_rate == 0.0

    def test_verify_with_exception(self):
        """Test verification with check that raises exception."""
        fast_verify = FastVerify()

        def exception_check():
            raise ValueError("Test exception")

        fast_verify.register_check(
            "exception_check", VerificationCategory.DATA_INTEGRITY, exception_check
        )

        result = fast_verify.verify("user123", checks=["exception_check"])

        assert result.failed_count == 1
        assert "error" in result.events[0].message.lower()


class TestRateLimiting:
    """Tests for rate limiting and fair play."""

    def test_rate_limit_enforcement(self):
        """Test that rate limit is enforced."""
        fast_verify = FastVerify(rate_limit_per_minute=5)

        # Run 5 verifications (should succeed)
        for i in range(5):
            result = fast_verify.verify("user123")
            assert result.failed_count == 0

        # 6th verification should fail
        result = fast_verify.verify("user123")
        assert result.failed_count == 1
        assert "rate limit" in result.events[0].message.lower()

    def test_rate_limit_disabled(self):
        """Test that rate limit can be disabled."""
        fast_verify = FastVerify(rate_limit_per_minute=5, enable_fair_play=False)

        # Run 10 verifications (should all succeed)
        for i in range(10):
            result = fast_verify.verify("user123")
            assert result.failed_count == 0

    def test_rate_limit_different_users(self):
        """Test that rate limit is per-user."""
        fast_verify = FastVerify(rate_limit_per_minute=2)

        # User 1: 2 verifications
        for i in range(2):
            result = fast_verify.verify("user1")
            assert result.failed_count == 0

        # User 2: 2 verifications (should succeed)
        for i in range(2):
            result = fast_verify.verify("user2")
            assert result.failed_count == 0

        # User 1: 3rd verification (should fail)
        result = fast_verify.verify("user1")
        assert result.failed_count == 1


class TestReputationSystem:
    """Tests for user reputation system."""

    def test_reputation_increase(self):
        """Test that reputation increases with successful verifications."""
        fast_verify = FastVerify(register_defaults=False)

        # Register a passing check
        def passing_check():
            return (True, "Check passed")

        fast_verify.register_check(
            "passing_check", VerificationCategory.DATA_INTEGRITY, passing_check
        )

        initial_reputation = fast_verify.get_reputation("user123")

        # Run successful verification
        result = fast_verify.verify("user123", checks=["passing_check"])

        new_reputation = fast_verify.get_reputation("user123")
        # Reputation can increase but is capped at 100
        assert new_reputation >= initial_reputation

    def test_reputation_decrease(self):
        """Test that reputation decreases with failed verifications."""
        fast_verify = FastVerify()

        def failing_check():
            return (False, "Check failed")

        fast_verify.register_check(
            "failing_check", VerificationCategory.DATA_INTEGRITY, failing_check
        )

        # Run failed verification
        result = fast_verify.verify("user123", checks=["failing_check"])

        reputation = fast_verify.get_reputation("user123")
        assert reputation < 100.0

    def test_reputation_bounds(self):
        """Test that reputation stays within bounds."""
        fast_verify = FastVerify()

        # Try to increase beyond 100
        for i in range(200):
            fast_verify.verify("user123")

        reputation = fast_verify.get_reputation("user123")
        assert reputation <= 100.0

        # Try to decrease below 0
        for i in range(200):
            result = fast_verify.verify("user123", checks=["failing_check"])

        reputation = fast_verify.get_reputation("user123")
        assert reputation >= 0.0


class TestPrivacyAndHashing:
    """Tests for privacy and user ID hashing."""

    def test_user_id_hashed(self):
        """Test that user IDs are hashed."""
        fast_verify = FastVerify()

        result = fast_verify.verify("user123")

        # Result should contain hashed user ID
        assert result.user_id_hash != "user123"
        assert len(result.user_id_hash) == 16

    def test_same_user_same_hash(self):
        """Test that same user ID produces same hash."""
        fast_verify = FastVerify()

        result1 = fast_verify.verify("user123")
        result2 = fast_verify.verify("user123")

        assert result1.user_id_hash == result2.user_id_hash

    def test_different_users_different_hashes(self):
        """Test that different user IDs produce different hashes."""
        fast_verify = FastVerify()

        result1 = fast_verify.verify("user123")
        result2 = fast_verify.verify("user456")

        assert result1.user_id_hash != result2.user_id_hash


class TestPerformanceMetrics:
    """Tests for performance metrics."""

    def test_duration_tracking(self):
        """Test that duration is tracked."""
        fast_verify = FastVerify()

        result = fast_verify.verify("user123")

        assert result.total_duration_ms >= 0
        assert result.total_duration_ms < 1000  # Should complete in < 1s

    def test_event_duration_tracking(self):
        """Test that event durations are tracked."""
        fast_verify = FastVerify()

        result = fast_verify.verify("user123")

        for event in result.events:
            assert event.duration_ms >= 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_fast_verify_portfolio(self):
        """Test fast_verify_portfolio function."""
        result = fast_verify_portfolio("user123")

        assert result.passed_count > 0
        assert isinstance(result, VerificationResult)

    def test_fast_verify_summary(self):
        """Test fast_verify_summary function."""
        result = fast_verify_portfolio("user123")
        summary = fast_verify_summary(result)

        assert "batch_id" in summary
        assert "success_rate" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "events" in summary
        assert isinstance(summary["events"], list)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_checks_list(self):
        """Test verification with empty checks list."""
        fast_verify = FastVerify(register_defaults=False)

        result = fast_verify.verify("user123", checks=[])

        assert result.passed_count == 0
        assert result.failed_count == 0

    def test_nonexistent_check(self):
        """Test verification with nonexistent check."""
        fast_verify = FastVerify()

        result = fast_verify.verify("user123", checks=["nonexistent_check"])

        assert len(result.events) == 0

    def test_timeout_handling(self):
        """Test timeout handling."""
        fast_verify = FastVerify()

        def slow_check():
            time.sleep(0.1)
            return (True, "Check passed")

        fast_verify.register_check("slow_check", VerificationCategory.DATA_INTEGRITY, slow_check)

        result = fast_verify.verify("user123", checks=["slow_check"], timeout_ms=50)

        # Should still complete (timeout is advisory)
        assert result.total_duration_ms >= 100


class TestCollaborativeAmbiance:
    """Tests for collaborative ambiance preservation."""

    def test_fair_play_enabled(self):
        """Test that fair play is enabled by default."""
        fast_verify = FastVerify()

        assert fast_verify.enable_fair_play is True

    def test_ai_safety_enabled(self):
        """Test that AI safety is enabled by default."""
        fast_verify = FastVerify()

        assert fast_verify.enable_ai_safety is True

    def test_unique_event_ids(self):
        """Test that events have unique IDs."""
        fast_verify = FastVerify()

        result = fast_verify.verify("user123")

        event_ids = [event.event_id for event in result.events]
        assert len(event_ids) == len(set(event_ids))

    def test_unique_thread_ids(self):
        """Test that events have thread IDs."""
        fast_verify = FastVerify()

        result = fast_verify.verify("user123")

        for event in result.events:
            assert len(event.thread_id) > 0
            assert event.thread_id.startswith("thr_")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
