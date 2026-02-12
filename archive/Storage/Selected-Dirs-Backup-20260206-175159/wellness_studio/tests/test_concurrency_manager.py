"""
Integrity Test Suite - Dynamic Safety-Aware IO Concurrency Manager
Tests concurrent execution, safety throttling, and audit integration
"""
import time
import threading
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

import sys
sys.path.insert(0, str(__file__).rsplit('tests', 1)[0] + 'src')

from wellness_studio.security.concurrency_manager import (
    DynamicSafetyIOManager,
    DynamicSafetyGuard,
    ConcurrencyStats
)
from wellness_studio.security.audit_logger import AuditLogger, AuditEventType
from wellness_studio.security.rate_limiter import RateLimiter, RateLimitConfig
from wellness_studio.security.ai_safety import ContentSafetyFilter


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger for testing"""
    logger = Mock(spec=AuditLogger)
    logger.log_event = Mock()
    logger.log_error = Mock()
    return logger


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter"""
    limiter = Mock(spec=RateLimiter)
    status = Mock()
    status.allowed = True
    limiter.check_rate_limit = Mock(return_value=status)
    return limiter


@pytest.fixture
def mock_safety_filter():
    """Create a mock safety filter"""
    filter = Mock(spec=ContentSafetyFilter)
    filter.get_safety_summary = Mock(return_value={
        'by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
        'total_violations': 0
    })
    return filter


@pytest.fixture
def io_manager(mock_audit_logger, mock_rate_limiter):
    """Create IO manager with mocked dependencies"""
    return DynamicSafetyIOManager(
        audit_logger=mock_audit_logger,
        rate_limiter=mock_rate_limiter,
        max_concurrency=5,
        min_concurrency=1
    )


@pytest.fixture
def safety_guard(io_manager, mock_safety_filter):
    """Create safety guard with mocked dependencies"""
    return DynamicSafetyGuard(
        io_manager=io_manager,
        safety_filter=mock_safety_filter,
        monitor_interval=1  # Fast for testing
    )


# ============================================================================
# TEST: INITIALIZATION
# ============================================================================

class TestInitialization:
    """Test proper initialization of concurrency components"""
    
    def test_io_manager_initializes_with_defaults(self, mock_audit_logger):
        """Verify IO manager starts with expected default state"""
        manager = DynamicSafetyIOManager(
            audit_logger=mock_audit_logger,
            max_concurrency=10,
            min_concurrency=2
        )
        
        assert manager.max_concurrency == 10
        assert manager.min_concurrency == 2
        assert manager.current_concurrency == 10
        assert manager.active_count == 0
        assert manager.completed_count == 0
        assert manager.blocked_count == 0
        assert manager.safety_throttle_factor == 0.0
        assert manager.is_degraded is False
    
    def test_io_manager_logs_initialization(self, mock_audit_logger):
        """Verify initialization is logged"""
        manager = DynamicSafetyIOManager(
            audit_logger=mock_audit_logger,
            max_concurrency=5
        )
        
        mock_audit_logger.log_event.assert_called_once()
        call_args = mock_audit_logger.log_event.call_args
        assert call_args.kwargs['action'] == "concurrency_manager_initialized"
        assert call_args.kwargs['details']['max_concurrency'] == 5


# ============================================================================
# TEST: SAFE IO EXECUTION
# ============================================================================

class TestSafeIOExecution:
    """Test the execute_safe_io method"""
    
    def test_successful_io_execution(self, io_manager):
        """Verify successful IO operations complete and are logged"""
        def sample_io():
            return "success_result"
        
        result = io_manager.execute_safe_io(
            io_func=sample_io,
            resource_id="test_resource_001",
            user_id="test_user"
        )
        
        assert result == "success_result"
        assert io_manager.completed_count == 1
        assert io_manager.active_count == 0  # Should be released
    
    def test_io_execution_with_args(self, io_manager):
        """Verify IO functions receive args and kwargs correctly"""
        def sample_io(a, b, keyword=None):
            return f"{a}-{b}-{keyword}"
        
        result = io_manager.execute_safe_io(
            io_func=sample_io,
            resource_id="test_resource_002",
            user_id="test_user",
            a="first",
            b="second",
            keyword="third"
        )
        
        assert result == "first-second-third"
    
    def test_io_blocked_by_rate_limit(self, io_manager, mock_rate_limiter):
        """Verify rate-limited requests are blocked"""
        mock_rate_limiter.check_rate_limit.return_value.allowed = False
        
        def sample_io():
            return "should_not_execute"
        
        result = io_manager.execute_safe_io(
            io_func=sample_io,
            resource_id="test_resource_blocked",
            user_id="rate_limited_user"
        )
        
        assert result is None
        assert io_manager.blocked_count == 1
    
    def test_io_exception_handling(self, io_manager, mock_audit_logger):
        """Verify exceptions in IO functions are caught and logged"""
        def failing_io():
            raise ValueError("Simulated IO failure")
        
        result = io_manager.execute_safe_io(
            io_func=failing_io,
            resource_id="test_resource_fail",
            user_id="test_user"
        )
        
        assert result is None
        mock_audit_logger.log_error.assert_called()
        call_args = mock_audit_logger.log_error.call_args
        assert call_args.kwargs['error_type'] == "io_execution_failed"


