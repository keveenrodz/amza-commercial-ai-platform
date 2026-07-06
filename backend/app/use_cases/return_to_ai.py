from __future__ import annotations

import contextlib

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.conversation_summarization_service import ConversationSummarizationService
from core.entities.opportunity import Opportunity
from core.enums.opportunity import OpportunityStatus
from core.exceptions.domain import (
    InvalidStatusTransitionError,
    OpportunityNotFoundError,
)
from core.value_objects.identifiers import OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger()


class ReturnToAIUseCase:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        summarization_service: ConversationSummarizationService,
    ) -> None:
        self._session_factory = session_factory
        self._summarization_service = summarization_service

    async def execute(self, opportunity_id: OpportunityId) -> Opportunity:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            opportunity.return_to_ai()

            with contextlib.suppress(InvalidStatusTransitionError):
                opportunity.transition_to(OpportunityStatus.QUALIFIED)

            opportunity.record_activity()
            await uow.opportunities.save(opportunity)
            await uow.commit()

        # Disparo incondicional: el agente de IA que retoma la conversación necesita un resumen
        # actualizado de lo que ocurrió con el asesor humano (ver spec 006, sección 10).
        try:
            async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
                conversation = await uow.conversations.get_by_opportunity(opportunity.id)
                if conversation is not None:
                    await self._summarization_service.execute(conversation.id, uow)
                    await uow.commit()
        except Exception:
            logger.warning("summary.generation_failed", opportunity_id=str(opportunity_id))

        return opportunity
