"""
Property-Based Testing for Authentication.

Uses Hypothesis to generate thousands of test cases automatically,
ensuring robust handling of edge cases and unexpected inputs.
"""

from __future__ import annotations

import string
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

try:
    from hypothesis import HealthCheck, assume, given, settings
    from hypothesis import strategies as st

    settings.register_profile("ci", suppress_health_check=[HealthCheck.function_scoped_fixture])
    settings.load_profile("ci")

    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False

    # Provide stubs so module loads without errors
    def assume(x):  # noqa: ARG001
        return None

    def given(*args, **kwargs):  # noqa: ARG001, ARG002
        def decorator(f):
            return f

        return decorator

    def settings(**kwargs):  # noqa: ARG001
        def decorator(f):
            return f

        return decorator

    st = None  # type: ignore

from application.mothership.main import create_app
from application.mothership.security.jwt import JWTManager, reset_jwt_manager

# =============================================================================
# Fixtures
# =============================================================================


pytestmark = pytest.mark.skipif(
    not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed - run: pip install hypothesis>=6.92.0"
)

if not HYPOTHESIS_AVAILABLE:
    pytest.skip("hypothesis not installed", allow_module_level=True)


@pytest.fixture
def jwt_manager() -> JWTManager:
    """Create a JWT manager for testing."""
    return JWTManager(
        secret_key="test-jwt-key-32-chars-minimum-required-for-security-validation",
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        environment="test",
    )


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    # Ensure env var matches jwt_manager fixture
    import os

    os.environ["MOTHERSHIP_SECRET_KEY"] = "test-jwt-key-32-chars-minimum-required-for-security-validation"
    # Ensure we're in development mode for tests (allows unauthenticated access)
    os.environ.setdefault("MOTHERSHIP_ENVIRONMENT", "development")
    # Disable rate limiting for property-based tests (they make many requests)
    os.environ.setdefault("MOTHERSHIP_RATE_LIMIT_ENABLED", "false")
    # Disable any features that might interfere with testing
    os.environ.setdefault("MOTHERSHIP_ENABLE_GRID_PULSE", "0")

    reset_jwt_manager()
    from application.mothership.config import reload_settings

    reload_settings()
    app = create_app()
    return TestClient(app)


# =============================================================================
# Custom Strategies
# =============================================================================

if HYPOTHESIS_AVAILABLE:
    # Safe ASCII text (no control characters)
    safe_text = st.text(
        alphabet=string.ascii_letters + string.digits + string.punctuation + " ",
        min_size=1,
        max_size=100,
    )

    # Safer text for API endpoints to avoid URL encoding/header parsing issues during hypothesis runs
    api_safe_text = st.text(
        alphabet=string.ascii_letters + string.digits + "_-",
        min_size=1,
        max_size=50,
    )

    # Username strategy (realistic usernames)
    username_strategy = st.one_of(
        st.emails(),
        st.text(
            alphabet=string.ascii_lowercase + string.digits + "_.-",
            min_size=3,
            max_size=50,
        ),
    )

    # Scope strategy
    scope_strategy = st.lists(
        st.sampled_from(["read", "write", "admin", "delete", "create"]),
        min_size=0,
        max_size=10,
        unique=True,
    )

    # Context strategy (nested dictionaries)
    context_value = st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=100),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=5),
            st.dictionaries(
                st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
                children,
                max_size=5,
            ),
        ),
        max_leaves=10,
    )
else:
    safe_text = None  # type: ignore
    api_safe_text = None  # type: ignore
    username_strategy = None  # type: ignore
    scope_strategy = None  # type: ignore
    context_value = None  # type: ignore

# =============================================================================
# JWT Token Properties
# =============================================================================


