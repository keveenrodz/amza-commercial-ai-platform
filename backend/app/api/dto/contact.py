from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.use_cases.list_contact_notes import ContactNoteWithAuthor
from core.entities.contact import Contact


class ContactSummaryResponse(BaseModel):
    display_name: str
    phone_number: str | None
    tags: list[str]
    is_favorite: bool

    @classmethod
    def from_domain(cls, contact: Contact) -> ContactSummaryResponse:
        return cls(
            display_name=contact.display_name,
            phone_number=contact.phone_number,
            tags=contact.tags,
            is_favorite=contact.is_favorite,
        )


class AddTagRequest(BaseModel):
    tag: str


class AddContactNoteRequest(BaseModel):
    advisor_id: str
    content: str


class ContactNoteResponse(BaseModel):
    id: str
    author_name: str
    content: str
    created_at: datetime

    @classmethod
    def from_domain(cls, item: ContactNoteWithAuthor) -> ContactNoteResponse:
        return cls(
            id=str(item.note.id),
            author_name=item.author_name,
            content=item.note.content,
            created_at=item.note.created_at,
        )
