from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.dto.auth import CurrentUserResponse
from app.config import settings
from app.dependencies import get_authenticate_use_case, get_google_auth_provider
from app.security import get_current_user
from app.use_cases.authenticate_with_provider import AuthenticateUseCase
from core.entities.internal_user import InternalUser
from core.interfaces.auth import AuthProvider
from infrastructure.database.session import AsyncSessionFactory
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter(prefix="/auth", tags=["auth"])

# Almacén de state en memoria, de un solo proceso -- ver spec 008 sección 7. Detalle de
# infraestructura: migrar a Redis el día que haga falta no cambia el contrato de AuthProvider ni
# de AuthenticateUseCase, ninguno de los dos sabe cómo se guarda el state.
_STATE_TTL = timedelta(minutes=5)
_pending_states: dict[str, datetime] = {}


def _issue_state() -> str:
    state = secrets.token_urlsafe(32)
    _pending_states[state] = datetime.now(tz=UTC) + _STATE_TTL
    return state


def _consume_state(state: str) -> bool:
    # Se borra al validar, nunca solo se lee -- un state nunca es reutilizable, ni siquiera si
    # alguien repite la misma callback URL.
    expires_at = _pending_states.pop(state, None)
    if expires_at is None:
        return False
    return datetime.now(tz=UTC) < expires_at


@router.get("/google/login")
async def google_login(
    auth_provider: AuthProvider = Depends(get_google_auth_provider),
) -> RedirectResponse:
    state = _issue_state()
    url = auth_provider.get_authorization_url(state, settings.google_redirect_uri)
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    use_case: AuthenticateUseCase = Depends(get_authenticate_use_case),
) -> RedirectResponse:
    if not _consume_state(state):
        raise HTTPException(status_code=401, detail="Invalid or expired state")

    token = await use_case.execute(code, settings.google_redirect_uri)

    # Redirect relativo -- resuelve correcto porque esta respuesta le llega al navegador a través
    # del proxy de Next.js (GOOGLE_REDIRECT_URI apunta a :3000/api/..., no directo a :8000). Si
    # apuntara directo al backend, la cookie que se fija abajo quedaría con el origen del
    # backend, no el del frontend, y nunca viajaría en los fetch("/api/...") reales (spec 009).
    response = RedirectResponse(url="/opportunities", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=not settings.debug,  # Nota: en desarrollo (settings.debug=true) no exige HTTPS;
        # en cualquier despliegue real, settings.debug=false y Secure queda obligatorio.
        samesite="lax",
        max_age=settings.jwt_ttl_hours * 3600,
    )
    return response


@router.get("/me")
async def get_me(user: InternalUser = Depends(get_current_user)) -> CurrentUserResponse:
    async with SQLAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        organization = await uow.organizations.get_by_id(user.organization_id)
    assert organization is not None  # invariante: no existe InternalUser sin Organization válida
    return CurrentUserResponse.from_domain(user, organization.slug)


@router.post("/logout")
async def logout() -> JSONResponse:
    # Nunca un Response(status_code=200) sin body -- apiFetch() del frontend siempre intenta
    # .json() salvo 204, y un 200 con body vacío rompe ese parseo (encontrado en validación
    # manual). Todo endpoint 200 en este API responde JSON, sin casos especiales.
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie("access_token")
    return response