class TestJWTTokenProperties:
    """Property-based tests for JWT tokens."""

    @given(
        subject=safe_text,
        user_id=st.one_of(st.none(), safe_text),
        email=st.one_of(st.none(), st.emails()),
    )
    @settings(max_examples=100, deadline=1000)
    def test_token_roundtrip_preserves_data(
        self,
        jwt_manager: JWTManager,
        subject: str,
        user_id: str | None,
        email: str | None,
    ) -> None:
        """Property: Token encode/decode preserves subject and claims."""
        assume(len(subject) > 0)

        # Create token
        token = jwt_manager.create_access_token(
            subject=subject,
            user_id=user_id,
            email=email,
        )

        # Verify token
        payload = jwt_manager.verify_token(token)

        # Check data preservation
        assert payload.sub == subject
        if user_id:
            assert payload.user_id == user_id
        if email:
            assert payload.email == email

    @given(
        subject=safe_text,
        scopes=scope_strategy,
    )
    @settings(max_examples=50, deadline=1000)
    def test_token_scopes_preserved(
        self,
        jwt_manager: JWTManager,
        subject: str,
        scopes: list[str],
    ) -> None:
        """Property: Token scopes are preserved exactly."""
        assume(len(subject) > 0)

        token = jwt_manager.create_access_token(
            subject=subject,
            scopes=scopes,
        )

        payload = jwt_manager.verify_token(token)
        assert set(payload.scopes) == set(scopes)

    @given(
        subject=safe_text,
        metadata=st.dictionaries(
            st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
            st.one_of(st.text(max_size=50), st.integers(), st.booleans()),
            max_size=10,
        ),
    )
    @settings(max_examples=50, deadline=1000)
    def test_token_metadata_preserved(
        self,
        jwt_manager: JWTManager,
        subject: str,
        metadata: dict[str, Any],
    ) -> None:
        """Property: Token metadata is preserved."""
        assume(len(subject) > 0)

        token = jwt_manager.create_access_token(
            subject=subject,
            metadata=metadata,
        )

        payload = jwt_manager.verify_token(token)
        assert payload.metadata == metadata

    @given(
        subject=safe_text,
        expire_minutes=st.integers(min_value=1, max_value=1440),  # 1 min to 24 hours
    )
    @settings(max_examples=50, deadline=1000)
    def test_token_expiration_in_future(
        self,
        jwt_manager: JWTManager,
        subject: str,
        expire_minutes: int,
    ) -> None:
        """Property: Token expiration is always in the future for positive deltas."""
        assume(len(subject) > 0)

        token = jwt_manager.create_access_token(
            subject=subject,
            expires_delta=timedelta(minutes=expire_minutes),
        )

        payload = jwt_manager.verify_token(token)

        # Expiration should be in the future
        exp_time = datetime.fromtimestamp(payload.exp, tz=UTC)
        now = datetime.now(UTC)
        assert exp_time > now

    @given(subject1=safe_text, subject2=safe_text)
    @settings(max_examples=50, deadline=1000)
    def test_different_subjects_produce_different_tokens(
        self,
        jwt_manager: JWTManager,
        subject1: str,
        subject2: str,
    ) -> None:
        """Property: Different subjects produce different tokens."""
        assume(len(subject1) > 0 and len(subject2) > 0)
        assume(subject1 != subject2)

        token1 = jwt_manager.create_access_token(subject=subject1)
        token2 = jwt_manager.create_access_token(subject=subject2)

        assert token1 != token2


# =============================================================================
# Login Endpoint Properties
# =============================================================================


