import asyncio

import pytest

from application.mothership.security.auth import AuthenticationError, verify_jwt_token
from application.mothership.security.jwt import get_jwt_manager, reset_jwt_manager
from application.mothership.security.token_revocation import get_token_validator


@pytest.mark.asyncio
async def test_verify_jwt_token_with_revocation():
    """Verify that verify_jwt_token correctly checks the revocation list."""
    reset_jwt_manager()
    try:
        manager = get_jwt_manager(
            secret_key="test-secret-key-at-least-32-chars-long-for-valid-test",
            environment="development",
        )

        token = manager.create_access_token(subject="test-user", user_id="test-user")
        payload = manager.decode_unverified(token)

        # Verify it works before revocation
        result = await verify_jwt_token(token)
        assert result["authenticated"] is True

        # Revoke the token
        validator = get_token_validator()
        await validator.revoke_token(payload, reason="integration-test")

        # Verify it fails after revocation
        with pytest.raises(AuthenticationError) as excinfo:
            await verify_jwt_token(token)

        assert "Token invalid" in str(excinfo.value) or "revoked" in str(excinfo.value).lower()
    finally:
        reset_jwt_manager()


if __name__ == "__main__":
    asyncio.run(test_verify_jwt_token_with_revocation())
