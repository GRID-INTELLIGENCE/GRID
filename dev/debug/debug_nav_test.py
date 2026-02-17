import os
import sys

sys.path.append(os.getcwd())

from fastapi.testclient import TestClient

from application.mothership.main import create_app
from application.mothership.security.jwt import reset_jwt_manager


def debug_test():
    reset_jwt_manager()
    app = create_app()
    client = TestClient(app)

    # Authenticate
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass",
            "scopes": ["read", "write"],
        },
    )
    if login_res.status_code != 200:
        print("Login failed:", login_res.json())
        return

    tokens = login_res.json()["data"]

    # Navigation request
    response = client.post(
        "/api/v1/navigation/plan",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={
            "goal": "Complete user onboarding",
            "context": {"user_type": "new"},
            "max_alternatives": 3,
        },
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    debug_test()
