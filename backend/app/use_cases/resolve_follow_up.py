from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.follow_up import FollowUp
from core.exceptions.domain import FollowUpNotFoundError
from core.value_objects.identifiers import OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class ResolveFollowUpUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, opportunity_id: OpportunityId) -> FollowUp:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            follow_up = await uow.follow_ups.get_active_by_opportunity(opportunity_id)
            if follow_up is None:
                raise FollowUpNotFoundError(opportunity_id)

            follow_up.resolve()
            await uow.follow_ups.save(follow_up)
            await uow.commit()
        return follow_up
