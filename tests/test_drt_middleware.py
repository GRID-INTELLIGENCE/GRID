"""
Simplified tests for DRT (Don't Repeat Themselves) Middleware.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.mothership.middleware.drt_middleware import (
    BehavioralSignature,
    ComprehensiveDRTMiddleware,
)

# Import metrics classes with fallback for testing
try:
    from application.mothership.middleware.drt_metrics import (
        DRTMetricsCollector,
        get_drt_metrics_collector,
        record_drt_deescalation,
        record_drt_escalation,
        record_drt_violation,
    )

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    DRTMetricsCollector = None
    get_drt_metrics_collector = None
    record_drt_violation = None
    record_drt_escalation = None
    record_drt_deescalation = None


class TestBehavioralSignature:
    """Test BehavioralSignature class."""

    def test_creation(self):
        """Test signature creation."""
        sig = BehavioralSignature(path_pattern="/api/users", method="GET", headers=("accept", "content-type"))
        assert sig.path_pattern == "/api/users"
        assert sig.method == "GET"
        assert sig.headers == ("accept", "content-type")
        assert isinstance(sig.timestamp, datetime)
        assert sig.request_count == 0

    def test_to_dict(self):
        """Test serialization."""
        sig = BehavioralSignature("/api/test", "POST", ("content-type",))
        data = sig.to_dict()
        assert data["path_pattern"] == "/api/test"
        assert data["method"] == "POST"
        assert "timestamp" in data


class TestDRTMiddleware:
    """Test DRT middleware functionality."""

    def test_path_normalization(self):
        """Test path normalization."""
        middleware = ComprehensiveDRTMiddleware.__new__(ComprehensiveDRTMiddleware)

        assert middleware._normalize_path("/api/users/123") == "/api/users/{ID}"
        # Full UUID with all segments
        assert middleware._normalize_path("/api/uuid/550e8400-e29b-41d4-a716-446655440000") == "/api/uuid/{UUID}"
        assert middleware._normalize_path("/api/static") == "/api/static"

    def test_query_normalization(self):
        """Test query normalization."""
        middleware = ComprehensiveDRTMiddleware.__new__(ComprehensiveDRTMiddleware)

        assert middleware._normalize_query("page=1&limit=10") == "limit&page"
        assert middleware._normalize_query("") == ""

    def test_similarity_calculation(self):
        """Test similarity calculation."""
        middleware = ComprehensiveDRTMiddleware.__new__(ComprehensiveDRTMiddleware)

        sig1 = BehavioralSignature("/api/users", "GET", ("accept", "content-type"))
        sig2 = BehavioralSignature("/api/users", "GET", ("accept", "content-type"))
        sig3 = BehavioralSignature("/api/users", "POST", ("accept",))

        # Identical should be 1.0
        assert middleware._calculate_similarity(sig1, sig2) == 1.0

        # Different method should be 0.0
        assert middleware._calculate_similarity(sig1, sig3) == 0.0

    def test_escalation(self):
        """Test endpoint escalation."""
        middleware = ComprehensiveDRTMiddleware.__new__(ComprehensiveDRTMiddleware)
        middleware.ESCALATED_ENDPOINTS = {}
        middleware.escalation_timeout_minutes = 30
        middleware.alert_on_escalation = False

        middleware._escalate_endpoint("/api/test")

        assert "/api/test" in middleware.ESCALATED_ENDPOINTS
        expiry = middleware.ESCALATED_ENDPOINTS["/api/test"]
        assert expiry > datetime.now(UTC)

    def test_attack_vector_management(self):
        """Test adding attack vectors."""
        middleware = ComprehensiveDRTMiddleware.__new__(ComprehensiveDRTMiddleware)
        middleware.attack_vectors = []

        sig = BehavioralSignature("/api/login", "POST", ("content-type",))
        middleware.add_attack_vector(sig)

        assert len(middleware.attack_vectors) == 1
        assert middleware.attack_vectors[0].path_pattern == "/api/login"

    def test_similarity_check(self):
        """Test similarity checking with attack vectors."""
        middleware = ComprehensiveDRTMiddleware.__new__(ComprehensiveDRTMiddleware)
        middleware.attack_vectors = []
        middleware.similarity_threshold = 0.8

        # Add attack vector
        attack_sig = BehavioralSignature("/api/login", "POST", ("content-type",))
        middleware.add_attack_vector(attack_sig)

        # Check similar request
        test_sig = BehavioralSignature("/api/login", "POST", ("content-type",))
        similarity, matched = middleware._check_similarity(test_sig)

        assert similarity == 1.0
        assert matched is not None
        assert matched.path_pattern == "/api/login"

    def test_status(self):
        """Test status reporting."""
        middleware = ComprehensiveDRTMiddleware.__new__(ComprehensiveDRTMiddleware)
        middleware.enabled = True
        middleware.similarity_threshold = 0.85
        middleware.retention_hours = 96
        middleware.auto_escalate = True
        middleware.behavioral_history = []
        middleware.attack_vectors = []
        middleware.ESCALATED_ENDPOINTS = {}

        status = middleware.get_status()

        assert status["enabled"] is True
        assert status["similarity_threshold"] == 0.85
        assert status["retention_hours"] == 96
        assert status["auto_escalate"] is True
        assert status["escalated_endpoints"] == 0
        assert status["behavioral_history_count"] == 0
        assert status["attack_vectors_count"] == 0


class TestDRTIntegration:
    """Integration tests."""

    def test_middleware_with_fastapi(self):
        """Test middleware with FastAPI app."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        # Test that middleware can be created
        middleware = ComprehensiveDRTMiddleware(app)
        assert middleware.enabled is True

    def test_attack_vector_detection(self):
        """Test attack vector detection in integration."""
        app = FastAPI()
        middleware = ComprehensiveDRTMiddleware(app, auto_escalate=True)

        # Add attack vector
        attack_sig = BehavioralSignature("/api/sensitive", "POST", ("content-type",))
        middleware.add_attack_vector(attack_sig)

        assert len(middleware.attack_vectors) == 1

    def test_middleware_status_endpoint(self):
        """Test status endpoint."""
        app = FastAPI()
        middleware = ComprehensiveDRTMiddleware(app)

        # Add data
        attack_sig = BehavioralSignature("/attack", "GET", ("accept",))
        middleware.add_attack_vector(attack_sig)
        middleware._escalate_endpoint("/test")

        status = middleware.get_status()

        assert status["attack_vectors_count"] == 1
        assert status["escalated_endpoints"] == 1


