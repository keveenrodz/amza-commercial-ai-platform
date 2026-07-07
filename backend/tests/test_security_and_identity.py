"""
Cubre los 6 escenarios de validación de spec 008 (Security & Identity):

1. Crear un InternalUser con scripts/create_user.py.
2. Iniciar sesión con Google (AuthProvider fake -- nunca se llama a Google real en tests).
3. Solo un InternalUser activo obtiene acceso.
4. GET /auth/me devuelve el usuario autenticado.
5. /organizations/* devuelve 401 sin autenticación y funciona con una sesión válida.
6. Desactivar el usuario y confirmar que la siguiente petición autenticada ya no tiene acceso.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.dependencies import get_authenticate_use_case
from app.use_cases.authenticate_with_provider import AuthenticateUseCase
from core.interfaces.auth import AuthenticatedIdentity
from infrastructure.database.session import AsyncSessionFactory
from modules.configuration.models.organization import OrganizationModel
from modules.users.models.internal_user import InternalUserModel
from scripts.create_user import create_user

_ORG_SLUG = "test-org"


class _FakeAuthProvider:
    """Nunca llama a Google -- exchange_code() devuelve exactamente la identidad configurada,
    o lanza si should_fail=True. Esto es lo único que sustituye a GoogleOAuthProvider en tests;
    AuthenticateUseCase, get_current_user y los routers corren sin ningún mock."""

    def __init__(self, identity: AuthenticatedIdentity | None = None) -> None:
        self._identity = identity

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        return f"https://fake.example/authorize?state={state}"

    async def exchange_code(self, code: str, redirect_uri: str) -> AuthenticatedIdentity:
        if self._identity is None:
            raise AssertionError("FakeAuthProvider sin identidad configurada")
        return self._identity


async def _seed_organization(slug: str = _ORG_SLUG) -> None:
    async with AsyncSessionFactory() as session:
        now = datetime.now(tz=UTC)
        session.add(
            OrganizationModel(
                id=uuid.uuid4(),
                name="Test Org",
                slug=slug,
                timezone="America/Bogota",
                language="es",
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()


async def _deactivate_user(email: str) -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(
            update(InternalUserModel)
            .where(InternalUserModel.email == email.lower())
            .values(status="inactive")
        )
        await session.commit()


def _override_auth_provider(app, identity: AuthenticatedIdentity) -> None:  # noqa: ANN001
    fake_provider = _FakeAuthProvider(identity)
    app.dependency_overrides[get_authenticate_use_case] = lambda: AuthenticateUseCase(
        session_factory=AsyncSessionFactory,
        auth_provider=fake_provider,
    )


async def _login(client: AsyncClient, email: str) -> None:
    """Ejecuta el flujo completo /auth/google/login -> /auth/google/callback con el
    FakeAuthProvider ya inyectado. Al terminar, el AsyncClient tiene la cookie de sesión."""
    from app.main import app

    identity = AuthenticatedIdentity(email=email, full_name="Test User", provider="google")
    _override_auth_provider(app, identity)

    login_response = await client.get("/auth/google/login", follow_redirects=False)
    redirect_url = login_response.headers["location"]
    state = redirect_url.split("state=")[1].split("&")[0]

    callback_response = await client.get(
        "/auth/google/callback",
        params={"code": "fake-code", "state": state},
    )
    assert callback_response.status_code == 200, callback_response.text


async def test_scenario_1_create_user_via_bootstrap_script() -> None:
    await _seed_organization()

    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")

    async with AsyncSessionFactory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(InternalUserModel).where(InternalUserModel.email == "juan@gmail.com")
        )
        user = result.scalar_one()
        assert user.role == "advisor"
        assert user.status == "active"


async def test_scenario_1b_duplicate_email_is_rejected_case_insensitively() -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")

    with pytest.raises(SystemExit):
        await create_user(_ORG_SLUG, "JUAN@gmail.com", "Otro Nombre", "administrator")


async def test_scenario_2_and_4_login_and_me(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")

    await _login(client, "juan@gmail.com")

    me_response = await client.get("/auth/me")
    assert me_response.status_code == 200
    body = me_response.json()
    assert body["email"] == "juan@gmail.com"
    assert body["role"] == "advisor"


async def test_scenario_3_unknown_email_is_denied(client: AsyncClient) -> None:
    await _seed_organization()
    # Nadie con este email existe como InternalUser -- Google podría autenticarlo con éxito
    # igual, el punto es que eso no basta.
    from app.main import app

    identity = AuthenticatedIdentity(
        email="extrano@gmail.com", full_name="Extrano", provider="google"
    )
    _override_auth_provider(app, identity)

    login_response = await client.get("/auth/google/login", follow_redirects=False)
    state = login_response.headers["location"].split("state=")[1].split("&")[0]

    callback_response = await client.get(
        "/auth/google/callback",
        params={"code": "fake-code", "state": state},
    )
    assert callback_response.status_code == 403
    assert "access_token" not in callback_response.cookies


async def test_scenario_5_organizations_requires_auth(client: AsyncClient) -> None:
    await _seed_organization()

    unauthenticated = await client.get(f"/organizations/{_ORG_SLUG}/opportunities")
    assert unauthenticated.status_code == 401

    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    authenticated = await client.get(f"/organizations/{_ORG_SLUG}/opportunities")
    assert authenticated.status_code == 200
    assert authenticated.json() == []


async def test_scenario_6_deactivated_user_loses_access_immediately(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    still_active = await client.get("/auth/me")
    assert still_active.status_code == 200

    await _deactivate_user("juan@gmail.com")

    # Misma cookie de sesión, mismo JWT sin expirar -- pero get_current_user() vuelve a
    # consultar la BD en cada request (spec 008 sección 4), así que pierde acceso de inmediato,
    # sin esperar a que el JWT expire.
    after_deactivation = await client.get("/auth/me")
    assert after_deactivation.status_code == 401
