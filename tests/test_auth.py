from datetime import timedelta
from fastapi.testclient import TestClient
from app.core.security import create_access_token


def test_register_user_success(client: TestClient):
    """Test successful user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "SecurePassword123!", "full_name": "Test User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "Test User"
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_email_fails(client: TestClient):
    """Test that registering duplicate email returns 400 Bad Request."""
    user_payload = {"email": "duplicate@example.com", "password": "Password123!"}
    client.post("/api/v1/auth/register", json=user_payload)

    second_response = client.post("/api/v1/auth/register", json=user_payload)
    assert second_response.status_code == 400
    assert "already exists" in second_response.json()["detail"]


def test_login_success(client: TestClient):
    """Test logging in with valid credentials returns a valid JWT token."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "loginuser@example.com", "password": "MySecretPassword123"}
    )
    # Test JSON login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@example.com", "password": "MySecretPassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client: TestClient):
    """Test logging in with incorrect password returns 401 Unauthorized."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpass@example.com", "password": "CorrectPassword"}
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "WrongPassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user_returns_401(client: TestClient):
    """Test logging in with non-existent user returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "SomePassword"}
    )
    assert response.status_code == 401


def test_users_me_success_and_no_password_hash(client: TestClient, user1_headers: dict):
    """
    Test GET /users/me:
    - Returns profile info
    - Password hash MUST NOT be in response
    """
    response = client.get("/api/v1/users/me", headers=user1_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user1@example.com"
    assert "hashed_password" not in data
    assert "password" not in data


def test_users_me_invalid_token_returns_401(client: TestClient):
    """Test accessing /users/me with an invalid token returns 401."""
    headers = {"Authorization": "Bearer invalid.token.value"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


def test_users_me_expired_token_returns_401(client: TestClient):
    """Test that an expired token is rejected with 401 Unauthorized."""
    # Create an expired token (expired 10 minutes ago)
    expired_token = create_access_token(
        subject="1",
        expires_delta=timedelta(minutes=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
