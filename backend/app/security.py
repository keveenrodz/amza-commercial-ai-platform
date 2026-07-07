from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Cookie, Depends, Header, HTTPException
from jwt.exceptions import InvalidTokenError

from app.config import settings
from core.entities.internal_user import InternalUser
from core.enums.user import InternalUserRole, InternalUserStatus
from core.value_objects.identifiers import InternalUserId
from infrastructure.database.session import AsyncSessionFactory
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


async def verify_telegram_secret(
    x_telegram_bot_api_secret_token: str = Header(default=""),
) -> None:
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


def create_access_token(user: InternalUser) -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_ttl_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


async def get_current_user(
    access_token: str | None = Cookie(default=None),
) -> InternalUser:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_access_token(access_token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc

    user_id = InternalUserId.from_string(payload["sub"])
    async with SQLAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        user = await uow.internal_users.get_by_id(user_id)

    # Consulta a BD en cada request, deliberado -- ver spec 008 sección 4. El costo es
    # insignificante a esta escala, y evitarlo abriría una ventana de hasta jwt_ttl_hours donde
    # un InternalUser desactivado (o con el rol recién cambiado) sigue actuando con privilegios
    # viejos.
    if user is None or user.status != InternalUserStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="Session no longer valid")
    return user


def require_role(*roles: InternalUserRole) -> Callable[..., Any]:
    async def dependency(user: InternalUser = Depends(get_current_user)) -> InternalUser:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return dependency
