from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dto.internal_user import (
    CreateInternalUserRequest,
    InternalUserResponse,
    UpdateInternalUserRequest,
)
from app.dependencies import (
    get_activate_internal_user_use_case,
    get_create_internal_user_use_case,
    get_deactivate_internal_user_use_case,
    get_list_internal_users_use_case,
    get_update_internal_user_use_case,
)
from app.security import require_role
from app.use_cases.activate_internal_user import ActivateInternalUserUseCase
from app.use_cases.create_internal_user import CreateInternalUserUseCase
from app.use_cases.deactivate_internal_user import DeactivateInternalUserUseCase
from app.use_cases.list_internal_users import ListInternalUsersUseCase
from app.use_cases.update_internal_user import UpdateInternalUserUseCase
from core.entities.internal_user import InternalUser
from core.enums.user import InternalUserRole
from core.value_objects.identifiers import InternalUserId

router = APIRouter(
    prefix="/organizations/{organization_slug}/users",
    tags=["internal-users"],
    dependencies=[Depends(require_role(InternalUserRole.ADMINISTRATOR))],
)


@router.get("")
async def list_internal_users(
    organization_slug: str,
    use_case: ListInternalUsersUseCase = Depends(get_list_internal_users_use_case),
) -> list[InternalUserResponse]:
    users = await use_case.execute(organization_slug)
    return [InternalUserResponse.from_domain(u) for u in users]


@router.post("", status_code=201)
async def create_internal_user(
    organization_slug: str,
    body: CreateInternalUserRequest,
    current_user: InternalUser = Depends(require_role(InternalUserRole.ADMINISTRATOR)),
    use_case: CreateInternalUserUseCase = Depends(get_create_internal_user_use_case),
) -> InternalUserResponse:
    # current_user aquí (no del body) es quién queda registrado como created_by -- misma razón
    # que en deactivate: dejar que el frontend lo declarara permitiría falsificar la auditoría.
    user = await use_case.execute(
        organization_slug, body.full_name, body.email, InternalUserRole(body.role),
        actor_id=current_user.id,
    )
    return InternalUserResponse.from_domain(user)


@router.put("/{user_id}")
async def update_internal_user(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance en spec 007
    user_id: str,
    body: UpdateInternalUserRequest,
    current_user: InternalUser = Depends(require_role(InternalUserRole.ADMINISTRATOR)),
    use_case: UpdateInternalUserUseCase = Depends(get_update_internal_user_use_case),
) -> InternalUserResponse:
    # current_user real (no del body) para decidir si el cambio de email está permitido -- mismo
    # motivo que en create/deactivate.
    user = await use_case.execute(
        current_user.id,
        InternalUserId.from_string(user_id),
        body.full_name,
        body.email,
        InternalUserRole(body.role),
    )
    return InternalUserResponse.from_domain(user)


@router.post("/{user_id}/deactivate")
async def deactivate_internal_user(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance en spec 007
    user_id: str,
    current_user: InternalUser = Depends(require_role(InternalUserRole.ADMINISTRATOR)),
    use_case: DeactivateInternalUserUseCase = Depends(get_deactivate_internal_user_use_case),
) -> InternalUserResponse:
    # current_user aquí (no del body) es lo que realmente importa para actor_id -- ver spec 014
    # sección 5: dejar que el frontend declare quién actúa permitiría que cualquier administrador
    # se hiciera pasar por el principal. La dependencia del router solo gatea el rol.
    user = await use_case.execute(current_user.id, InternalUserId.from_string(user_id))
    return InternalUserResponse.from_domain(user)


@router.post("/{user_id}/activate")
async def activate_internal_user(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance en spec 007
    user_id: str,
    use_case: ActivateInternalUserUseCase = Depends(get_activate_internal_user_use_case),
) -> InternalUserResponse:
    user = await use_case.execute(InternalUserId.from_string(user_id))
    return InternalUserResponse.from_domain(user)
