from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from core.interfaces.auth import AuthenticatedIdentity

_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
_VALID_ISSUERS = ("https://accounts.google.com", "accounts.google.com")


class GoogleAuthenticationError(Exception):
    """El id_token de Google no pasó una o más invariantes del protocolo OIDC (firma, issuer,
    audience, expiración, o email_verified). Nunca es un error de negocio -- ver
    AuthenticateUseCase para la distinción con AccessDeniedError."""


class GoogleOAuthProvider:
    """Implementa AuthProvider (core/interfaces/auth.py) vía Authorization Code flow. Sin PKCE
    -- el backend es un cliente confidencial (guarda client_secret), esa protección es para
    clientes públicos. Sin authlib -- httpx + PyJWT.PyJWKClient bastan (ver spec 008 sección 2)."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._jwks_client = PyJWKClient(_JWKS_URI)

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
        return f"{_AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> AuthenticatedIdentity:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GoogleAuthenticationError(f"Token exchange failed: {exc}") from exc

        id_token = response.json()["id_token"]
        claims = self._verify_id_token(id_token)

        if not claims.get("email_verified"):
            raise GoogleAuthenticationError("Google email is not verified")

        return AuthenticatedIdentity(
            email=claims["email"],
            full_name=claims.get("name", claims["email"]),
            provider="google",
        )

    def _verify_id_token(self, id_token: str) -> dict[str, Any]:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(id_token)
            claims: dict[str, Any] = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=_VALID_ISSUERS,
            )
        except InvalidTokenError as exc:
            raise GoogleAuthenticationError(f"Invalid Google id_token: {exc}") from exc
        return claims
