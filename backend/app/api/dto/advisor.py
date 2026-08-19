from __future__ import annotations

from pydantic import BaseModel

from core.entities.internal_user import InternalUser


class AdvisorSummaryResponse(BaseModel):
    id: str
    full_name: str

    @classmethod
    def from_domain(cls, advisor: InternalUser) -> AdvisorSummaryResponse:
        return cls(id=str(advisor.id), full_name=advisor.full_name)
