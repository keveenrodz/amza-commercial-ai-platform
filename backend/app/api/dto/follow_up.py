from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from core.entities.follow_up import FollowUp


class ScheduleFollowUpRequest(BaseModel):
    advisor_id: str
    due_at: datetime
    reason: str


class FollowUpResponse(BaseModel):
    id: str
    due_at: datetime
    reason: str

    @classmethod
    def from_domain(cls, follow_up: FollowUp) -> FollowUpResponse:
        return cls(id=str(follow_up.id), due_at=follow_up.due_at, reason=follow_up.reason)
