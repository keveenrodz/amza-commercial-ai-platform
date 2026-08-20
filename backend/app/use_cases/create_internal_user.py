from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.internal_user import InternalUser
from core.enums.user import InternalUserRole, InternalUserStatus
from core.exceptions.domain import (
    InternalUserEmailAlreadyExistsError,
    OrganizationSlugNotFoundError,
)
from core.value_objects.identifiers import InternalUserId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class CreateInternalUserUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        organization_slug: str,
        full_name: str,
        email: str,
        role: InternalUserRole,
        actor_id: InternalUserId | None = None,
    ) -> InternalUser:
        # actor_id es None solo para el bootstrap por script (scripts/create_user.py, antes de
        # que exista ningún administrador que pueda estar "agregando" a alguien) -- cualquier
        # creación real vía la pantalla de administración siempre lo trae (spec 014 sección 5:
        # el actor real, no algo que el body pueda declarar).
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)

            if await uow.internal_users.get_by_email(email) is not None:
                raise InternalUserEmailAlreadyExistsError(email)

            is_primary = False
            if role == InternalUserRole.ADMINISTRATOR:
                existing_primary = await uow.internal_users.get_primary_administrator(
                    organization.id,
                )
                is_primary = existing_primary is None

            now = datetime.now(tz=UTC)
            user = InternalUser(
                id=InternalUserId.generate(),
                organization_id=organization.id,
                full_name=full_name,
                email=email,
                role=role,
                status=InternalUserStatus.ACTIVE,
                is_primary=is_primary,
                created_at=now,
                updated_at=now,
                created_by=actor_id,
            )
            await uow.internal_users.save(user)
            await uow.commit()
        return user
