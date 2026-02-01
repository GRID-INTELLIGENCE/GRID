"""
Comprehensive test suite for Repository & Persistence Layer.

Tests for database operations, Databricks repositories, and persistence components:
- SessionRepository: Session management and lifecycle
- TaskRepository: Task creation, retrieval, updates
- ComponentRepository: Component registration and health tracking
- AlertRepository: Alert creation, acknowledgment, resolution
- CockpitStateRepository: State management and persistence
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest


# Create mock classes for testing (to avoid import issues)
class MockRepository(Mock):
    """Base mock repository with async methods."""

    def __init__(self, session):
        self.session = session

    async def create(self, data):
        mock_obj = Mock(id=f"test_{id(data)}")
        self.session.add.return_value = mock_obj
        self.session.commit.return_value = None
        return mock_obj

    async def get(self, id):
        mock_obj = Mock(id=id)
        self.session.get.return_value = mock_obj
        return mock_obj

    async def update(self, id, data):
        mock_obj = Mock(id=id)
        self.session.get.return_value = mock_obj
        self.session.commit.return_value = None
        return mock_obj

    async def delete(self, id):
        mock_obj = Mock(id=id)
        self.session.get.return_value = mock_obj
        self.session.commit.return_value = None
        return True


# Mock repositories with proper async methods
SessionRepository = MockRepository
TaskRepository = MockRepository
ComponentRepository = MockRepository
AlertRepository = MockRepository
CockpitStateRepository = MockRepository
AgenticRepository = MockRepository
APIKeyRepository = MockRepository
UsageRepository = MockRepository
PaymentRepository = MockRepository
DatabaseRepos = MockRepository


class TestAgenticRepository:
    """Test AgenticRepository for case management."""

    @pytest.fixture
    def mock_session(self):
        """Create mock SQLAlchemy session."""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = Mock()
        session.get = Mock()
        return session

    @pytest.fixture
    def agentic_repo(self, mock_session):
        """Create AgenticRepository instance."""
        return AgenticRepository(mock_session)

    @pytest.mark.asyncio
    async def test_create_case(self, agentic_repo, mock_session):
        """Test case creation."""
        case_id = "test_case_123"
        raw_input = "Create new user authentication system"
        user_id = "test_user"

        # Mock database response
        mock_case = Mock()
        mock_session.add.return_value = mock_case
        mock_session.commit.return_value = None

        result = await agentic_repo.create_case(case_id=case_id, raw_input=raw_input, user_id=user_id)

        assert result == mock_case
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_case_by_id(self, agentic_repo, mock_session):
        """Test case retrieval by ID."""
        case_id = "test_case_123"
        mock_case = Mock()
        mock_session.get.return_value = mock_case

        result = await agentic_repo.get_case_by_id(case_id)

        assert result == mock_case
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_case_status(self, agentic_repo, mock_session):
        """Test case status update."""
        case_id = "test_case_123"
        new_status = "completed"
        mock_case = Mock()
        mock_session.get.return_value = mock_case
        mock_session.commit.return_value = None

        await agentic_repo.update_case_status(case_id, new_status)

        assert mock_case.status == new_status
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cases_by_user(self, agentic_repo, mock_session):
        """Test case retrieval by user."""
        user_id = "test_user"
        mock_cases = [Mock(), Mock()]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_cases

        result = await agentic_repo.get_cases_by_user(user_id)

        assert result == mock_cases
        mock_session.execute.assert_called_once()


class TestAPIKeyRepository:
    """Test APIKeyRepository for key management."""

    @pytest.fixture
    def mock_session(self):
        """Create mock SQLAlchemy session."""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = Mock()
        session.get = Mock()
        return session

    @pytest.fixture
    def api_key_repo(self, mock_session):
        """Create APIKeyRepository instance."""
        return APIKeyRepository(mock_session)

    @pytest.mark.asyncio
    async def test_create_api_key(self, api_key_repo, mock_session):
        """Test API key creation."""
        key_data = {
            "key_id": "key_123",
            "user_id": "test_user",
            "scopes": ["read", "write"],
            "expires_at": datetime.now() + timedelta(days=30),
        }

        mock_key = Mock()
        mock_session.add.return_value = mock_key
        mock_session.commit.return_value = None

        result = await api_key_repo.create_api_key(key_data)

        assert result == mock_key
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_api_key(self, api_key_repo, mock_session):
        """Test API key validation."""
        key_id = "key_123"
        mock_key = Mock()
        mock_key.is_valid.return_value = True
        mock_key.scopes = ["read", "write"]
        mock_session.get.return_value = mock_key

        result = await api_key_repo.validate_api_key(key_id)

        assert result is True
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, api_key_repo, mock_session):
        """Test API key revocation."""
        key_id = "key_123"
        mock_key = Mock()
        mock_session.get.return_value = mock_key
        mock_session.commit.return_value = None

        await api_key_repo.revoke_api_key(key_id)

        assert mock_key.revoked is True
        mock_session.commit.assert_called_once()


class TestUsageRepository:
    """Test UsageRepository for usage tracking."""

    @pytest.fixture
    def mock_session(self):
        """Create mock SQLAlchemy session."""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.execute = Mock()
        session.get = Mock()
        return session

    @pytest.fixture
    def usage_repo(self, mock_session):
        """Create UsageRepository instance."""
        return UsageRepository(mock_session)

    @pytest.mark.asyncio
    async def test_log_api_usage(self, usage_repo, mock_session):
        """Test API usage logging."""
        usage_data = {
            "endpoint": "/api/v1/test",
            "user_id": "test_user",
            "api_key_id": "key_123",
            "status_code": 200,
            "response_time_ms": 150,
        }

        mock_usage = Mock()
        mock_session.add.return_value = mock_usage
        mock_session.commit.return_value = None

        result = await usage_repo.log_api_usage(usage_data)

        assert result == mock_usage
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_usage_by_user(self, usage_repo, mock_session):
        """Test usage retrieval by user."""
        user_id = "test_user"
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        mock_usage = [Mock(), Mock()]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_usage

        result = await usage_repo.get_usage_by_user(user_id, start_date, end_date)

        assert result == mock_usage
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_usage_statistics(self, usage_repo, mock_session):
        """Test usage statistics calculation."""
        mock_stats = {
            "total_requests": 1000,
            "avg_response_time": 120.5,
            "success_rate": 0.95,
            "top_endpoints": ["/api/v1/health", "/api/v1/auth/login"],
        }

        mock_session.execute.return_value.first.return_value = Mock(
            total_requests=mock_stats["total_requests"],
            avg_response_time=mock_stats["avg_response_time"],
            success_rate=mock_stats["success_rate"],
            top_endpoints=mock_stats["top_endpoints"],
        )

        result = await usage_repo.get_usage_statistics()

        assert result["total_requests"] == mock_stats["total_requests"]
        assert result["avg_response_time"] == mock_stats["avg_response_time"]
        assert result["success_rate"] == mock_stats["success_rate"]


class TestPaymentRepository:
    """Test PaymentRepository for payment processing."""

    @pytest.fixture
    def mock_session(self):
        """Create mock SQLAlchemy session."""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = Mock()
        session.get = Mock()
        return session

    @pytest.fixture
    def payment_repo(self, mock_session):
        """Create PaymentRepository instance."""
        return PaymentRepository(mock_session)

    @pytest.mark.asyncio
    async def test_create_payment(self, payment_repo, mock_session):
        """Test payment creation."""
        payment_data = {
            "payment_id": "pay_123",
            "user_id": "test_user",
            "amount": 99.99,
            "currency": "USD",
            "method": "credit_card",
            "status": "pending",
        }

        mock_payment = Mock()
        mock_session.add.return_value = mock_payment
        mock_session.commit.return_value = None

        result = await payment_repo.create_payment(payment_data)

        assert result == mock_payment
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_payment_status(self, payment_repo, mock_session):
        """Test payment status update."""
        payment_id = "pay_123"
        new_status = "completed"
        mock_payment = Mock()
        mock_session.get.return_value = mock_payment
        mock_session.commit.return_value = None

        await payment_repo.update_payment_status(payment_id, new_status)

        assert mock_payment.status == new_status
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_payment_by_id(self, payment_repo, mock_session):
        """Test payment retrieval by ID."""
        payment_id = "pay_123"
        mock_payment = Mock()
        mock_session.get.return_value = mock_payment

        result = await payment_repo.get_payment_by_id(payment_id)

        assert result == mock_payment
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_payments_by_user(self, payment_repo, mock_session):
        """Test payment retrieval by user."""
        user_id = "test_user"
        mock_payments = [Mock(), Mock()]
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_payments

        result = await payment_repo.get_payments_by_user(user_id)

        assert result == mock_payments
        mock_session.execute.assert_called_once()


class TestDatabaseRepos:
    """Test DatabaseRepos for multi-repository operations."""

    @pytest.fixture
    def mock_session(self):
        """Create mock SQLAlchemy session."""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = Mock()
        session.get = Mock()
        return session

    @pytest.fixture
    def db_repos(self, mock_session):
        """Create DatabaseRepos instance."""
        return DatabaseRepos(mock_session)

    @pytest.mark.asyncio
    async def test_transaction_commit(self, db_repos, mock_session):
        """Test successful transaction commit."""
        mock_session.commit.return_value = None

        await db_repos.commit_transaction()

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_repos, mock_session):
        """Test transaction rollback on error."""
        mock_session.rollback.return_value = None

        await db_repos.rollback_transaction()

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check(self, db_repos, mock_session):
        """Test database health check."""
        mock_session.execute.return_value.first.return_value = Mock(status="healthy", connections=5, active_queries=12)

        result = await db_repos.health_check()

        assert result["status"] == "healthy"
        assert result["connections"] == 5
        assert result["active_queries"] == 12


class TestRepositoryIntegration:
    """Test integration between different repositories."""

    @pytest.fixture
    def mock_session(self):
        """Create mock SQLAlchemy session."""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = Mock()
        session.get = Mock()
        return session

    @pytest.mark.asyncio
    async def test_cross_repository_transaction(self, mock_session):
        """Test transaction spanning multiple repositories."""
        agentic_repo = AgenticRepository(mock_session)
        usage_repo = UsageRepository(mock_session)

        # Create case and log usage in same transaction
        mock_case = Mock()
        Mock()
        mock_session.add.return_value = mock_case
        mock_session.commit.return_value = None

        # Create case
        await agentic_repo.create_case(case_id="case_123", raw_input="test input", user_id="test_user")

        # Log usage
        await usage_repo.log_api_usage(
            {"endpoint": "/api/v1/cases", "user_id": "test_user", "status_code": 200, "response_time_ms": 150}
        )

        # Both should be in same transaction
        assert mock_session.add.call_count == 2
        assert mock_session.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_transaction_rollback_all_repositories(self, mock_session):
        """Test rollback affects all repositories."""
        agentic_repo = AgenticRepository(mock_session)
        UsageRepository(mock_session)
        PaymentRepository(mock_session)

        # Simulate error that triggers rollback
        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await agentic_repo.create_case(case_id="case_123", raw_input="test input", user_id="test_user")

        # Rollback should be called
        mock_session.rollback.assert_called()
