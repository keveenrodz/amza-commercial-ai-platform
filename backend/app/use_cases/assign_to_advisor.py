from __future__ import annotations

import contextlib

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.conversation_summarization_service import ConversationSummarizationService
from core.entities.opportunity import Opportunity
from core.enums.opportunity import OpportunityStatus
from core.exceptions.domain import (
    InternalUserNotFoundError,
    InvalidStatusTransitionError,
    OpportunityNotFoundError,
)
from core.value_objects.identifiers import InternalUserId, OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger()


class AssignToAdvisorUseCase:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        summarization_service: ConversationSummarizationService,
    ) -> None:
        self._session_factory = session_factory
        self._summarization_service = summarization_service

    async def execute(
        self,
        opportunity_id: OpportunityId,
        advisor_id: InternalUserId,
    ) -> Opportunity:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            advisor = await uow.internal_users.get_by_id(advisor_id)
            if advisor is None:
                raise InternalUserNotFoundError(advisor_id)

            opportunity.assign_to_advisor(advisor_id)

            with contextlib.suppress(InvalidStatusTransitionError):
                opportunity.transition_to(OpportunityStatus.WAITING_FOR_ADVISOR)

            opportunity.record_activity()
            await uow.opportunities.save(opportunity)
            await uow.commit()

        # Disparo incondicional: un asesor humano que toma la conversación necesita un resumen
        # actualizado aunque no se haya cruzado el umbral de tamaño (ver spec 006, sección 10).
        try:
            async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
                conversation = await uow.conversations.get_by_opportunity(opportunity.id)
                if conversation is not None:
                    await self._summarization_service.execute(conversation.id, uow)
                    await uow.commit()
        except Exception:
            logger.warning("summary.generation_failed", opportunity_id=str(opportunity_id))

        return opportunity
