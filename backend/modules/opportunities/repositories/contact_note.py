from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.contact_note import ContactNote
from core.value_objects.identifiers import ContactId, ContactNoteId, InternalUserId
from modules.opportunities.models.contact_note import ContactNoteModel


def _to_entity(model: ContactNoteModel) -> ContactNote:
    return ContactNote(
        id=ContactNoteId(value=model.id),
        contact_id=ContactId(value=model.contact_id),
        author_id=InternalUserId(value=model.author_id),
        content=model.content,
        created_at=model.created_at,
    )


def _from_entity(entity: ContactNote) -> ContactNoteModel:
    return ContactNoteModel(
        id=entity.id.value,
        contact_id=entity.contact_id.value,
        author_id=entity.author_id.value,
        content=entity.content,
        created_at=entity.created_at,
    )


class SQLAlchemyContactNoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_contact(self, contact_id: ContactId) -> list[ContactNote]:
        result = await self._session.execute(
            select(ContactNoteModel)
            .where(ContactNoteModel.contact_id == contact_id.value)
            .order_by(ContactNoteModel.created_at.asc())
        )
        return [_to_entity(model) for model in result.scalars()]

    async def save(self, note: ContactNote) -> None:
        # append-only: nunca se actualiza una nota existente, cada llamada crea una fila nueva.
        self._session.add(_from_entity(note))
