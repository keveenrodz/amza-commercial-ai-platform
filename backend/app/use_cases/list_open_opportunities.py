from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.contact import Contact
from core.entities.follow_up import FollowUp
from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.enums.message import MessageContentType
from core.exceptions.domain import OrganizationSlugNotFoundError
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

_MAX_PREVIEW_LENGTH = 60

_NON_TEXT_LABELS: dict[MessageContentType, str] = {
    MessageContentType.IMAGE: "📷 Imagen",
    MessageContentType.VIDEO: "🎥 Video",
    MessageContentType.DOCUMENT: "📄 Documento",
    MessageContentType.AUDIO: "🎤 Audio",
    MessageContentType.LOCATION: "📍 Ubicación",
}


def build_message_preview(message: Message) -> str:
    if message.content_type != MessageContentType.TEXT:
        return _NON_TEXT_LABELS.get(message.content_type, "Adjunto")
    text = message.content.strip()
    if len(text) <= _MAX_PREVIEW_LENGTH:
        return text
    return text[:_MAX_PREVIEW_LENGTH].rstrip() + "…"


@dataclass(frozen=True)
class OpenOpportunity:
    opportunity: Opportunity
    contact: Contact
    follow_up: FollowUp | None
    last_message_preview: str | None


class ListOpenOpportunitiesUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, organization_slug: str) -> list[OpenOpportunity]:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)

            opportunities = await uow.opportunities.list_open_by_organization(organization.id)

            contacts_by_id = {
                c.id: c
                for c in await uow.contacts.list_by_ids([o.contact_id for o in opportunities])
            }
            follow_ups_by_opportunity = {
                f.opportunity_id: f
                for f in await uow.follow_ups.list_active_by_opportunity_ids(
                    [o.id for o in opportunities]
                )
            }
            latest_message_by_opportunity = await uow.messages.get_latest_by_opportunity_ids(
                [o.id for o in opportunities]
            )

            return [
                OpenOpportunity(
                    opportunity=o,
                    contact=contacts_by_id[o.contact_id],
                    follow_up=follow_ups_by_opportunity.get(o.id),
                    last_message_preview=(
                        build_message_preview(latest_message_by_opportunity[o.id])
                        if o.id in latest_message_by_opportunity
                        else None
                    ),
                )
                for o in opportunities
            ]
