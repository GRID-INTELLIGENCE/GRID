import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from application.mothership.security.auth import verify_jwt_token
from application.mothership.security.jwt import get_jwt_manager
from application.mothership.security.token_revocation import get_token_validator


@pytest.mark.asyncio
async def test_verify_jwt_token_with_revocation():
    """Verify that verify_jwt_token correctly checks the revocation list."""
    # 1. Setup JWT manager
    get_jwt_manager(secret_key="test-secret-key-at-least-32-chars-long-for-valid-test", environment="development")

    # 2. Create a token
    jti = "integration-test-jti"
    # We need to manually add jti to the payload or use a manager that adds it
    # JWTManager.create_access_token doesn't seem to take jti as argument,
    # but we can pass it in metadata if the manager supports it,
    # or just mock the token creation.

    # Actually, let's look at JWTManager.create_access_token again
    # It doesn't take jti. Let's see how it generates it.
    # It doesn't generate jti!

    # Let's create a payload with jti
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=30)
    payload = {
        "sub": "test-user",
        "jti": jti,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
    }

    import jose.jwt

    token = jose.jwt.encode(payload, "test-secret-key-at-least-32-chars-long-for-valid-test", algorithm="HS256")

    # 3. Verify it works before revocation
    result = await verify_jwt_token(token)
    assert result["authenticated"] is True

    # 4. Revoke the token
    validator = get_token_validator()
    await validator.revoke_token(payload, reason="integration-test")

    # 5. Verify it fails after revocation
    with pytest.raises(Exception) as excinfo:
        await verify_jwt_token(token)

    assert "Token invalid" in str(excinfo.value) or "revoked" in str(excinfo.value).lower()
    print("Integration test passed: Token revocation correctly blocks authentication.")


if __name__ == "__main__":
    asyncio.run(test_verify_jwt_token_with_revocation())
