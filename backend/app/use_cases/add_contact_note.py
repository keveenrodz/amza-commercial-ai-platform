from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.use_cases.list_contact_notes import ContactNoteWithAuthor
from core.entities.contact_note import ContactNote
from core.exceptions.domain import ContactNotFoundError, InternalUserNotFoundError
from core.value_objects.identifiers import ContactId, ContactNoteId, InternalUserId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class AddContactNoteUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        contact_id: ContactId,
        author_id: InternalUserId,
        content: str,
    ) -> ContactNoteWithAuthor:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            contact = await uow.contacts.get_by_id(contact_id)
            if contact is None:
                raise ContactNotFoundError(contact_id)

            author = await uow.internal_users.get_by_id(author_id)
            if author is None:
                raise InternalUserNotFoundError(author_id)

            note = ContactNote(
                id=ContactNoteId.generate(),
                contact_id=contact_id,
                author_id=author_id,
                content=content,
                created_at=datetime.now(tz=UTC),
            )
            await uow.contact_notes.save(note)
            await uow.commit()
        return ContactNoteWithAuthor(note=note, author_name=author.full_name)
