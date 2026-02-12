"""Tests for error recovery system."""

import pytest

from coinbase.error_recovery import (
    ErrorCategory,
    ErrorClassifier,
    RecoveryEngine,
)


def test_classify_transient_error():
    """Test classification of transient errors."""
    error = TimeoutError("Operation timed out")
    context = ErrorClassifier.classify(error)

    assert context.category == ErrorCategory.TRANSIENT
    assert context.recoverable is True
    assert context.strategy == "retry_with_backoff"


def test_classify_permission_error():
    """Test classification of permission errors."""
    error = PermissionError("Access denied")
    context = ErrorClassifier.classify(error)

    assert context.category == ErrorCategory.PERMISSION
    assert context.recoverable is False
    assert context.strategy == "abort"


def test_classify_validation_error():
    """Test classification of validation errors."""
    error = ValueError("Invalid input")
    context = ErrorClassifier.classify(error)

    assert context.category == ErrorCategory.VALIDATION
    assert context.recoverable is False


def test_classify_unknown_error():
    """Test classification of unknown errors."""
    error = RuntimeError("Unknown error")
    context = ErrorClassifier.classify(error)

    assert context.category == ErrorCategory.UNKNOWN
    assert context.recoverable is True


def test_successful_execution():
    """Test successful task execution."""
    engine = RecoveryEngine()

    def task():
        return "success"

    result = engine.execute_with_recovery(task)

    assert result == "success"


def test_retry_on_transient_error():
    """Test retry on transient error."""
    engine = RecoveryEngine(max_attempts=3)
    attempt_count = 0

    def task():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise TimeoutError("Timed out")
        return "success"

    result = engine.execute_with_recovery(task)

    assert result == "success"
    assert attempt_count == 2


def test_max_attempts_exceeded():
    """Test max attempts exceeded."""
    engine = RecoveryEngine(max_attempts=2)

    def task():
        raise TimeoutError("Always fails")

    with pytest.raises(TimeoutError):
        engine.execute_with_recovery(task)


def test_no_retry_on_permission_error():
    """Test no retry on permission error."""
    engine = RecoveryEngine(max_attempts=3)
    attempt_count = 0

    def task():
        nonlocal attempt_count
        attempt_count += 1
        raise PermissionError("Access denied")

    with pytest.raises(PermissionError):
        engine.execute_with_recovery(task)

    # Should only attempt once
    assert attempt_count == 1


def test_exponential_backoff():
    """Test exponential backoff delay."""
    import time

    engine = RecoveryEngine(max_attempts=3, base_delay=0.1)
    start_time = time.time()

    def task():
        raise TimeoutError("Timed out")

    with pytest.raises(TimeoutError):
        engine.execute_with_recovery(task)

    elapsed = time.time() - start_time

    # Should have waited for 2 retries: 0.1s + 0.2s = 0.3s minimum
    assert elapsed >= 0.3
