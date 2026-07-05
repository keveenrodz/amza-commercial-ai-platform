from __future__ import annotations

import contextlib

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.opportunity import Opportunity
from core.enums.opportunity import OpportunityStatus
from core.exceptions.domain import (
    InternalUserNotFoundError,
    InvalidStatusTransitionError,
    OpportunityNotFoundError,
)
from core.value_objects.identifiers import InternalUserId, OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class AssignToAdvisorUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

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
            return opportunity
