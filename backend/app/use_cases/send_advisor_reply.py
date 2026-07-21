from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.message import Message
from core.enums.message import MessageContentType, MessageRole
from core.exceptions.domain import (
    ContactNotFoundError,
    OpportunityNotAssignedToAdvisorError,
    OpportunityNotFoundError,
)
from core.interfaces.providers import ChannelProvider
from core.value_objects.identifiers import InternalUserId, MessageId, OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class SendAdvisorReplyUseCase:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        channel_provider: ChannelProvider,
    ) -> None:
        self._session_factory = session_factory
        self._channel_provider = channel_provider

    async def execute(
        self,
        opportunity_id: OpportunityId,
        advisor_id: InternalUserId,
        content: str,
    ) -> Message:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            if opportunity.assigned_advisor_id != advisor_id:
                raise OpportunityNotAssignedToAdvisorError(opportunity_id, advisor_id)

            conversation = await uow.conversations.get_by_opportunity(opportunity.id)
            # invariante: toda Opportunity asignada a un asesor ya tiene una Conversation
            assert conversation is not None

            contact = await uow.contacts.get_by_id(opportunity.contact_id)
            if contact is None:
                raise ContactNotFoundError(opportunity.contact_id)

            message = Message(
                id=MessageId.generate(),
                conversation_id=conversation.id,
                sender_role=MessageRole.ADVISOR,
                content_type=MessageContentType.TEXT,
                content=content,
                channel_type=opportunity.channel_type,
                sent_at=datetime.now(tz=UTC),
            )
            await uow.messages.save(message)

            opportunity.record_activity()
            await uow.opportunities.save(opportunity)

            await self._channel_provider.send(message, contact)

            await uow.commit()

        return message