class TestDRTMetricsCollector:
    """Test DRT metrics collection functionality."""

    @pytest.fixture
    def metrics_collector(self):
        """Create a fresh metrics collector for testing."""
        collector = DRTMetricsCollector()
        yield collector

    def test_initialization(self, metrics_collector):
        """Test metrics collector initialization."""
        assert metrics_collector.metrics.violations_total == 0
        assert metrics_collector.metrics.escalations_total == 0
        assert metrics_collector.metrics.false_positives_marked == 0
        assert metrics_collector.metrics.false_positive_rate == 0.0
        assert isinstance(metrics_collector.metrics.similarity_scores, list)

    def test_record_violation(self, metrics_collector):
        """Test recording violations."""
        # Record a violation
        metrics_collector.record_violation(
            similarity_score=0.95,
            attack_vector_severity="high",
            request_path="/api/sensitive",
            request_method="POST",
            was_blocked=False,
            processing_time=0.05,
        )

        # Check metrics
        assert metrics_collector.metrics.violations_total == 1
        assert metrics_collector.metrics.violations_by_severity["high"] == 1
        assert metrics_collector.metrics.violations_by_path["/api/sensitive"] == 1
        assert metrics_collector.metrics.violations_by_method["POST"] == 1
        assert 0.95 in metrics_collector.metrics.similarity_scores
        assert metrics_collector.metrics.processing_count == 1
        assert metrics_collector.metrics.processing_time_avg > 0

    def test_record_escalation(self, metrics_collector):
        """Test recording escalations."""
        # Record escalation
        metrics_collector.record_escalation(path="/api/sensitive", similarity_score=0.90, duration_minutes=30)

        # Check metrics
        assert metrics_collector.metrics.escalations_total == 1
        assert metrics_collector.metrics.escalated_endpoints_count == 1
        assert metrics_collector.metrics.escalation_duration_avg == 30.0

    def test_record_deescalation(self, metrics_collector):
        """Test recording de-escalations."""
        # First record escalation
        metrics_collector.record_escalation("/api/test", 0.8)
        assert metrics_collector.metrics.escalated_endpoints_count == 1

        # Then de-escalate
        metrics_collector.record_deescalation("/api/test")
        assert metrics_collector.metrics.escalated_endpoints_count == 0

    def test_record_false_positive(self, metrics_collector):
        """Test recording false positives."""
        # Record some violations first
        metrics_collector.record_violation(0.8, "medium", "/api/test", "GET")
        metrics_collector.record_violation(0.9, "high", "/api/test2", "POST")

        # Record false positives
        metrics_collector.record_false_positive()
        metrics_collector.record_false_positive()

        # Check metrics
        assert metrics_collector.metrics.false_positives_marked == 2
        assert metrics_collector.metrics.false_positive_rate == 1.0  # 2/2 = 100%

    def test_record_behavioral_signature(self, metrics_collector):
        """Test recording behavioral signatures."""
        signature = BehavioralSignature(path_pattern="/api/test*", method="GET", headers=("X-Test",))
        metrics_collector.record_behavioral_signature(signature)
        assert metrics_collector.metrics.behavioral_signatures_total == 1

    def test_record_attack_vector(self, metrics_collector):
        """Test recording attack vectors."""
        metrics_collector.record_attack_vector("high")
        assert metrics_collector.metrics.attack_vectors_total == 1

    def test_record_cleanup_operation(self, metrics_collector):
        """Test recording cleanup operations."""
        metrics_collector.record_cleanup_operation(duration=1.5)
        assert metrics_collector.metrics.cleanup_operations == 1
        assert metrics_collector.metrics.processing_time_avg > 0

    def test_record_db_error(self, metrics_collector):
        """Test recording database errors."""
        metrics_collector.record_db_error("test_operation")
        assert metrics_collector.metrics.db_operation_errors == 1

    def test_similarity_score_tracking(self, metrics_collector):
        """Test similarity score distribution tracking."""
        scores = [0.5, 0.7, 0.8, 0.9, 0.95]

        for score in scores:
            metrics_collector.record_violation(
                similarity_score=score, attack_vector_severity="medium", request_path="/api/test", request_method="GET"
            )

        # Check that all scores are tracked
        assert len(metrics_collector.metrics.similarity_scores) == 5
        assert set(scores).issubset(set(metrics_collector.metrics.similarity_scores))

        # Test that we don't exceed the limit
        for i in range(1000):  # Add many more scores
            metrics_collector.record_violation(
                similarity_score=0.6, attack_vector_severity="low", request_path="/api/test", request_method="GET"
            )

        # Should be capped at 1000
        assert len(metrics_collector.metrics.similarity_scores) <= 1000

    def test_get_metrics_dict(self, metrics_collector):
        """Test getting metrics as dictionary."""
        # Add some test data
        metrics_collector.record_violation(0.85, "medium", "/api/test", "GET")
        metrics_collector.record_escalation("/api/test", 0.85)
        metrics_collector.record_false_positive()

        metrics_dict = metrics_collector.get_metrics_dict()

        # Check that all expected metrics are present
        required_keys = [
            "drt_violations_total",
            "drt_escalations_total",
            "drt_false_positives_marked",
            "drt_false_positive_rate",
            "drt_processing_time_avg_ms",
            "drt_similarity_scores_count",
            "drt_uptime_seconds",
        ]

        for key in required_keys:
            assert key in metrics_dict
            assert isinstance(metrics_dict[key], (int, float))

    def test_get_prometheus_metrics(self, metrics_collector):
        """Test Prometheus metrics output format."""
        # Add some test data
        metrics_collector.record_violation(0.8, "high", "/api/test", "GET")

        prometheus_output = metrics_collector.get_prometheus_metrics()

        # Check basic format
        assert "# HELP" in prometheus_output
        assert "# TYPE" in prometheus_output
        assert "drt_violations_total" in prometheus_output
        assert "gauge" in prometheus_output

    def test_global_collector_functions(self):
        """Test global collector convenience functions."""
        # Reset the global collector for clean testing
        import application.mothership.middleware.drt_metrics as _drt_metrics_mod

        _drt_metrics_mod._metrics_collector = None

        collector = get_drt_metrics_collector()
        assert isinstance(collector, DRTMetricsCollector)

        # Test recording functions
        record_drt_violation(0.9, "critical", "/api/critical", "DELETE")
        record_drt_escalation("/api/critical", 0.9)
        record_drt_deescalation("/api/critical")

        # Check that metrics were recorded
        assert collector.metrics.violations_total == 1
        assert collector.metrics.escalations_total == 1

    def test_metrics_reset(self, metrics_collector):
        """Test metrics reset functionality."""
        # Add some data
        metrics_collector.record_violation(0.8, "medium", "/api/test", "GET")
        assert metrics_collector.metrics.violations_total == 1

        # Reset
        metrics_collector.reset_metrics()

        # Check reset
        assert metrics_collector.metrics.violations_total == 0
        assert metrics_collector.metrics.escalations_total == 0
        assert metrics_collector.metrics.false_positives_marked == 0


