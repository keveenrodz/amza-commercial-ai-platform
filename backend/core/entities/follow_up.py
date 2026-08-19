from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from core.value_objects.identifiers import FollowUpId, InternalUserId, OpportunityId


@dataclass
class FollowUp:
    id: FollowUpId
    opportunity_id: OpportunityId
    due_at: datetime
    reason: str
    created_by: InternalUserId
    created_at: datetime
    resolved_at: datetime | None = None

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    def resolve(self) -> None:
        self.resolved_at = datetime.now(tz=UTC)
