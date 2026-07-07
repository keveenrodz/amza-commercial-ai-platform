from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.security import create_access_token
from core.enums.user import InternalUserStatus
from core.exceptions.domain import AccessDeniedError
from core.interfaces.auth import AuthProvider
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger()


class AuthenticateUseCase:
    """Genérico sobre AuthProvider -- la misma clase sirve para Google y, más adelante,
    Microsoft; el router decide qué AuthProvider inyectar según la ruta, este caso de uso no
    sabe ni le importa cuál es."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        auth_provider: AuthProvider,
    ) -> None:
        self._session_factory = session_factory
        self._auth_provider = auth_provider

    async def execute(self, code: str, redirect_uri: str) -> str:
        identity = await self._auth_provider.exchange_code(code, redirect_uri)

        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            user = await uow.internal_users.get_by_email(identity.email)

        if user is None or user.status != InternalUserStatus.ACTIVE:
            # Ver Principio Arquitectónico en spec 008 -- este es el único control de acceso
            # real. Log de auditoría, no un simple warning: es un intento de acceso, no un error
            # técnico.
            logger.warning(
                "auth.access_denied",
                email=identity.email,
                provider=identity.provider,
            )
            raise AccessDeniedError(identity.email)

        logger.info(
            "auth.login_success",
            internal_user_id=str(user.id),
            email=user.email,
            provider=identity.provider,
            organization_id=str(user.organization_id),
        )

        return create_access_token(user)
