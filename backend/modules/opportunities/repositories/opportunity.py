from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.opportunity import Opportunity
from core.enums.channel import ChannelType
from core.enums.opportunity import AttentionMode, OpportunityStatus
from core.value_objects.identifiers import (
    AgentId,
    ContactId,
    InternalUserId,
    OpportunityId,
    OrganizationId,
)
from modules.opportunities.models.opportunity import OpportunityModel

_TERMINAL_STATUSES = (
    OpportunityStatus.WON.value,
    OpportunityStatus.LOST.value,
    OpportunityStatus.CLOSED.value,
)


def _to_entity(model: OpportunityModel) -> Opportunity:
    return Opportunity(
        id=OpportunityId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        contact_id=ContactId(value=model.contact_id),
        agent_id=AgentId(value=model.agent_id),
        attention_mode=AttentionMode(model.attention_mode),
        assigned_advisor_id=(
            InternalUserId(value=model.assigned_advisor_id)
            if model.assigned_advisor_id
            else None
        ),
        status=OpportunityStatus(model.status),
        channel_type=ChannelType(model.channel_type),
        started_at=model.started_at,
        last_activity_at=model.last_activity_at,
        closed_at=model.closed_at,
    )


def _from_entity(entity: Opportunity) -> OpportunityModel:
    return OpportunityModel(
        id=entity.id.value,
        organization_id=entity.organization_id.value,
        contact_id=entity.contact_id.value,
        agent_id=entity.agent_id.value,
        assigned_advisor_id=(
            entity.assigned_advisor_id.value if entity.assigned_advisor_id else None
        ),
        attention_mode=entity.attention_mode.value,
        status=entity.status.value,
        channel_type=entity.channel_type.value,
        started_at=entity.started_at,
        last_activity_at=entity.last_activity_at,
        closed_at=entity.closed_at,
    )


class SQLAlchemyOpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: OpportunityId) -> Opportunity | None:
        result = await self._session.execute(
            select(OpportunityModel).where(OpportunityModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_active_by_contact(
        self,
        contact_id: ContactId,
        channel_type: ChannelType,
    ) -> Opportunity | None:
        result = await self._session.execute(
            select(OpportunityModel)
            .where(
                OpportunityModel.contact_id == contact_id.value,
                OpportunityModel.channel_type == channel_type.value,
                ~OpportunityModel.status.in_(_TERMINAL_STATUSES),
            )
            .order_by(OpportunityModel.started_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, opportunity: Opportunity) -> None:
        await self._session.merge(_from_entity(opportunity))

    async def list_open_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> list[Opportunity]:
        result = await self._session.execute(
            select(OpportunityModel)
            .where(
                OpportunityModel.organization_id == organization_id.value,
                ~OpportunityModel.status.in_(_TERMINAL_STATUSES),
            )
            .order_by(OpportunityModel.last_activity_at.desc())
        )
        return [_to_entity(m) for m in result.scalars().all()]