# ============================================================================
# TEST: CONCURRENCY CONTROL
# ============================================================================

class TestConcurrencyControl:
    """Test concurrent execution limits and slot management"""
    
    def test_concurrent_slot_limit(self, io_manager):
        """Verify only max_concurrency tasks run simultaneously"""
        execution_log = []
        barrier = threading.Barrier(io_manager.max_concurrency + 1)
        
        def slow_io(task_id):
            execution_log.append(('start', task_id, time.time()))
            time.sleep(0.1)
            execution_log.append(('end', task_id, time.time()))
            return task_id
        
        threads = []
        for i in range(io_manager.max_concurrency + 2):
            t = threading.Thread(
                target=io_manager.execute_safe_io,
                kwargs={
                    'io_func': slow_io,
                    'resource_id': f"resource_{i}",
                    'user_id': "concurrent_user",
                    'task_id': i
                }
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=5)
        
        # All tasks should complete
        assert io_manager.completed_count == io_manager.max_concurrency + 2
    
    def test_stats_reflect_current_state(self, io_manager):
        """Verify get_stats returns accurate state"""
        stats = io_manager.get_stats()
        
        assert isinstance(stats, ConcurrencyStats)
        assert stats.active_slots == 0
        assert stats.total_slots == io_manager.max_concurrency
        assert stats.completed_tasks == 0
        assert stats.blocked_tasks == 0
        assert stats.safety_throttle_level == 0.0


# ============================================================================
# TEST: DYNAMIC SAFETY ADJUSTMENT
# ============================================================================

class TestDynamicSafetyAdjustment:
    """Test dynamic concurrency scaling based on safety scores"""
    
    def test_full_safety_maintains_max_concurrency(self, io_manager):
        """Verify safety_score=1.0 keeps max concurrency"""
        io_manager._adjust_concurrency(safety_score=1.0)
        
        assert io_manager.current_concurrency == io_manager.max_concurrency
        assert io_manager.safety_throttle_factor == 0.0
        assert io_manager.is_degraded is False
    
    def test_low_safety_reduces_concurrency(self, io_manager):
        """Verify safety_score=0.2 reduces concurrency significantly"""
        io_manager._adjust_concurrency(safety_score=0.2)
        
        # Expected: 1 + (5-1) * 0.2 = 1.8 → 1
        assert io_manager.current_concurrency <= 2
        assert io_manager.safety_throttle_factor > 0.5
        assert io_manager.is_degraded is True
    
    def test_zero_safety_reaches_minimum(self, io_manager):
        """Verify safety_score=0.0 reduces to min_concurrency"""
        io_manager._adjust_concurrency(safety_score=0.0)
        
        assert io_manager.current_concurrency == io_manager.min_concurrency
        assert io_manager.is_degraded is True
    
    def test_adjustment_logs_config_change(self, io_manager, mock_audit_logger):
        """Verify concurrency adjustments are logged"""
        mock_audit_logger.log_event.reset_mock()
        
        io_manager._adjust_concurrency(safety_score=0.5)
        
        # Should log a config change for the adjustment
        calls = [c for c in mock_audit_logger.log_event.call_args_list 
                 if c.kwargs.get('action') == 'concurrency_dynamic_adjustment']
        assert len(calls) == 1


# ============================================================================
# TEST: SAFETY GUARD MONITORING
# ============================================================================

