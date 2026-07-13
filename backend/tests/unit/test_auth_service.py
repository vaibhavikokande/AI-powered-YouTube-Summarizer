import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import UnauthorizedError, ValidationAppError
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.services.auth_service import AuthService


def _service_with_mocks() -> AuthService:
    google_oauth = MagicMock()
    google_oauth.verify_id_token = AsyncMock()

    service = AuthService(session=MagicMock(), google_oauth=google_oauth)
    service._repository = MagicMock()
    return service


def _fake_user(**overrides):
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_active = True
    user.hashed_password = hash_password("correct-password")
    for key, value in overrides.items():
        setattr(user, key, value)
    return user


async def test_register_creates_user_when_email_is_new():
    service = _service_with_mocks()
    service._repository.get_by_email = AsyncMock(return_value=None)
    service._repository.create = AsyncMock(return_value="new-user")

    result = await service.register("new@example.com", "password123", "New User")

    assert result == "new-user"
    service._repository.create.assert_called_once()


async def test_register_rejects_duplicate_email():
    service = _service_with_mocks()
    service._repository.get_by_email = AsyncMock(return_value=_fake_user())

    with pytest.raises(ValidationAppError):
        await service.register("existing@example.com", "password123", None)


async def test_authenticate_accepts_correct_password():
    service = _service_with_mocks()
    user = _fake_user()
    service._repository.get_by_email = AsyncMock(return_value=user)

    result = await service.authenticate("user@example.com", "correct-password")

    assert result is user


async def test_authenticate_rejects_wrong_password():
    service = _service_with_mocks()
    service._repository.get_by_email = AsyncMock(return_value=_fake_user())

    with pytest.raises(UnauthorizedError):
        await service.authenticate("user@example.com", "wrong-password")


async def test_authenticate_rejects_unknown_email():
    service = _service_with_mocks()
    service._repository.get_by_email = AsyncMock(return_value=None)

    with pytest.raises(UnauthorizedError):
        await service.authenticate("nobody@example.com", "whatever")


async def test_authenticate_rejects_inactive_user():
    service = _service_with_mocks()
    service._repository.get_by_email = AsyncMock(return_value=_fake_user(is_active=False))

    with pytest.raises(UnauthorizedError):
        await service.authenticate("user@example.com", "correct-password")


async def test_login_with_google_returns_existing_user_by_google_id():
    service = _service_with_mocks()
    service._google_oauth.verify_id_token = AsyncMock(return_value={"sub": "g-123", "email": "a@b.com"})
    existing = _fake_user()
    service._repository.get_by_google_id = AsyncMock(return_value=existing)

    result = await service.login_with_google("some-id-token")

    assert result is existing
    service._repository.create.assert_not_called()


async def test_login_with_google_links_existing_email_account():
    service = _service_with_mocks()
    service._google_oauth.verify_id_token = AsyncMock(
        return_value={"sub": "g-123", "email": "a@b.com"}
    )
    service._repository.get_by_google_id = AsyncMock(return_value=None)
    existing_by_email = _fake_user()
    service._repository.get_by_email = AsyncMock(return_value=existing_by_email)

    result = await service.login_with_google("some-id-token")

    assert result is existing_by_email
    service._repository.create.assert_not_called()


async def test_login_with_google_creates_new_user_when_none_found():
    service = _service_with_mocks()
    service._google_oauth.verify_id_token = AsyncMock(
        return_value={"sub": "g-123", "email": "new@b.com", "name": "New", "picture": "http://x/y.png"}
    )
    service._repository.get_by_google_id = AsyncMock(return_value=None)
    service._repository.get_by_email = AsyncMock(return_value=None)
    service._repository.create = AsyncMock(return_value="brand-new-user")

    result = await service.login_with_google("some-id-token")

    assert result == "brand-new-user"
    service._repository.create.assert_called_once_with(
        "new@b.com", google_id="g-123", full_name="New", avatar_url="http://x/y.png"
    )


async def test_refresh_rejects_access_token_used_as_refresh():
    service = _service_with_mocks()
    access_token = create_access_token(str(uuid.uuid4()))

    with pytest.raises(UnauthorizedError):
        await service.refresh(access_token)


async def test_refresh_issues_new_tokens_for_valid_refresh_token():
    service = _service_with_mocks()
    user = _fake_user()
    service._repository.get_by_id = AsyncMock(return_value=user)
    refresh_token = create_refresh_token(str(user.id))

    result = await service.refresh(refresh_token)

    assert result.access_token
    assert result.refresh_token
