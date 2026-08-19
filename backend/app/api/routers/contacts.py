from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dto.contact import (
    AddContactNoteRequest,
    AddTagRequest,
    ContactNoteResponse,
    ContactSummaryResponse,
)
from app.dependencies import (
    get_add_contact_note_use_case,
    get_add_contact_tag_use_case,
    get_list_contact_notes_use_case,
    get_remove_contact_tag_use_case,
    get_toggle_contact_favorite_use_case,
)
from app.security import get_current_user
from app.use_cases.add_contact_note import AddContactNoteUseCase
from app.use_cases.add_contact_tag import AddContactTagUseCase
from app.use_cases.list_contact_notes import ListContactNotesUseCase
from app.use_cases.remove_contact_tag import RemoveContactTagUseCase
from app.use_cases.toggle_contact_favorite import ToggleContactFavoriteUseCase
from core.value_objects.identifiers import ContactId, InternalUserId

# Mismo criterio que opportunities.py: protegido a nivel de router, sin distinción de rol
# todavía (ver spec 014 para cuándo eso cambie).
router = APIRouter(
    prefix="/organizations/{organization_slug}/contacts",
    tags=["contacts"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/{contact_id}/tags")
async def add_contact_tag(
    organization_slug: str,
    contact_id: str,
    body: AddTagRequest,
    use_case: AddContactTagUseCase = Depends(get_add_contact_tag_use_case),
) -> ContactSummaryResponse:
    contact = await use_case.execute(ContactId.from_string(contact_id), body.tag)
    return ContactSummaryResponse.from_domain(contact)


@router.delete("/{contact_id}/tags/{tag}")
async def remove_contact_tag(
    organization_slug: str,
    contact_id: str,
    tag: str,
    use_case: RemoveContactTagUseCase = Depends(get_remove_contact_tag_use_case),
) -> ContactSummaryResponse:
    contact = await use_case.execute(ContactId.from_string(contact_id), tag)
    return ContactSummaryResponse.from_domain(contact)


@router.post("/{contact_id}/favorite")
async def toggle_contact_favorite(
    organization_slug: str,
    contact_id: str,
    use_case: ToggleContactFavoriteUseCase = Depends(get_toggle_contact_favorite_use_case),
) -> ContactSummaryResponse:
    contact = await use_case.execute(ContactId.from_string(contact_id))
    return ContactSummaryResponse.from_domain(contact)


@router.get("/{contact_id}/notes")
async def list_contact_notes(
    organization_slug: str,
    contact_id: str,
    use_case: ListContactNotesUseCase = Depends(get_list_contact_notes_use_case),
) -> list[ContactNoteResponse]:
    notes = await use_case.execute(ContactId.from_string(contact_id))
    return [ContactNoteResponse.from_domain(n) for n in notes]


@router.post("/{contact_id}/notes")
async def add_contact_note(
    organization_slug: str,
    contact_id: str,
    body: AddContactNoteRequest,
    use_case: AddContactNoteUseCase = Depends(get_add_contact_note_use_case),
) -> ContactNoteResponse:
    note = await use_case.execute(
        ContactId.from_string(contact_id),
        InternalUserId.from_string(body.advisor_id),
        body.content,
    )
    return ContactNoteResponse.from_domain(note)
