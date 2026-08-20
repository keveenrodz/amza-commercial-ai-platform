from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.internal_user import InternalUser
from core.enums.user import InternalUserRole
from core.exceptions.domain import (
    CannotDemotePrimaryAdminError,
    InternalUserEmailAlreadyExistsError,
    InternalUserNotFoundError,
    OnlyPrimaryAdminCanEditEmailError,
)
from core.value_objects.identifiers import InternalUserId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class UpdateInternalUserUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        actor_id: InternalUserId,
        target_id: InternalUserId,
        full_name: str,
        email: str,
        role: InternalUserRole,
    ) -> InternalUser:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            target = await uow.internal_users.get_by_id(target_id)
            if target is None:
                raise InternalUserNotFoundError(target_id)

            email_changed = email.lower() != target.email
            if email_changed:
                # El email solo lo puede editar el administrador principal, sin excepción ni
                # siquiera para su propio registro -- a diferencia del resto de este caso de uso
                # (cualquier admin puede editar nombre/rol), este campo es la identidad de login
                # vía Google; cambiarlo sin control real sería un vector real de secuestro de
                # cuenta.
                actor = await uow.internal_users.get_by_id(actor_id)
                if actor is None or not actor.is_primary:
                    raise OnlyPrimaryAdminCanEditEmailError(target_id)

                existing = await uow.internal_users.get_by_email(email)
                if existing is not None and existing.id != target_id:
                    raise InternalUserEmailAlreadyExistsError(email)

            # El principal siempre debe seguir siendo Administrator -- si se le quita el rol acá
            # el índice único de la migración 0005 dejaría de proteger nada, porque ya no
            # quedaría ningún registro marcado is_primary=True que lo represente correctamente.
            if target.is_primary and role != InternalUserRole.ADMINISTRATOR:
                raise CannotDemotePrimaryAdminError(target_id)

            target.full_name = full_name
            target.email = email.lower()
            target.role = role
            target.updated_at = datetime.now(tz=UTC)
            await uow.internal_users.save(target)
            await uow.commit()
        return target
