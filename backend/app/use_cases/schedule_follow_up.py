from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.follow_up import FollowUp
from core.exceptions.domain import FollowUpAlreadyScheduledError, OpportunityNotFoundError
from core.value_objects.identifiers import FollowUpId, InternalUserId, OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class ScheduleFollowUpUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        opportunity_id: OpportunityId,
        advisor_id: InternalUserId,
        due_at: datetime,
        reason: str,
    ) -> FollowUp:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            existing = await uow.follow_ups.get_active_by_opportunity(opportunity_id)
            if existing is not None:
                raise FollowUpAlreadyScheduledError(opportunity_id)

            follow_up = FollowUp(
                id=FollowUpId.generate(),
                opportunity_id=opportunity_id,
                due_at=due_at,
                reason=reason,
                created_by=advisor_id,
                created_at=datetime.now(tz=UTC),
            )
            await uow.follow_ups.save(follow_up)
            await uow.commit()
        return follow_up
