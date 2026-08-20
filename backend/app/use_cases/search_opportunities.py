from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.use_cases.list_open_opportunities import OpenOpportunity, build_message_preview
from core.exceptions.domain import OrganizationSlugNotFoundError
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class SearchOpportunitiesUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, organization_slug: str, query: str) -> list[OpenOpportunity]:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)

            opportunities = await uow.opportunities.search_open_by_organization(
                organization.id, query
            )

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
