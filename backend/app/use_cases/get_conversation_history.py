from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.conversation import Conversation
from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.exceptions.domain import OpportunityNotFoundError
from core.value_objects.identifiers import OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

_DEFAULT_MESSAGE_LIMIT = 50


@dataclass(frozen=True)
class ConversationHistory:
    opportunity: Opportunity
    conversation: Conversation | None
    messages: list[Message]


class GetConversationHistoryUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        opportunity_id: OpportunityId,
        message_limit: int = _DEFAULT_MESSAGE_LIMIT,
    ) -> ConversationHistory:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            conversation = await uow.conversations.get_by_opportunity(opportunity_id)

            messages: list[Message] = []
            if conversation is not None:
                messages = await uow.messages.list_by_conversation(
                    conversation.id,
                    limit=message_limit,
                )

            return ConversationHistory(
                opportunity=opportunity,
                conversation=conversation,
                messages=messages,
            )