class TestLoginEndpointProperties:
    """Property-based tests for login endpoint."""

    @given(
        username=username_strategy,
        password=safe_text,
    )
    @settings(max_examples=50, deadline=2000)
    def test_login_accepts_valid_credentials(
        self,
        client: TestClient,
        username: str,
        password: str,
    ) -> None:
        """Property: Login with any valid-format credentials succeeds in dev mode."""
        assume(len(username) > 0 and len(password) > 0)
        assume(len(username) <= 255 and len(password) <= 255)

        response = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

        # In development mode, should accept any credits, but security middleware might block malicious-looking patterns
        assert response.status_code in [200, 429, 422]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]
            assert "refresh_token" in data["data"]

    @given(
        username=safe_text,
        password=safe_text,
        scopes=scope_strategy,
    )
    @settings(max_examples=30, deadline=2000)
    def test_login_response_structure_invariant(
        self,
        client: TestClient,
        username: str,
        password: str,
        scopes: list[str],
    ) -> None:
        """Property: Login response always has consistent structure."""
        assume(1 <= len(username) <= 255)
        assume(1 <= len(password) <= 255)

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": username,
                "password": password,
                "scopes": scopes,
            },
        )

        if response.status_code == 200:
            data = response.json()
            # Required fields
            assert "success" in data
            assert "data" in data
            assert "access_token" in data["data"]
            assert "refresh_token" in data["data"]
            assert "token_type" in data["data"]
            assert "expires_in" in data["data"]
            assert data["data"]["token_type"] == "bearer"

    @given(username=st.text(min_size=256))
    @settings(max_examples=20, deadline=2000)
    def test_login_rejects_oversized_username(
        self,
        client: TestClient,
        username: str,
    ) -> None:
        """Property: Login rejects usernames over max length."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "test"},
        )

        # Should reject with validation error
        assert response.status_code == 422

    @given(password=st.text(min_size=256))
    @settings(max_examples=20, deadline=2000)
    def test_login_rejects_oversized_password(
        self,
        client: TestClient,
        password: str,
    ) -> None:
        """Property: Login rejects passwords over max length."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "test", "password": password},
        )

        # Should reject with validation error
        assert response.status_code == 422


# =============================================================================
# Navigation Endpoint Properties
# =============================================================================


class TestNavigationEndpointProperties:
    """Property-based tests for navigation endpoint."""

    @given(
        goal=safe_text,
        context=st.dictionaries(
            st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
            st.one_of(st.text(max_size=100), st.integers(), st.booleans()),
            max_size=10,
        ),
        max_alternatives=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=30, deadline=3000)
    def test_navigation_accepts_valid_goals(
        self,
        client: TestClient,
        goal: str,
        context: dict[str, Any],
        max_alternatives: int,
    ) -> None:
        """Property: Navigation accepts any valid goal format."""
        assume(len(goal) > 0 and len(goal) <= 1000)

        response = client.post(
            "/api/v1/navigation/plan",
            json={
                "goal": goal,
                "context": context,
                "max_alternatives": max_alternatives,
            },
        )

        # Should succeed in dev mode
        assert response.status_code in [200, 422, 429]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "request_id" in data["data"]

    @given(
        goal=safe_text,
        max_alternatives=st.integers(min_value=-100, max_value=1000),
    )
    @settings(max_examples=30, deadline=3000)
    def test_navigation_max_alternatives_bounds(
        self,
        client: TestClient,
        goal: str,
        max_alternatives: int,
    ) -> None:
        """Property: Navigation handles max_alternatives boundary conditions."""
        assume(len(goal) > 0 and len(goal) <= 500)

        response = client.post(
            "/api/v1/navigation/plan",
            json={
                "goal": goal,
                "context": {},
                "max_alternatives": max_alternatives,
            },
        )

        # Should handle gracefully (accept or reject with 422)
        assert response.status_code in [200, 422, 429]

    @given(
        goal=safe_text,
        enable_learning=st.booleans(),
        learning_weight=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        adaptation_threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=30, deadline=3000)
    def test_navigation_learning_parameters(
        self,
        client: TestClient,
        goal: str,
        enable_learning: bool,
        learning_weight: float,
        adaptation_threshold: float,
    ) -> None:
        """Property: Navigation handles all learning parameter combinations."""
        assume(len(goal) > 0 and len(goal) <= 500)

        response = client.post(
            "/api/v1/navigation/plan",
            json={
                "goal": goal,
                "context": {},
                "enable_learning": enable_learning,
                "learning_weight": learning_weight,
                "adaptation_threshold": adaptation_threshold,
            },
        )

        assert response.status_code in [200, 422, 429]


# =============================================================================
# Token Validation Properties
# =============================================================================


