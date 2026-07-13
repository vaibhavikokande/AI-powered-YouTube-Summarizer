from typing import Any

import httpx
from authlib.jose import JsonWebKey, JsonWebToken
from authlib.jose.errors import JoseError

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

_GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}


class GoogleOAuthService:
    """Verifies a Google Identity Services ID token.

    Deliberately doesn't depend on the `google-auth` SDK — the ID token is a
    standard JWT, and authlib + Google's public JWKS endpoint is enough to
    verify its signature and claims (audience, issuer, expiry).
    """

    async def verify_id_token(self, id_token: str) -> dict[str, Any]:
        settings = get_settings()
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise UnauthorizedError("Google OAuth is not configured on this server.")

        jwks = await self._fetch_jwks()

        try:
            claims = JsonWebToken(["RS256"]).decode(id_token, key=jwks)
            claims.validate()
        except JoseError as exc:
            raise UnauthorizedError("Invalid Google ID token.") from exc

        if claims.get("aud") != settings.GOOGLE_OAUTH_CLIENT_ID:
            raise UnauthorizedError("Google ID token was not issued for this application.")
        if claims.get("iss") not in _GOOGLE_ISSUERS:
            raise UnauthorizedError("Google ID token has an unexpected issuer.")

        return dict(claims)

    async def _fetch_jwks(self) -> Any:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(_GOOGLE_JWKS_URL)
            response.raise_for_status()
            return JsonWebKey.import_key_set(response.json())
