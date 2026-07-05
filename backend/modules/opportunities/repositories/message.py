from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.message import Message
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from core.value_objects.identifiers import ConversationId, MessageId
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

    async def save(self, message: Message) -> None:
        await self._session.merge(_from_entity(message))
