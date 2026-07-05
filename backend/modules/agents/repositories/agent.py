from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.agent import Agent
from core.enums.agent import AgentStatus
from core.value_objects.identifiers import AgentId, OrganizationId
from modules.agents.models.agent import AgentModel


def _to_entity(model: AgentModel) -> Agent:
    return Agent(
        id=AgentId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        name=model.name,
        system_prompt=model.system_prompt,
        model=model.model,
        status=AgentStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _from_entity(entity: Agent) -> AgentModel:
    return AgentModel(
        id=entity.id.value,
        organization_id=entity.organization_id.value,
        name=entity.name,
        system_prompt=entity.system_prompt,
        model=entity.model,
        status=entity.status.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class SQLAlchemyAgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: AgentId) -> Agent | None:
        result = await self._session.execute(
            select(AgentModel).where(AgentModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_default_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> Agent | None:
        result = await self._session.execute(
            select(AgentModel)
            .where(
                AgentModel.organization_id == organization_id.value,
                AgentModel.status == AgentStatus.ACTIVE.value,
            )
            .order_by(AgentModel.created_at.asc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, agent: Agent) -> None:
        await self._session.merge(_from_entity(agent))
