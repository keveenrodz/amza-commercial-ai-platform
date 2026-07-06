from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.conversation_summary import ConversationSummary
from core.value_objects.identifiers import ConversationId, ConversationSummaryId
from modules.memory.models.conversation_summary import ConversationSummaryModel


def _to_entity(model: ConversationSummaryModel) -> ConversationSummary:
    return ConversationSummary(
        id=ConversationSummaryId(value=model.id),
        conversation_id=ConversationId(value=model.conversation_id),
        summary=model.summary,
        up_to_sent_at=model.up_to_sent_at,
        version=model.version,
        created_at=model.created_at,
    )


def _from_entity(entity: ConversationSummary) -> ConversationSummaryModel:
    return ConversationSummaryModel(
        id=entity.id.value,
        conversation_id=entity.conversation_id.value,
        summary=entity.summary,
        up_to_sent_at=entity.up_to_sent_at,
        version=entity.version,
        created_at=entity.created_at,
    )


class SQLAlchemyConversationSummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest(
        self,
        conversation_id: ConversationId,
    ) -> ConversationSummary | None:
        result = await self._session.execute(
            select(ConversationSummaryModel)
            .where(ConversationSummaryModel.conversation_id == conversation_id.value)
            .order_by(ConversationSummaryModel.version.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, summary: ConversationSummary) -> None:
        # append-only: nunca se actualiza un summary existente, cada llamada crea una fila nueva.
        self._session.add(_from_entity(summary))
