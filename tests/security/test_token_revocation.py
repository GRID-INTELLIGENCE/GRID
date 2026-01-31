import pytest
from datetime import datetime, timedelta, UTC

from application.mothership.security.token_revocation import (
    TokenRevocationList,
    TokenValidator,
)


@pytest.fixture
def revocation_list():
    """Create a fresh revocation list for each test."""
    return TokenRevocationList()


@pytest.fixture
def token_validator(revocation_list):
    """Create a token validator with revocation list."""
    return TokenValidator(revocation_list)


class TestTokenRevocationList:
    """Test token revocation list operations."""

    @pytest.mark.asyncio
    async def test_revoke_token(self, revocation_list):
        """Test revoking a token."""
        jti = "test-jti-123"
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        
        result = await revocation_list.revoke_token(jti, expires_at, reason="logout")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_revoked(self, revocation_list):
        """Test checking if token is revoked."""
        jti = "test-jti-456"
        
        # Not revoked initially
        assert await revocation_list.is_revoked(jti) is False
        
        # Revoke it
        await revocation_list.revoke_token(jti, reason="test")
        
        # Now should be revoked
        assert await revocation_list.is_revoked(jti) is True

    @pytest.mark.asyncio
    async def test_expired_token_not_stored(self, revocation_list):
        """Test that already expired tokens are not stored."""
        jti = "expired-jti"
        expires_at = datetime.now(UTC) - timedelta(hours=1)  # Already expired
        
        result = await revocation_list.revoke_token(jti, expires_at)
        
        # Should return True but not actually store
        assert result is True


class TestTokenValidator:
    """Test token validator with revocation checking."""

    @pytest.mark.asyncio
    async def test_validate_valid_token(self, token_validator):
        """Test validation of valid token."""
        payload = {
            "jti": "valid-jti",
            "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
        }
        
        is_valid, error = await token_validator.validate_token(payload)
        
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_revoked_token(self, token_validator, revocation_list):
        """Test validation of revoked token."""
        jti = "revoked-jti"
        await revocation_list.revoke_token(jti, reason="test")
        
        payload = {
            "jti": jti,
            "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
        }
        
        is_valid, error = await token_validator.validate_token(payload)
        
        assert is_valid is False
        assert error == "Token has been revoked"

    @pytest.mark.asyncio
    async def test_validate_missing_jti(self, token_validator):
        """Test validation rejects tokens without JTI."""
        payload = {"exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp()}
        
        is_valid, error = await token_validator.validate_token(payload)
        
        assert is_valid is False
        assert error == "Token missing JTI claim"
