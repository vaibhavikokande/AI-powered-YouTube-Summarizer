import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.enums import SummaryType
from app.schemas.share_link import ShareLinkResponse
from app.schemas.summary import KeyTakeaways, SummaryResponse, Topics


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def _fake_share_link_response() -> ShareLinkResponse:
    return ShareLinkResponse(
        id=uuid.uuid4(),
        token="abc123",
        summary_id=uuid.uuid4(),
        expires_at=None,
        created_at=datetime.now(timezone.utc),
    )


def _fake_summary_response() -> SummaryResponse:
    return SummaryResponse(
        id=uuid.uuid4(),
        video_id=uuid.uuid4(),
        summary_type=SummaryType.MEDIUM,
        content="A summary.",
        key_takeaways=KeyTakeaways(),
        timestamped_sections=[],
        topics=Topics(),
        mindmap_markdown=None,
        llm_provider="claude",
        created_at=datetime.now(timezone.utc),
    )


def test_create_share_link_returns_token():
    with patch("app.api.v1.endpoints.share.ShareService") as MockService:
        MockService.return_value.create_share_link = AsyncMock(
            return_value=_fake_share_link_response()
        )

        response = client.post("/api/v1/share", json={"summary_id": str(uuid.uuid4())})

    assert response.status_code == 200
    assert response.json()["token"] == "abc123"


def test_get_shared_summary_returns_summary():
    with patch("app.api.v1.endpoints.share.ShareService") as MockService:
        MockService.return_value.resolve_share_link = AsyncMock(
            return_value=_fake_summary_response()
        )

        response = client.get("/api/v1/share/abc123")

    assert response.status_code == 200
    assert response.json()["content"] == "A summary."
