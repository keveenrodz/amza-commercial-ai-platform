from __future__ import annotations

import contextlib

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.opportunity import Opportunity
from core.enums.opportunity import OpportunityStatus
from core.exceptions.domain import (
    InvalidStatusTransitionError,
    OpportunityNotFoundError,
)
from core.value_objects.identifiers import OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class ReturnToAIUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

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
            return opportunity