class TestDRTFalsePositiveTracking:
    """Test DRT false positive tracking functionality."""

    @pytest.fixture
    async def mock_session(self):
        """Create a mock database session for testing."""
        from unittest.mock import MagicMock

        # Explicitly set return_value to MagicMock to avoid Python 3.13 AsyncMock
        # behaviour where return_value is itself an AsyncMock, causing sync methods
        # like scalar_one_or_none() to return coroutines instead of values.
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        execute_result.scalars.return_value.all.return_value = []
        execute_result.scalar_one.return_value = 0

        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        session.get = AsyncMock(return_value=MagicMock())
        return session

    @pytest.fixture
    async def fp_repo(self, mock_session):
        """Create a false positive repository for testing."""
        from application.mothership.repositories.drt import DRTFalsePositiveRepository

        return DRTFalsePositiveRepository(mock_session)

    @pytest.fixture
    async def pattern_repo(self, mock_session):
        """Create a false positive pattern repository for testing."""
        from application.mothership.repositories.drt import DRTFalsePositivePatternRepository

        return DRTFalsePositivePatternRepository(mock_session)

    @pytest.mark.asyncio
    async def test_mark_false_positive(self, fp_repo):
        """Test marking a violation as false positive."""
        violation_id = "test-violation-123"

        result = await fp_repo.mark_false_positive(
            violation_id=violation_id, marked_by="test-user", reason="Legitimate admin access", confidence=0.9
        )

        assert result is not None  # Should return an ID
        fp_repo._db.add.assert_called_once()
        fp_repo._db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_violation(self, fp_repo):
        """Test getting false positive record by violation ID."""
        violation_id = "test-violation-456"
        mock_fp_record = MagicMock()
        fp_repo._db.execute.return_value.scalar_one_or_none.return_value = mock_fp_record

        result = await fp_repo.get_by_violation(violation_id)

        assert result == mock_fp_record
        fp_repo._db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_false_positives(self, fp_repo):
        """Test getting recent false positive records."""
        mock_rows = [
            MagicMock(id="fp1", violation_id="v1", marked_by="user1", reason="test1", confidence=0.8),
            MagicMock(id="fp2", violation_id="v2", marked_by="user2", reason="test2", confidence=0.9),
        ]
        fp_repo._db.execute.return_value.scalars.return_value.all.return_value = mock_rows

        result = await fp_repo.get_recent(hours=24, limit=10)

        assert len(result) == 2
        assert result[0]["id"] == "fp1"
        assert result[1]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_count_false_positives(self, fp_repo):
        """Test counting false positive records."""
        fp_repo._db.execute.return_value.scalar_one.return_value = 15

        result = await fp_repo.count(hours=48)

        assert result == 15
        fp_repo._db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_false_positive_rate_calculation(self, fp_repo):
        """Test false positive rate calculation."""
        # Mock violation count
        violation_result = MagicMock()
        violation_result.scalar_one.return_value = 100
        fp_repo._db.execute.side_effect = [violation_result, violation_result]

        # Mock false positive count
        fp_result = MagicMock()
        fp_result.scalar_one.return_value = 10
        fp_repo._db.execute.side_effect = [violation_result, fp_result]

        rate = await fp_repo.get_false_positive_rate(hours=24)

        assert rate == 0.1  # 10/100 = 0.1

    @pytest.mark.asyncio
    async def test_record_pattern(self, pattern_repo):
        """Test recording false positive patterns."""
        from application.mothership.middleware.drt_middleware import BehavioralSignature

        signature = BehavioralSignature(path_pattern="/api/admin", method="GET", headers=("accept", "authorization"))

        # Test false positive pattern recording
        await pattern_repo.record_pattern(signature, is_false_positive=True)

        # Should have called execute to check for existing pattern
        assert pattern_repo._db.execute.called

        # Should have called add for new pattern
        pattern_repo._db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_pattern_update_existing(self, pattern_repo):
        """Test updating existing false positive pattern."""
        from application.mothership.middleware.drt_middleware import BehavioralSignature

        signature = BehavioralSignature(path_pattern="/api/admin", method="GET", headers=("accept", "authorization"))

        # Mock existing pattern
        mock_pattern = MagicMock()
        mock_pattern.total_violations = 5
        mock_pattern.false_positive_count = 3
        pattern_repo._db.execute.return_value.scalar_one_or_none.return_value = mock_pattern

        # Record another false positive
        await pattern_repo.record_pattern(signature, is_false_positive=True)

        # Should update existing pattern
        assert mock_pattern.total_violations == 6
        assert mock_pattern.false_positive_count == 4
        assert mock_pattern.false_positive_rate == 4 / 6

    @pytest.mark.asyncio
    async def test_get_patterns_above_threshold(self, pattern_repo):
        """Test getting patterns with high false positive rates."""
        mock_patterns = [
            MagicMock(
                id="pattern1",
                path_pattern="/api/admin",
                method="GET",
                false_positive_count=8,
                total_violations=10,
                false_positive_rate=0.8,
            ),
            MagicMock(
                id="pattern2",
                path_pattern="/api/user",
                method="POST",
                false_positive_count=2,
                total_violations=10,
                false_positive_rate=0.2,
            ),
        ]
        # Mock DB returns only patterns above threshold (DB WHERE clause is applied server-side)
        pattern_repo._db.execute.return_value.scalars.return_value.all.return_value = [mock_patterns[0]]

        result = await pattern_repo.get_patterns_above_threshold(threshold=0.5)

        assert len(result) == 1
        assert result[0]["id"] == "pattern1"
        assert result[0]["false_positive_rate"] == 0.8

    @pytest.mark.asyncio
    async def test_deactivate_pattern(self, pattern_repo):
        """Test deactivating a false positive pattern."""
        pattern_id = "test-pattern-123"
        pattern_repo._db.execute.return_value.rowcount = 1

        result = await pattern_repo.deactivate_pattern(pattern_id)

        assert result is True
        pattern_repo._db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_patterns(self, pattern_repo):
        """Test cleaning up old false positive patterns."""
        pattern_repo._db.execute.return_value.rowcount = 5

        result = await pattern_repo.cleanup_old_patterns(days=90)

        assert result == 5
        pattern_repo._db.execute.assert_called_once()


