from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.contact import Contact
from core.enums.channel import ChannelType
from core.enums.user import ContactStatus
from core.value_objects.identifiers import ContactId, OrganizationId
from modules.opportunities.models.contact import ContactModel


def _to_entity(model: ContactModel) -> Contact:
    return Contact(
        id=ContactId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        channel_type=ChannelType(model.channel_type),
        external_id=model.external_id,
        display_name=model.display_name,
        status=ContactStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        phone_number=model.phone_number,
        email=model.email,
    )


def _from_entity(entity: Contact) -> ContactModel:
    return ContactModel(
        id=entity.id.value,
        organization_id=entity.organization_id.value,
        channel_type=entity.channel_type.value,
        external_id=entity.external_id,
        display_name=entity.display_name,
        status=entity.status.value,
        phone_number=entity.phone_number,
        email=entity.email,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class SQLAlchemyContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: ContactId) -> Contact | None:
        result = await self._session.execute(
            select(ContactModel).where(ContactModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_external_id(
        self,
        external_id: str,
        channel_type: ChannelType,
        organization_id: OrganizationId,
    ) -> Contact | None:
        result = await self._session.execute(
            select(ContactModel).where(
                ContactModel.external_id == external_id,
                ContactModel.channel_type == channel_type.value,
                ContactModel.organization_id == organization_id.value,
            )
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, contact: Contact) -> None:
        await self._session.merge(_from_entity(contact))
