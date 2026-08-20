from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from core.entities.internal_user import InternalUser


class InternalUserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    status: str
    is_primary: bool

    @classmethod
    def from_domain(cls, user: InternalUser) -> InternalUserResponse:
        return cls(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            is_primary=user.is_primary,
        )


class CreateInternalUserRequest(BaseModel):
    full_name: str
    email: str
    # Literal, no str -- un valor inválido lo rechaza Pydantic con 422 directo, en vez de que
    # InternalUserRole(role) lance un ValueError sin capturar dentro del caso de uso.
    role: Literal["advisor", "administrator"]