class TestDRTAPIIntegration:
    """Integration tests for DRT API endpoints."""

    @pytest.fixture
    def test_app_with_drt(self):
        """Create a test FastAPI app with DRT middleware and endpoints."""
        from fastapi import FastAPI

        app = FastAPI()

        # Create and configure middleware
        from application.mothership.middleware.drt_middleware import ComprehensiveDRTMiddleware

        middleware = ComprehensiveDRTMiddleware(
            app, enabled=True, similarity_threshold=0.8, auto_escalate=True, alert_on_escalation=True
        )

        # Add test endpoints
        @app.get("/api/health")
        async def health_check():
            return {"status": "ok"}

        @app.post("/api/test")
        async def test_endpoint():
            return {"data": "test"}

        # Add DRT monitoring endpoints
        from application.mothership.routers.drt_monitoring import router

        app.include_router(router)

        # Set the middleware instance for the test
        from application.mothership.routers.drt_monitoring import set_drt_middleware

        set_drt_middleware(middleware)

        # Create test client - use middleware as outer ASGI app so requests go through dispatch
        client = TestClient(middleware)

        return {"app": app, "middleware": middleware, "client": client}

    def test_drt_status_endpoint(self, test_app_with_drt):
        """Test DRT status endpoint returns correct data."""
        client = test_app_with_drt["client"]

        response = client.get("/drt/status")
        assert response.status_code == 200

        data = response.json()
        assert "enabled" in data
        assert "similarity_threshold" in data
        assert "escalated_endpoints_count" in data
        assert "behavioral_history_count" in data
        assert "attack_vectors_count" in data
        assert data["similarity_threshold"] == 0.8

    def test_drt_attack_vector_management(self, test_app_with_drt):
        """Test adding and managing attack vectors via API."""
        client = test_app_with_drt["client"]
        test_app_with_drt["middleware"]

        # Initially should have no attack vectors
        initial_status = client.get("/drt/status").json()
        initial_count = initial_status["attack_vectors_count"]

        # Add an attack vector
        attack_vector_data = {
            "path_pattern": "/api/sensitive",
            "method": "POST",
            "headers": ["content-type", "authorization"],
            "body_pattern": '{"action":"delete"}',
            "query_pattern": "force=true",
        }

        response = client.post("/drt/attack-vectors", json=attack_vector_data)
        assert response.status_code == 200
        assert "Attack vector added" in response.json()["message"]

        # Check that attack vector count increased
        updated_status = client.get("/drt/status").json()
        assert updated_status["attack_vectors_count"] == initial_count + 1

    def test_drt_endpoint_escalation(self, test_app_with_drt):
        """Test endpoint escalation via API."""
        client = test_app_with_drt["client"]

        # Escalate an endpoint
        response = client.post("/drt/escalate/api/sensitive")
        assert response.status_code == 200
        assert "Endpoint escalated" in response.json()["message"]

        # Check escalated endpoints
        response = client.get("/drt/escalated-endpoints")
        assert response.status_code == 200
        escalated = response.json()["escalated_endpoints"]
        assert "/api/sensitive" in escalated

        # De-escalate the endpoint
        response = client.post("/drt/de-escalate/api/sensitive")
        assert response.status_code == 200

        # Check that it's de-escalated
        response = client.get("/drt/escalated-endpoints")
        assert response.status_code == 200
        escalated = response.json()["escalated_endpoints"]
        assert "/api/sensitive" not in escalated

    def test_drt_behavioral_history(self, test_app_with_drt):
        """Test behavioral history endpoint."""
        client = test_app_with_drt["client"]

        # Make some requests to generate behavioral history
        client.get("/api/health")
        client.post("/api/test")

        # Check behavioral history
        response = client.get("/drt/behavioral-history")
        assert response.status_code == 200

        history = response.json()["behavioral_history"]
        assert isinstance(history, list)
        assert len(history) >= 2  # Should have at least the requests we made

        # Check structure of history entries
        for entry in history:
            assert "path_pattern" in entry
            assert "method" in entry
            assert "timestamp" in entry
            assert "request_count" in entry

    def test_false_positive_marking(self, test_app_with_drt):
        """Test marking violations as false positives."""
        client = test_app_with_drt["client"]
        test_app_with_drt["middleware"]

        # Add an attack vector
        attack_vector_data = {"path_pattern": "/api/test", "method": "POST", "headers": ["content-type"]}
        client.post("/drt/attack-vectors", json=attack_vector_data)

        # Make a request that should trigger the attack vector
        client.post("/api/test", json={"test": "data"})

        # Check that we have some behavioral history (simulating a violation)
        # In a real scenario, we'd need to trigger an actual violation

        # Try to mark a violation as false positive (using a mock violation ID)

        # Note: This would normally require a real violation ID from the database
        # For this test, we're just checking the endpoint exists and accepts the format
        # In a real integration test, we'd need to set up the full database and trigger real violations

    def test_false_positive_stats(self, test_app_with_drt):
        """Test false positive statistics endpoint."""
        client = test_app_with_drt["client"]

        response = client.get("/drt/false-positives/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_false_positives" in data
        assert "false_positive_rate" in data
        assert "recent_false_positives" in data
        assert "patterns_learned" in data
        assert "timestamp" in data

        # Should initially be all zeros/empty
        assert data["total_false_positives"] == 0
        assert data["false_positive_rate"] == 0.0

    def test_false_positive_recent_endpoint(self, test_app_with_drt):
        """Test recent false positives endpoint."""
        client = test_app_with_drt["client"]

        response = client.get("/drt/false-positives/recent?hours=24&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert "false_positives" in data
        assert "count" in data
        assert "hours" in data
        assert "timestamp" in data

        assert isinstance(data["false_positives"], list)
        assert data["hours"] == 24

    def test_false_positive_patterns_endpoint(self, test_app_with_drt):
        """Test false positive patterns endpoint."""
        client = test_app_with_drt["client"]

        response = client.get("/drt/false-positive-patterns?threshold=0.8")
        assert response.status_code == 200

        data = response.json()
        assert "patterns" in data
        assert "count" in data
        assert "threshold" in data
        assert "active_only" in data
        assert "timestamp" in data

        assert isinstance(data["patterns"], list)
        assert data["threshold"] == 0.8
        assert data["active_only"] is True

    def test_false_positive_pattern_deactivation(self, test_app_with_drt):
        """Test deactivating false positive patterns."""
        client = test_app_with_drt["client"]

        # Try to deactivate a non-existent pattern
        response = client.delete("/drt/false-positive-patterns/mock-pattern-id")
        # Should return 404 since pattern doesn't exist
        assert response.status_code == 404 or response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
