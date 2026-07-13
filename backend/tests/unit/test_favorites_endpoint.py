import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.schemas.favorite import FavoriteResponse


async def _override_get_db():
    yield None


def _fake_current_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    return user


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[get_current_user] = _fake_current_user
client = TestClient(app)


def _fake_favorite() -> FavoriteResponse:
    return FavoriteResponse(
        id=uuid.uuid4(), video_id=uuid.uuid4(), created_at=datetime.now(timezone.utc)
    )


def test_list_favorites_returns_items():
    with patch("app.api.v1.endpoints.favorites.FavoriteService") as MockService:
        MockService.return_value.list_favorites = AsyncMock(return_value=[_fake_favorite()])

        response = client.get("/api/v1/favorites")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_add_favorite_returns_201():
    with patch("app.api.v1.endpoints.favorites.FavoriteService") as MockService:
        MockService.return_value.add_favorite = AsyncMock(return_value=_fake_favorite())

        response = client.post(f"/api/v1/favorites/{uuid.uuid4()}")

    assert response.status_code == 201


def test_remove_favorite_returns_204():
    with patch("app.api.v1.endpoints.favorites.FavoriteService") as MockService:
        MockService.return_value.remove_favorite = AsyncMock()

        response = client.delete(f"/api/v1/favorites/{uuid.uuid4()}")

    assert response.status_code == 204
