from __future__ import annotations

from pydantic import BaseModel

from core.entities.internal_user import InternalUser


class CurrentUserResponse(BaseModel):
    id: str
    organization_id: str
    full_name: str
    email: str
    role: str
    status: str

    @classmethod
    def from_domain(cls, user: InternalUser) -> CurrentUserResponse:
        return cls(
            id=str(user.id),
            organization_id=str(user.organization_id),
            full_name=user.full_name,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
        )
