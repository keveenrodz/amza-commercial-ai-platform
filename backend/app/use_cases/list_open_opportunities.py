from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.contact import Contact
from core.entities.opportunity import Opportunity
from core.exceptions.domain import OrganizationSlugNotFoundError
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


@dataclass(frozen=True)
class OpenOpportunity:
    opportunity: Opportunity
    contact: Contact


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

            return [
                OpenOpportunity(opportunity=o, contact=contacts_by_id[o.contact_id])
                for o in opportunities
            ]
