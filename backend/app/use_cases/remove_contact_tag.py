from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.contact import Contact
from core.exceptions.domain import ContactNotFoundError
from core.value_objects.identifiers import ContactId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class RemoveContactTagUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, contact_id: ContactId, tag: str) -> Contact:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            contact = await uow.contacts.get_by_id(contact_id)
            if contact is None:
                raise ContactNotFoundError(contact_id)
            if tag in contact.tags:
                contact.tags.remove(tag)
                await uow.contacts.save(contact)
                await uow.commit()
        return contact
