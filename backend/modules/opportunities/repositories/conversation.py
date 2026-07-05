from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.conversation import Conversation
from core.value_objects.identifiers import ConversationId, OpportunityId
from modules.opportunities.models.conversation import ConversationModel


def _to_entity(model: ConversationModel) -> Conversation:
    return Conversation(
        id=ConversationId(value=model.id),
        opportunity_id=OpportunityId(value=model.opportunity_id),
        started_at=model.started_at,
        ended_at=model.ended_at,
    )


def _from_entity(entity: Conversation) -> ConversationModel:
    return ConversationModel(
        id=entity.id.value,
        opportunity_id=entity.opportunity_id.value,
        started_at=entity.started_at,
        ended_at=entity.ended_at,
    )


class SQLAlchemyConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: ConversationId) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationModel).where(ConversationModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_opportunity(
        self,
        opportunity_id: OpportunityId,
    ) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationModel).where(
                ConversationModel.opportunity_id == opportunity_id.value
            )
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, conversation: Conversation) -> None:
        await self._session.merge(_from_entity(conversation))
