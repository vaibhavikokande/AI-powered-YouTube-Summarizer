import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.deps import get_current_user, get_current_user_optional
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, create_refresh_token


def _fake_user(is_active=True):
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_active = is_active
    return user


async def test_get_current_user_rejects_missing_header():
    with pytest.raises(UnauthorizedError):
        await get_current_user(authorization=None, db=MagicMock())


async def test_get_current_user_rejects_malformed_header():
    with pytest.raises(UnauthorizedError):
        await get_current_user(authorization="NotBearer abc", db=MagicMock())


async def test_get_current_user_rejects_refresh_token_used_as_access():
    user = _fake_user()
    token = create_refresh_token(str(user.id))

    with patch("app.api.deps.UserRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=user)
        with pytest.raises(UnauthorizedError):
            await get_current_user(authorization=f"Bearer {token}", db=MagicMock())


async def test_get_current_user_returns_user_for_valid_token():
    user = _fake_user()
    token = create_access_token(str(user.id))

    with patch("app.api.deps.UserRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=user)
        result = await get_current_user(authorization=f"Bearer {token}", db=MagicMock())

    assert result is user


async def test_get_current_user_rejects_inactive_user():
    user = _fake_user(is_active=False)
    token = create_access_token(str(user.id))

    with patch("app.api.deps.UserRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=user)
        with pytest.raises(UnauthorizedError):
            await get_current_user(authorization=f"Bearer {token}", db=MagicMock())


async def test_get_current_user_optional_returns_none_without_header():
    result = await get_current_user_optional(authorization=None, db=MagicMock())
    assert result is None


async def test_get_current_user_optional_returns_none_for_invalid_token():
    result = await get_current_user_optional(
        authorization="Bearer not-a-real-token", db=MagicMock()
    )
    assert result is None


async def test_get_current_user_optional_returns_user_for_valid_token():
    user = _fake_user()
    token = create_access_token(str(user.id))

    with patch("app.api.deps.UserRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=user)
        result = await get_current_user_optional(authorization=f"Bearer {token}", db=MagicMock())

    assert result is user
