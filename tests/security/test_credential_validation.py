"""Tests for credential validation service."""

import pytest
from unittest.mock import patch

from application.mothership.security.credential_validation import (
    CredentialValidationService,
)
from grid.organization.models import UserStatus


@pytest.fixture
def validation_service():
    """Create a fresh validation service for each test."""
    return CredentialValidationService(max_failed_attempts=3, lockout_duration_minutes=5)


@pytest.fixture
async def test_user(validation_service):
    """Create a test user with known credentials."""
    user = await validation_service.create_user(
        username="testuser",
        password="SecurePass123!",
        email="test@example.com",
        org_id="test-org"
    )
    return user


class TestCredentialValidation:
    """Test credential validation logic."""

    @pytest.mark.asyncio
    async def test_successful_login(self, validation_service, test_user):
        """Test successful authentication."""
        result = await validation_service.validate_credentials("testuser", "SecurePass123!")
        
        assert result.success is True
        assert result.user is not None
        assert result.user.username == "testuser"
        assert result.error_code is None

    @pytest.mark.asyncio
    async def test_invalid_password(self, validation_service, test_user):
        """Test authentication with wrong password."""
        result = await validation_service.validate_credentials("testuser", "WrongPassword")
        
        assert result.success is False
        assert result.error_code == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_invalid_username(self, validation_service):
        """Test authentication with non-existent user."""
        result = await validation_service.validate_credentials("nonexistent", "password")
        
        assert result.success is False
        assert result.error_code == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_case_insensitive_username(self, validation_service, test_user):
        """Test that username lookup is case-insensitive."""
        result = await validation_service.validate_credentials("TESTUSER", "SecurePass123!")
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_account_lockout(self, validation_service, test_user):
        """Test account lockout after max failed attempts."""
        # Make 3 failed attempts (max_failed_attempts=3)
        for _ in range(3):
            await validation_service.validate_credentials("testuser", "wrong")
        
        # Next attempt should be locked
        result = await validation_service.validate_credentials("testuser", "SecurePass123!")
        
        assert result.success is False
        assert result.error_code == "ACCOUNT_LOCKED"

    @pytest.mark.asyncio
    async def test_suspended_account(self, validation_service, test_user):
        """Test login with suspended account."""
        test_user.status = UserStatus.SUSPENDED
        
        result = await validation_service.validate_credentials("testuser", "SecurePass123!")
        
        assert result.success is False
        assert result.error_code == "ACCOUNT_SUSPENDED"


class TestPostgresIntegration:
    """Test PostgreSQL adapter integration."""

    @pytest.mark.asyncio
    async def test_postgres_fallback_on_import_error(self, validation_service):
        """Test graceful fallback when PostgreSQL adapter not available."""
        with patch.dict('sys.modules', {'grid.integration.postgres_adapter': None}):
            result = await validation_service.validate_credentials("unknown", "password")
            
            # Should not crash, just return not found
            assert result.success is False
            assert result.error_code == "INVALID_CREDENTIALS"
