from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.internal_user import InternalUser
from core.exceptions.domain import OrganizationSlugNotFoundError
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class ListInternalUsersUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, organization_slug: str) -> list[InternalUser]:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)
            return await uow.internal_users.list_by_organization(organization.id)
