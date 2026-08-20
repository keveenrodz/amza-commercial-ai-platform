from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.contact import Contact
from core.entities.conversation import Conversation
from core.entities.follow_up import FollowUp
from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.exceptions.domain import ContactNotFoundError, OpportunityNotFoundError
from core.value_objects.identifiers import OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

_DEFAULT_MESSAGE_LIMIT = 50


@dataclass(frozen=True)
class ConversationHistory:
    opportunity: Opportunity
    conversation: Conversation | None
    contact: Contact
    follow_up: FollowUp | None
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

            contact = await uow.contacts.get_by_id(opportunity.contact_id)
            if contact is None:
                raise ContactNotFoundError(opportunity.contact_id)

            follow_up = await uow.follow_ups.get_active_by_opportunity(opportunity_id)

            conversation = await uow.conversations.get_by_opportunity(opportunity_id)

            messages: list[Message] = []
            if conversation is not None:
                messages = await uow.messages.list_by_conversation(
                    conversation.id,
                    limit=message_limit,
                )

            # Excepción deliberada a "las lecturas no escriben" (spec 013, sección 5): abrir la
            # conversación *es* la señal de "ya lo vi", igual que en cualquier cliente de chat.
            if opportunity.unread_count > 0:
                opportunity.mark_read()
                await uow.opportunities.save(opportunity)
                await uow.commit()

            return ConversationHistory(
                opportunity=opportunity,
                conversation=conversation,
                contact=contact,
                follow_up=follow_up,
                messages=messages,
            )
