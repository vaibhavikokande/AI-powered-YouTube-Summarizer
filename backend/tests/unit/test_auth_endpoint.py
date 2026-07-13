import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.schemas.auth import Token
from app.schemas.user import UserResponse


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def _fake_token() -> Token:
    return Token(access_token="access-token", refresh_token="refresh-token")


def test_register_returns_tokens():
    with patch("app.api.v1.endpoints.auth.AuthService") as MockAuthService:
        MockAuthService.return_value.register = AsyncMock(return_value=MagicMock())
        MockAuthService.return_value.issue_tokens = MagicMock(return_value=_fake_token())

        response = client.post(
            "/api/v1/register",
            json={"email": "new@example.com", "password": "password123", "full_name": "New User"},
        )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access-token"


def test_login_returns_tokens():
    with patch("app.api.v1.endpoints.auth.AuthService") as MockAuthService:
        MockAuthService.return_value.authenticate = AsyncMock(return_value=MagicMock())
        MockAuthService.return_value.issue_tokens = MagicMock(return_value=_fake_token())

        response = client.post(
            "/api/v1/login", json={"email": "user@example.com", "password": "password123"}
        )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_login_google_returns_tokens():
    with patch("app.api.v1.endpoints.auth.AuthService") as MockAuthService:
        MockAuthService.return_value.login_with_google = AsyncMock(return_value=MagicMock())
        MockAuthService.return_value.issue_tokens = MagicMock(return_value=_fake_token())

        response = client.post("/api/v1/login/google", json={"id_token": "fake-google-id-token"})

    assert response.status_code == 200


def test_refresh_returns_new_tokens():
    with patch("app.api.v1.endpoints.auth.AuthService") as MockAuthService:
        MockAuthService.return_value.refresh = AsyncMock(return_value=_fake_token())

        response = client.post("/api/v1/refresh", json={"refresh_token": "some-refresh-token"})

    assert response.status_code == 200


def test_register_missing_fields_returns_422():
    response = client.post("/api/v1/register", json={"email": "bad-request"})
    assert response.status_code == 422


def test_get_me_returns_current_user():
    fake_user = UserResponse(
        id=uuid.uuid4(),
        email="user@example.com",
        full_name="Test User",
        avatar_url=None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        response = client.get("/api/v1/me")
    finally:
        del app.dependency_overrides[get_current_user]

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
