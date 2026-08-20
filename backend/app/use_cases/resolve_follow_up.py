from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.system_message import record_system_message
from core.entities.follow_up import FollowUp
from core.exceptions.domain import FollowUpNotFoundError, OpportunityNotFoundError
from core.value_objects.identifiers import InternalUserId, OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class ResolveFollowUpUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, opportunity_id: OpportunityId, advisor_id: InternalUserId) -> FollowUp:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            follow_up = await uow.follow_ups.get_active_by_opportunity(opportunity_id)
            if follow_up is None:
                raise FollowUpNotFoundError(opportunity_id)

            follow_up.resolve()
            await uow.follow_ups.save(follow_up)

            advisor = await uow.internal_users.get_by_id(advisor_id)
            advisor_name = advisor.full_name if advisor else "Un asesor"
            await record_system_message(
                uow,
                opportunity,
                f"{advisor_name} marcó el seguimiento de este cliente como resuelto.",
            )

            await uow.commit()
        return follow_up
