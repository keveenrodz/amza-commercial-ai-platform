from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.contact_note import ContactNote
from core.exceptions.domain import ContactNotFoundError
from core.value_objects.identifiers import ContactId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


@dataclass(frozen=True)
class ContactNoteWithAuthor:
    note: ContactNote
    author_name: str


class ListContactNotesUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, contact_id: ContactId) -> list[ContactNoteWithAuthor]:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            contact = await uow.contacts.get_by_id(contact_id)
            if contact is None:
                raise ContactNotFoundError(contact_id)

            notes = await uow.contact_notes.list_by_contact(contact_id)

            # get_by_id() en un loop -- aceptable a esta escala (pocas notas por contacto, pocos
            # autores distintos); a diferencia de ContactRepository.list_by_ids (spec 012), aquí
            # no vale la pena un método batch solo para esto.
            result: list[ContactNoteWithAuthor] = []
            for note in notes:
                author = await uow.internal_users.get_by_id(note.author_id)
                author_name = author.full_name if author is not None else "Usuario desconocido"
                result.append(ContactNoteWithAuthor(note=note, author_name=author_name))
            return result
