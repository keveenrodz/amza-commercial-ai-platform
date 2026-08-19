from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.value_objects.identifiers import ContactId, ContactNoteId, InternalUserId


@dataclass(frozen=True)
class ContactNote:
    id: ContactNoteId
    contact_id: ContactId
    author_id: InternalUserId
    content: str
    created_at: datetime
