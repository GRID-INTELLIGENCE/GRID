import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from src.grid.api.main import app
from src.grid.core.database import get_db, Base, engine
from src.grid.models.user import User
from src.grid.core.security import get_password_hash

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)

# Override the get_db dependency
@pytest.fixture(scope="module", autouse=True)
def override_get_db():
    def _get_db_override():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_register_user_success(client, db):
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "full_name": "New User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data

def test_register_duplicate_email(client, db):
    # First registration
    client.post(
        "/auth/register",
        json={
            "username": "user1",
            "email": "dup@example.com",
            "password": "StrongPassword123!"
        }
    )
    # Second registration with same email
    response = client.post(
        "/auth/register",
        json={
            "username": "user2",
            "email": "dup@example.com",
            "password": "StrongPassword123!"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_register_weak_password(client, db):
    response = client.post(
        "/auth/register",
        json={
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "123"
        }
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Password is too weak" in detail["message"]

def test_login_success(client, db):
    # Ensure user exists
    client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "StrongPassword123!"
        }
    )

    # Login
    response = client.post(
        "/auth/token",
        data={
            "username": "loginuser",
            "password": "StrongPassword123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client, db):
    response = client.post(
        "/auth/token",
        data={
            "username": "nonexistent",
            "password": "password"
        }
    )
    assert response.status_code == 401
