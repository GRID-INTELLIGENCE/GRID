from datetime import timedelta

import pytest

from src.grid.auth.token_manager import TokenManager


# Use a known secret for testing
@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("MOTHERSHIP_SECRET_KEY", "test-secret-key-123")
    monkeypatch.setenv("MOTHERSHIP_JWT_ALGORITHM", "HS256")
    # Reset singleton if needed, or TokenManager pulls from env.


@pytest.fixture
def token_manager(mock_settings):
    # Re-instantiate to pick up env vars
    return TokenManager()


@pytest.mark.asyncio
async def test_create_and_verify_token(token_manager):
    data = {"sub": "user123", "role": "admin"}
    token = token_manager.create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

    payload = await token_manager.verify_token(token)
    assert payload["sub"] == "user123"
    assert payload["role"] == "admin"


@pytest.mark.asyncio
async def test_token_expiration(token_manager):
    data = {"sub": "expired_user"}
    # Create token executing 1 second ago
    expires = timedelta(seconds=-1)
    token = token_manager.create_access_token(data, expires_delta=expires)

    with pytest.raises(ValueError, match="Could not validate credentials"):
        await token_manager.verify_token(token)


@pytest.mark.asyncio
async def test_revoke_token(token_manager):
    data = {"sub": "revoked_user"}
    token = token_manager.create_access_token(data)

    # Verify works first
    await token_manager.verify_token(token)

    # Revoke
    await token_manager.revoke_token(token)

    # Verify fails
    with pytest.raises(ValueError, match="Token has been revoked"):
        await token_manager.verify_token(token)
