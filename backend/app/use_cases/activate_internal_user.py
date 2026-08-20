from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.internal_user import InternalUser
from core.enums.user import InternalUserStatus
from core.exceptions.domain import InternalUserNotFoundError
from core.value_objects.identifiers import InternalUserId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class ActivateInternalUserUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, target_id: InternalUserId) -> InternalUser:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            target = await uow.internal_users.get_by_id(target_id)
            if target is None:
                raise InternalUserNotFoundError(target_id)

            # Reactivar no tiene el riesgo que la regla 3 (solo el principal desactiva admins)
            # busca evitar -- nadie pierde acceso al reactivar a alguien, así que sin chequeos
            # adicionales de quién lo hace.
            target.status = InternalUserStatus.ACTIVE
            target.updated_at = datetime.now(tz=UTC)
            await uow.internal_users.save(target)
            await uow.commit()
        return target
