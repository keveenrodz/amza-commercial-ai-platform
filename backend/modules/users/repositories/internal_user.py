from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.internal_user import InternalUser
from core.enums.user import InternalUserRole, InternalUserStatus
from core.value_objects.identifiers import InternalUserId, OrganizationId
from modules.users.models.internal_user import InternalUserModel


def _to_entity(model: InternalUserModel) -> InternalUser:
    return InternalUser(
        id=InternalUserId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        full_name=model.full_name,
        email=model.email,
        role=InternalUserRole(model.role),
        status=InternalUserStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _from_entity(entity: InternalUser) -> InternalUserModel:
    return InternalUserModel(
        id=entity.id.value,
        organization_id=entity.organization_id.value,
        full_name=entity.full_name,
        email=entity.email.lower(),
        role=entity.role.value,
        status=entity.status.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class SQLAlchemyInternalUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: InternalUserId) -> InternalUser | None:
        result = await self._session.execute(
            select(InternalUserModel).where(InternalUserModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_email(self, email: str) -> InternalUser | None:
        result = await self._session.execute(
            select(InternalUserModel).where(InternalUserModel.email == email.lower())
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, internal_user: InternalUser) -> None:
        await self._session.merge(_from_entity(internal_user))

    async def list_advisors_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> list[InternalUser]:
        result = await self._session.execute(
            select(InternalUserModel)
            .where(
                InternalUserModel.organization_id == organization_id.value,
                InternalUserModel.role == InternalUserRole.ADVISOR.value,
                InternalUserModel.status == InternalUserStatus.ACTIVE.value,
            )
            .order_by(InternalUserModel.full_name.asc())
        )
        return [_to_entity(m) for m in result.scalars().all()]