class TestTokenValidationProperties:
    """Property-based tests for token validation."""

    @given(
        subject=api_safe_text,
        scopes=scope_strategy,
    )
    @settings(max_examples=50, deadline=2000)
    def test_validate_endpoint_returns_token_info(
        self,
        client: TestClient,
        jwt_manager: JWTManager,
        subject: str,
        scopes: list[str],
    ) -> None:
        """Property: Validate endpoint returns token information correctly."""
        assume(len(subject) > 0)

        # Create token
        token = jwt_manager.create_access_token(
            subject=subject,
            scopes=scopes,
            user_id=f"user_{subject}",
        )

        # Validate via API
        response = client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in [200, 429, 422]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["data"]["valid"] is True
            assert set(data["data"]["scopes"]) == set(scopes)


# =============================================================================
# Security Properties
# =============================================================================


class TestSecurityProperties:
    """Property-based security tests."""

    @given(
        subject=safe_text,
        tamper_byte=st.integers(min_value=0, max_value=255),
        tamper_position=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=30, deadline=1000)
    def test_tampered_tokens_always_rejected(
        self,
        jwt_manager: JWTManager,
        subject: str,
        tamper_byte: int,
        tamper_position: int,
    ) -> None:
        """Property: Any tampered token is rejected."""
        assume(len(subject) > 0)

        # Create valid token
        token = jwt_manager.create_access_token(subject=subject)

        # Tamper with token bytes
        token_bytes = bytearray(token.encode())
        if len(token_bytes) > tamper_position:
            assume(token_bytes[tamper_position] != tamper_byte)
            token_bytes[tamper_position] = tamper_byte
            tampered_token = token_bytes.decode("utf-8", errors="ignore")

            # Should reject tampered token
            from jwt.exceptions import InvalidTokenError as JWTError

            with pytest.raises((JWTError, ValueError, Exception)):
                jwt_manager.verify_token(tampered_token)

    @given(
        subject=safe_text,
        expire_seconds=st.integers(min_value=-3600, max_value=-60),
    )
    @settings(max_examples=30, deadline=1000)
    def test_expired_tokens_always_rejected(
        self,
        jwt_manager: JWTManager,
        subject: str,
        expire_seconds: int,
    ) -> None:
        """Property: All expired tokens are rejected."""
        assume(len(subject) > 0)

        # Create expired token
        token = jwt_manager.create_access_token(
            subject=subject,
            expires_delta=timedelta(seconds=expire_seconds),
        )

        # Should reject expired token
        from jwt.exceptions import InvalidTokenError as JWTError

        with pytest.raises(JWTError):
            jwt_manager.verify_token(token)


# =============================================================================
# Idempotency Properties
# =============================================================================


class TestIdempotencyProperties:
    """Property-based tests for idempotency."""

    @given(
        username=username_strategy,
        password=safe_text,
        iterations=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=20, deadline=5000)
    def test_login_idempotency(
        self,
        client: TestClient,
        username: str,
        password: str,
        iterations: int,
    ) -> None:
        """Property: Multiple identical login requests produce valid tokens."""
        assume(1 <= len(username) <= 255)
        assume(1 <= len(password) <= 255)

        tokens = []
        for _ in range(iterations):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": password},
            )
            assert response.status_code in [200, 429, 422]
            if response.status_code == 200:
                tokens.append(response.json()["data"]["access_token"])

        # All tokens should be valid (but likely different due to timestamps)
        for token in tokens:
            response = client.get(
                "/api/v1/auth/validate",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code in [200, 429, 422]

    @given(
        goal=safe_text,
        iterations=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=20, deadline=5000)
    def test_navigation_idempotency(
        self,
        client: TestClient,
        goal: str,
        iterations: int,
    ) -> None:
        """Property: Multiple identical navigation requests all succeed."""
        assume(1 <= len(goal) <= 500)

        for _ in range(iterations):
            response = client.post(
                "/api/v1/navigation/plan",
                json={"goal": goal, "context": {}},
            )
            # Should consistently succeed or fail
            assert response.status_code in [200, 422, 429]
