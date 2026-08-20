from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.internal_user import InternalUser
from core.enums.user import InternalUserRole, InternalUserStatus
from core.exceptions.domain import (
    CannotRemoveSelfError,
    InternalUserNotFoundError,
    OnlyPrimaryAdminCanDeactivateAdminsError,
)
from core.value_objects.identifiers import InternalUserId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class DeactivateInternalUserUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, actor_id: InternalUserId, target_id: InternalUserId) -> InternalUser:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            target = await uow.internal_users.get_by_id(target_id)
            if target is None:
                raise InternalUserNotFoundError(target_id)

            if target.id == actor_id:
                raise CannotRemoveSelfError(actor_id)

            if target.role == InternalUserRole.ADMINISTRATOR:
                actor = await uow.internal_users.get_by_id(actor_id)
                # invariante: actor viene de get_current_user, ya autenticado
                assert actor is not None
                if not actor.is_primary:
                    raise OnlyPrimaryAdminCanDeactivateAdminsError(target_id)

            target.status = InternalUserStatus.INACTIVE
            target.updated_at = datetime.now(tz=UTC)
            await uow.internal_users.save(target)
            await uow.commit()
        return target