class TestSafetyGuardMonitoring:
    """Test the DynamicSafetyGuard background monitoring"""
    
    def test_guard_starts_and_stops(self, safety_guard):
        """Verify guard thread lifecycle"""
        safety_guard.start_monitoring()
        
        assert safety_guard._thread is not None
        assert safety_guard._thread.is_alive()
        
        safety_guard.stop()
        time.sleep(0.5)
        
        assert not safety_guard._thread.is_alive()
    
    def test_guard_adjusts_on_critical_violations(self, safety_guard, mock_safety_filter):
        """Verify guard reduces concurrency when violations detected"""
        # Simulate critical violations
        mock_safety_filter.get_safety_summary.return_value = {
            'by_severity': {'critical': 2, 'high': 10, 'medium': 0, 'low': 0},
            'total_violations': 12
        }
        
        initial_concurrency = safety_guard.io_manager.current_concurrency
        
        safety_guard.start_monitoring()
        time.sleep(1.5)  # Wait for monitor loop
        safety_guard.stop()
        
        # Concurrency should have been reduced
        assert safety_guard.io_manager.current_concurrency < initial_concurrency
    
    def test_guard_recovers_when_safe(self, safety_guard, mock_safety_filter):
        """Verify guard restores concurrency when violations clear"""
        # First reduce
        mock_safety_filter.get_safety_summary.return_value = {
            'by_severity': {'critical': 2, 'high': 0},
            'total_violations': 2
        }
        safety_guard.io_manager._adjust_concurrency(0.3)
        reduced = safety_guard.io_manager.current_concurrency
        
        # Then clear violations
        mock_safety_filter.get_safety_summary.return_value = {
            'by_severity': {'critical': 0, 'high': 0},
            'total_violations': 0
        }
        
        safety_guard.start_monitoring()
        time.sleep(1.5)
        safety_guard.stop()
        
        # Should be restored
        assert safety_guard.io_manager.current_concurrency > reduced


# ============================================================================
# TEST: AUDIT TRAIL INTEGRITY
# ============================================================================

class TestAuditTrailIntegrity:
    """Test complete audit logging for all operations"""
    
    def test_io_start_and_success_logged(self, io_manager, mock_audit_logger):
        """Verify IO operations log start and success events"""
        def sample_io():
            return "result"
        
        mock_audit_logger.log_event.reset_mock()
        
        io_manager.execute_safe_io(
            io_func=sample_io,
            resource_id="audit_test_resource",
            user_id="audit_user"
        )
        
        actions = [c.kwargs['action'] for c in mock_audit_logger.log_event.call_args_list]
        assert 'concurrent_io_started' in actions
        assert 'concurrent_io_success' in actions
    
    def test_blocked_io_logged_as_violation(self, io_manager, mock_audit_logger, mock_rate_limiter):
        """Verify blocked IO is logged as safety violation"""
        mock_rate_limiter.check_rate_limit.return_value.allowed = False
        mock_audit_logger.log_event.reset_mock()
        
        io_manager.execute_safe_io(
            io_func=lambda: None,
            resource_id="blocked_resource",
            user_id="blocked_user"
        )
        
        calls = mock_audit_logger.log_event.call_args_list
        violation_calls = [c for c in calls if c.kwargs.get('action') == 'io_concurrency_blocked']
        assert len(violation_calls) == 1
        assert violation_calls[0].kwargs['status'] == 'blocked'
    
    def test_shutdown_logged(self, io_manager, mock_audit_logger):
        """Verify shutdown is logged with completion stats"""
        io_manager.execute_safe_io(io_func=lambda: "x", resource_id="r", user_id="u")
        mock_audit_logger.log_event.reset_mock()
        
        io_manager.shutdown()
        
        calls = [c for c in mock_audit_logger.log_event.call_args_list 
                 if c.kwargs.get('action') == 'concurrency_manager_shutdown']
        assert len(calls) == 1
        assert calls[0].kwargs['details']['completed'] == 1


# ============================================================================
# TEST: EDGE CASES & STRESS
# ============================================================================

class TestEdgeCasesAndStress:
    """Test edge cases and stress scenarios"""
    
    def test_rapid_concurrent_requests(self, io_manager):
        """Stress test with rapid concurrent requests"""
        results = []
        
        def fast_io(i):
            return i * 2
        
        threads = []
        for i in range(50):
            t = threading.Thread(
                target=lambda idx=i: results.append(
                    io_manager.execute_safe_io(
                        io_func=fast_io,
                        resource_id=f"stress_{idx}",
                        user_id="stress_user",
                        i=idx
                    )
                )
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        assert io_manager.completed_count == 50
        assert len([r for r in results if r is not None]) == 50
    
    def test_no_rate_limiter(self, mock_audit_logger):
        """Verify IO works without rate limiter"""
        manager = DynamicSafetyIOManager(
            audit_logger=mock_audit_logger,
            rate_limiter=None,  # No rate limiter
            max_concurrency=3
        )
        
        result = manager.execute_safe_io(
            io_func=lambda: "no_limit_result",
            resource_id="no_limit_resource",
            user_id="user"
        )
        
        assert result == "no_limit_result"
        assert manager.completed_count == 1


# ============================================================================
# MAIN RUNNER
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
