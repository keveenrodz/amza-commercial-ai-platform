from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.follow_up import FollowUp
from core.value_objects.identifiers import FollowUpId, InternalUserId, OpportunityId
from modules.opportunities.models.follow_up import FollowUpModel


def _to_entity(model: FollowUpModel) -> FollowUp:
    return FollowUp(
        id=FollowUpId(value=model.id),
        opportunity_id=OpportunityId(value=model.opportunity_id),
        due_at=model.due_at,
        reason=model.reason,
        created_by=InternalUserId(value=model.created_by),
        created_at=model.created_at,
        resolved_at=model.resolved_at,
    )


def _from_entity(entity: FollowUp) -> FollowUpModel:
    return FollowUpModel(
        id=entity.id.value,
        opportunity_id=entity.opportunity_id.value,
        due_at=entity.due_at,
        reason=entity.reason,
        created_by=entity.created_by.value,
        created_at=entity.created_at,
        resolved_at=entity.resolved_at,
    )


class SQLAlchemyFollowUpRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_by_opportunity(
        self,
        opportunity_id: OpportunityId,
    ) -> FollowUp | None:
        result = await self._session.execute(
            select(FollowUpModel).where(
                FollowUpModel.opportunity_id == opportunity_id.value,
                FollowUpModel.resolved_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_active_by_opportunity_ids(
        self,
        opportunity_ids: list[OpportunityId],
    ) -> list[FollowUp]:
        if not opportunity_ids:
            return []
        result = await self._session.execute(
            select(FollowUpModel).where(
                FollowUpModel.opportunity_id.in_([i.value for i in opportunity_ids]),
                FollowUpModel.resolved_at.is_(None),
            )
        )
        return [_to_entity(model) for model in result.scalars()]

    async def save(self, follow_up: FollowUp) -> None:
        await self._session.merge(_from_entity(follow_up))
