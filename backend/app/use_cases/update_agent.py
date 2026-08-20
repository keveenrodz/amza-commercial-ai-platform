from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.agent import Agent
from core.exceptions.domain import NoActiveAgentError, OrganizationSlugNotFoundError
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class UpdateAgentUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        organization_slug: str,
        system_prompt: str,
        escalation_rules: str,
        model: str,
    ) -> Agent:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)

            agent = await uow.agents.get_default_by_organization(organization.id)
            if agent is None:
                raise NoActiveAgentError(organization.id)

            agent.system_prompt = system_prompt
            agent.escalation_rules = escalation_rules
            agent.model = model
            agent.updated_at = datetime.now(tz=UTC)
            await uow.agents.save(agent)
            await uow.commit()

        return agent
