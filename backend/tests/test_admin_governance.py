"""
Cubre spec 014 (Admin Governance & Access Control):

1. Crear el primer Administrator de una organización -> is_primary=True.
2. Crear un segundo Administrator -> is_primary=False.
3. Crear un Advisor -> is_primary siempre False, sin importar si es el primer InternalUser.
4. Crear con un email ya existente -> 422.
5. Un administrador no-principal intenta desactivar a otro administrador -> 422.
6. El administrador principal desactiva a otro administrador -> 200.
7. Cualquier administrador (principal o no) desactiva a un Advisor -> 200.
8. Cualquier usuario intenta desactivarse a sí mismo (principal incluido) -> 422.
9. Un Advisor autenticado llama cualquier endpoint de /users -> 403.
10. Backfill de la migración 0005: deja exactamente un is_primary=True por organización cuando ya
    existía al menos un Administrator antes de aplicarla.

Extendido con la auditoría de creación y la edición de usuarios (feedback post-014, migración
0006): quién creó a cada InternalUser queda registrado (created_by) pero no se expone en la
respuesta; editar nombre/rol lo puede hacer cualquier admin, el email solo el principal; el
principal no puede perder el rol Administrator vía edición (dejaría el índice único de 0005 sin
nadie que represente).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.use_cases.create_internal_user import CreateInternalUserUseCase
from core.enums.user import InternalUserRole
from core.exceptions.domain import InternalUserEmailAlreadyExistsError
from infrastructure.database.session import AsyncSessionFactory
from modules.configuration.models.organization import OrganizationModel
from modules.users.models.internal_user import InternalUserModel
from scripts.create_user import create_user
from tests.test_security_and_identity import _ORG_SLUG, _login, _seed_organization

_USERS_URL = f"/organizations/{_ORG_SLUG}/users"


async def _create_via_use_case(email: str, full_name: str, role: str) -> object:
    use_case = CreateInternalUserUseCase(session_factory=AsyncSessionFactory)
    return await use_case.execute(_ORG_SLUG, full_name, email, InternalUserRole(role))


async def test_first_administrator_is_primary() -> None:
    await _seed_organization()
    admin = await _create_via_use_case("first-admin@gmail.com", "Primer Admin", "administrator")
    assert admin.is_primary is True


async def test_second_administrator_is_not_primary() -> None:
    await _seed_organization()
    await _create_via_use_case("first-admin@gmail.com", "Primer Admin", "administrator")
    second = await _create_via_use_case("second-admin@gmail.com", "Segundo Admin", "administrator")
    assert second.is_primary is False


async def test_advisor_is_never_primary_even_if_first_user() -> None:
    await _seed_organization()
    advisor = await _create_via_use_case("first-advisor@gmail.com", "Primer Asesor", "advisor")
    assert advisor.is_primary is False


async def test_duplicate_email_is_rejected(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "admin@gmail.com", "Admin", "administrator")
    await _login(client, "admin@gmail.com")

    response = await client.post(
        _USERS_URL,
        json={"full_name": "Otra Persona", "email": "admin@gmail.com", "role": "advisor"},
    )
    assert response.status_code == 422

    use_case = CreateInternalUserUseCase(session_factory=AsyncSessionFactory)
    with pytest.raises(InternalUserEmailAlreadyExistsError):
        await use_case.execute(
            _ORG_SLUG, "Otra Persona", "ADMIN@gmail.com", InternalUserRole.ADVISOR,
        )


async def test_non_primary_admin_cannot_deactivate_another_admin(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "principal@gmail.com", "Admin Principal", "administrator")
    await create_user(_ORG_SLUG, "segundo@gmail.com", "Segundo Admin", "administrator")
    await _login(client, "segundo@gmail.com")

    async with AsyncSessionFactory() as session:
        principal = (
            await session.execute(
                select(InternalUserModel).where(InternalUserModel.email == "principal@gmail.com")
            )
        ).scalar_one()

    # segundo (no principal) intenta desactivar al principal
    response = await client.post(f"{_USERS_URL}/{principal.id}/deactivate")
    assert response.status_code == 422
    assert "primary administrator" in response.json()["detail"].lower()


async def test_primary_admin_deactivates_another_admin(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "principal@gmail.com", "Admin Principal", "administrator")
    await create_user(_ORG_SLUG, "segundo@gmail.com", "Segundo Admin", "administrator")
    await _login(client, "principal@gmail.com")

    async with AsyncSessionFactory() as session:
        second = (
            await session.execute(
                select(InternalUserModel).where(InternalUserModel.email == "segundo@gmail.com")
            )
        ).scalar_one()

    response = await client.post(f"{_USERS_URL}/{second.id}/deactivate")
    assert response.status_code == 200
    assert response.json()["status"] == "inactive"


async def test_any_admin_deactivates_an_advisor(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "principal@gmail.com", "Admin Principal", "administrator")
    await create_user(_ORG_SLUG, "segundo@gmail.com", "Segundo Admin", "administrator")
    await create_user(_ORG_SLUG, "asesor@gmail.com", "Un Asesor", "advisor")
    await _login(client, "segundo@gmail.com")

    async with AsyncSessionFactory() as session:
        advisor = (
            await session.execute(
                select(InternalUserModel).where(InternalUserModel.email == "asesor@gmail.com")
            )
        ).scalar_one()

    response = await client.post(f"{_USERS_URL}/{advisor.id}/deactivate")
    assert response.status_code == 200
    assert response.json()["status"] == "inactive"


async def test_cannot_deactivate_self(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "principal@gmail.com", "Admin Principal", "administrator")
    await _login(client, "principal@gmail.com")

    async with AsyncSessionFactory() as session:
        principal = (
            await session.execute(
                select(InternalUserModel).where(InternalUserModel.email == "principal@gmail.com")
            )
        ).scalar_one()

    response = await client.post(f"{_USERS_URL}/{principal.id}/deactivate")
    assert response.status_code == 422


async def test_advisor_gets_403_on_users_endpoints(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "asesor@gmail.com", "Un Asesor", "advisor")
    await _login(client, "asesor@gmail.com")

    list_response = await client.get(_USERS_URL)
    assert list_response.status_code == 403

    create_response = await client.post(
        _USERS_URL,
        json={"full_name": "Otro", "email": "otro@gmail.com", "role": "advisor"},
    )
    assert create_response.status_code == 403


async def test_created_by_is_recorded_for_audit(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "principal@gmail.com", "Admin Principal", "administrator")
    await _login(client, "principal@gmail.com")
    principal_id = (await client.get("/auth/me")).json()["id"]

    response = await client.post(
        _USERS_URL,
        json={"full_name": "Nuevo Asesor", "email": "nuevo@gmail.com", "role": "advisor"},
    )
    assert response.status_code == 201, response.text

    async with AsyncSessionFactory() as session:
        created = (
            await session.execute(
                select(InternalUserModel).where(InternalUserModel.email == "nuevo@gmail.com")
            )
        ).scalar_one()
        assert str(created.created_by) == principal_id

    # No se expone en la respuesta -- es solo para auditoría, no algo que la UI necesite mostrar.
    assert "created_by" not in response.json()


async def test_created_by_is_null_for_bootstrap_script_users() -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "bootstrap@gmail.com", "Bootstrap Admin", "administrator")

    async with AsyncSessionFactory() as session:
        user = (
            await session.execute(
                select(InternalUserModel).where(InternalUserModel.email == "bootstrap@gmail.com")
            )
        ).scalar_one()
        assert user.created_by is None


async def test_update_internal_user_changes_name_and_role(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "principal@gmail.com", "Admin Principal", "administrator")
    await create_user(_ORG_SLUG, "asesor@gmail.com", "Asesor Viejo", "advisor")
    await _login(client, "principal@gmail.com")

    async with AsyncSessionFactory() as session:
        advisor = (
            await session.execute(
                select(InternalUserModel).where(InternalUserModel.email == "asesor@gmail.com")
            )
        ).scalar_one()

    response = await client.put(
        f"{_USERS_URL}/{advisor.id}",
        json={
            "full_name": "Asesor Nuevo Nombre",
            "email": "asesor@gmail.com",
            "role": "administrator",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["full_name"] == "Asesor Nuevo Nombre"
    assert body["role"] == "administrator"


async def test_only_primary_admin_can_edit_email(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "principal@gmail.com", "Admin Principal", "administrator")
    await create_user(_ORG_SLUG, "segundo@gmail.com", "Segundo Admin", "administrator")
    await _login(client, "segundo@gmail.com")

    async with AsyncSessionFactory() as session:
        target = (
            await session.execute(
                select(InternalUserModel).where(InternalUserModel.email == "segundo@gmail.com")
            )
        ).scalar_one()

    # segundo (no principal) intenta cambiar su propio email
    response = await client.put(
        f"{_USERS_URL}/{target.id}",
        json={
            "full_name": "Segundo Admin",
            "email": "nuevo-email@gmail.com",
            "role": "administrator",
        },
    )
    assert response.status_code == 422
    assert "email" in response.json()["detail"].lower()


async def test_cannot_demote_primary_admin_role(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "principal@gmail.com", "Admin Principal", "administrator")
    await _login(client, "principal@gmail.com")
    principal_id = (await client.get("/auth/me")).json()["id"]

    response = await client.put(
        f"{_USERS_URL}/{principal_id}",
        json={"full_name": "Admin Principal", "email": "principal@gmail.com", "role": "advisor"},
    )
    assert response.status_code == 422


async def test_migration_backfill_leaves_exactly_one_primary_per_organization() -> None:
    """No corre Alembic de verdad (los tests usan Base.metadata.create_all) -- ejecuta la misma
    sentencia SQL de la migración 0005 contra filas sembradas a mano, para validar su lógica de
    backfill de forma aislada."""
    await _seed_organization()
    async with AsyncSessionFactory() as session:
        org = (
            await session.execute(select(OrganizationModel.id).limit(1))
        ).scalar_one()

        older = datetime.now(tz=UTC) - timedelta(days=2)
        newer = datetime.now(tz=UTC) - timedelta(days=1)
        for email, created_at in (
            ("older-admin@gmail.com", older),
            ("newer-admin@gmail.com", newer),
        ):
            session.add(
                InternalUserModel(
                    id=uuid.uuid4(),
                    organization_id=org,
                    email=email,
                    full_name=email,
                    role="administrator",
                    status="active",
                    created_at=created_at,
                    updated_at=created_at,
                    is_primary=False,
                )
            )
        await session.commit()

        await session.execute(
            text(
                """
                UPDATE internal_users
                SET is_primary = 1
                WHERE id IN (
                    SELECT id FROM internal_users iu
                    WHERE role = 'administrator'
                    AND created_at = (
                        SELECT MIN(created_at) FROM internal_users
                        WHERE organization_id = iu.organization_id AND role = 'administrator'
                    )
                )
                """
            )
        )
        await session.commit()

        primaries = (
            await session.execute(
                select(InternalUserModel).where(InternalUserModel.is_primary == True)  # noqa: E712
            )
        ).scalars().all()
        assert len(primaries) == 1
        assert primaries[0].email == "older-admin@gmail.com"
