import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Create a dedicated engine for the test database
test_engine = create_engine(
    settings.test_database_url,
    pool_pre_ping=True
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables before test session and drop them after."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a clean database session for each test wrapped in a transaction rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def user1_headers(client: TestClient) -> dict:
    """Fixture to register and login user 1, returning Authorization header."""
    user_data = {
        "email": "user1@example.com",
        "password": "Password123!",
        "full_name": "User One"
    }
    client.post("/api/v1/auth/register", json=user_data)
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def user2_headers(client: TestClient) -> dict:
    """Fixture to register and login user 2, returning Authorization header."""
    user_data = {
        "email": "user2@example.com",
        "password": "Password123!",
        "full_name": "User Two"
    }
    client.post("/api/v1/auth/register", json=user_data)
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
