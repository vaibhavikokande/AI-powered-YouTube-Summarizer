from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from authlib.jose.errors import JoseError

from app.core.exceptions import UnauthorizedError
from app.services.google_oauth_service import GoogleOAuthService


class _FakeClaims(dict):
    """Mimics authlib's JWTClaims: dict-like plus a `.validate()` method."""

    def validate(self):
        pass


def _mock_settings(client_id="test-client-id"):
    return MagicMock(GOOGLE_OAUTH_CLIENT_ID=client_id)


async def test_verify_id_token_raises_when_oauth_not_configured():
    with patch(
        "app.services.google_oauth_service.get_settings", return_value=_mock_settings(client_id=None)
    ):
        with pytest.raises(UnauthorizedError):
            await GoogleOAuthService().verify_id_token("some-token")


async def test_verify_id_token_returns_claims_for_valid_token():
    fake_claims = _FakeClaims(
        sub="g-123", email="a@b.com", aud="test-client-id", iss="https://accounts.google.com"
    )

    service = GoogleOAuthService()

    with (
        patch("app.services.google_oauth_service.get_settings", return_value=_mock_settings()),
        patch.object(service, "_fetch_jwks", new=AsyncMock(return_value=MagicMock())),
        patch("app.services.google_oauth_service.JsonWebToken") as MockJWT,
    ):
        MockJWT.return_value.decode.return_value = fake_claims
        result = await service.verify_id_token("some-token")

    assert result == dict(fake_claims)


async def test_verify_id_token_rejects_wrong_audience():
    fake_claims = _FakeClaims(
        sub="g-123", email="a@b.com", aud="someone-elses-client-id", iss="https://accounts.google.com"
    )

    service = GoogleOAuthService()

    with (
        patch("app.services.google_oauth_service.get_settings", return_value=_mock_settings()),
        patch.object(service, "_fetch_jwks", new=AsyncMock(return_value=MagicMock())),
        patch("app.services.google_oauth_service.JsonWebToken") as MockJWT,
    ):
        MockJWT.return_value.decode.return_value = fake_claims
        with pytest.raises(UnauthorizedError):
            await service.verify_id_token("some-token")


async def test_verify_id_token_wraps_jose_errors():
    service = GoogleOAuthService()

    with (
        patch("app.services.google_oauth_service.get_settings", return_value=_mock_settings()),
        patch.object(service, "_fetch_jwks", new=AsyncMock(return_value=MagicMock())),
        patch("app.services.google_oauth_service.JsonWebToken") as MockJWT,
    ):
        MockJWT.return_value.decode.side_effect = JoseError("bad signature")
        with pytest.raises(UnauthorizedError):
            await service.verify_id_token("some-token")
