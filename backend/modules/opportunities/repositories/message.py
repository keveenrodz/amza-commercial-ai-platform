from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.message import Message
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from core.value_objects.identifiers import ConversationId, MessageId, OpportunityId
from modules.opportunities.models.conversation import ConversationModel
from modules.opportunities.models.message import MessageModel


def _to_entity(model: MessageModel) -> Message:
    return Message(
        id=MessageId(value=model.id),
        conversation_id=ConversationId(value=model.conversation_id),
        sender_role=MessageRole(model.sender_role),
        content_type=MessageContentType(model.content_type),
        content=model.content,
        channel_type=ChannelType(model.channel_type),
        sent_at=model.sent_at,
        provider_message_id=model.provider_message_id,
        metadata=model.extra_metadata if model.extra_metadata is not None else {},
    )


def _from_entity(entity: Message) -> MessageModel:
    return MessageModel(
        id=entity.id.value,
        conversation_id=entity.conversation_id.value,
        sender_role=entity.sender_role.value,
        content_type=entity.content_type.value,
        content=entity.content,
        channel_type=entity.channel_type.value,
        sent_at=entity.sent_at,
        provider_message_id=entity.provider_message_id,
        extra_metadata=entity.metadata if entity.metadata else None,
    )


class SQLAlchemyMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: MessageId) -> Message | None:
        result = await self._session.execute(
            select(MessageModel).where(MessageModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_by_conversation(
        self,
        conversation_id: ConversationId,
        limit: int,
    ) -> list[Message]:
        result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id.value)
            .order_by(MessageModel.sent_at.desc())
            .limit(limit)
        )
        return [_to_entity(m) for m in reversed(result.scalars().all())]

    async def list_since(
        self,
        conversation_id: ConversationId,
        after: datetime | None,
    ) -> list[Message]:
        # after es exclusivo: sent_at > after, nunca >= (evita re-resumir el mensaje de corte)
        stmt = select(MessageModel).where(MessageModel.conversation_id == conversation_id.value)
        if after is not None:
            stmt = stmt.where(MessageModel.sent_at > after)
        result = await self._session.execute(stmt.order_by(MessageModel.sent_at.asc()))
        return [_to_entity(m) for m in result.scalars().all()]

    async def count_since(
        self,
        conversation_id: ConversationId,
        after: datetime | None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(MessageModel)
            .where(MessageModel.conversation_id == conversation_id.value)
        )
        if after is not None:
            stmt = stmt.where(MessageModel.sent_at > after)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_latest_by_opportunity_ids(
        self,
        opportunity_ids: list[OpportunityId],
    ) -> dict[OpportunityId, Message]:
        if not opportunity_ids:
            return {}
        ids = [o.value for o in opportunity_ids]

        # "Greatest-n-per-group" vía subquery correlacionada (max(sent_at) por conversación) en
        # vez de ROW_NUMBER() -- más simple de leer, y el volumen por request (una página de
        # oportunidades) no justifica la sintaxis de window function.
        latest_per_conversation = (
            select(
                MessageModel.conversation_id,
                func.max(MessageModel.sent_at).label("max_sent_at"),
            )
            .join(ConversationModel, ConversationModel.id == MessageModel.conversation_id)
            .where(ConversationModel.opportunity_id.in_(ids))
            .group_by(MessageModel.conversation_id)
            .subquery()
        )

        result = await self._session.execute(
            select(MessageModel, ConversationModel.opportunity_id)
            .join(ConversationModel, ConversationModel.id == MessageModel.conversation_id)
            .join(
                latest_per_conversation,
                and_(
                    MessageModel.conversation_id == latest_per_conversation.c.conversation_id,
                    MessageModel.sent_at == latest_per_conversation.c.max_sent_at,
                ),
            )
        )
        out: dict[OpportunityId, Message] = {}
        for message_model, opportunity_id_value in result.all():
            # Si dos mensajes empatan en sent_at exacto (raro), el último gana -- aceptable para
            # una vista previa, no una fuente de verdad transaccional.
            out[OpportunityId(value=opportunity_id_value)] = _to_entity(message_model)
        return out

    async def exists_by_provider_message_id(
        self,
        channel_type: ChannelType,
        provider_message_id: str,
    ) -> bool:
        result = await self._session.execute(
            select(MessageModel.id).where(
                MessageModel.channel_type == channel_type.value,
                MessageModel.provider_message_id == provider_message_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def save(self, message: Message) -> None:
        await self._session.merge(_from_entity(message))
