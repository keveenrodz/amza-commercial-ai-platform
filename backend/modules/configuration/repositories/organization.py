from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.organization import Organization
from core.enums.user import OrganizationStatus
from core.value_objects.identifiers import OrganizationId
from modules.configuration.models.organization import OrganizationModel


def _to_entity(model: OrganizationModel) -> Organization:
    return Organization(
        id=OrganizationId(value=model.id),
        name=model.name,
        slug=model.slug,
        timezone=model.timezone,
        language=model.language,
        status=OrganizationStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyOrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: OrganizationId) -> Organization | None:
        result = await self._session.execute(
            select(OrganizationModel).where(OrganizationModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self._session.execute(
            select(OrganizationModel).where(OrganizationModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None
