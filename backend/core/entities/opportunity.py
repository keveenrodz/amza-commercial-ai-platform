from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from core.enums.channel import ChannelType
from core.enums.opportunity import AttentionMode, OpportunityStatus
from core.exceptions.domain import InvalidStatusTransitionError, OpportunityAlreadyClosedError
from core.value_objects.identifiers import (
    AgentId,
    ContactId,
    InternalUserId,
    OpportunityId,
    OrganizationId,
)

_ALLOWED_TRANSITIONS: dict[OpportunityStatus, frozenset[OpportunityStatus]] = {
    OpportunityStatus.NEW: frozenset({
        OpportunityStatus.QUALIFIED,
        OpportunityStatus.LOST,
        OpportunityStatus.CLOSED,
    }),
    OpportunityStatus.QUALIFIED: frozenset({
        OpportunityStatus.WAITING_FOR_ADVISOR,
        OpportunityStatus.QUOTATION_PENDING,
        OpportunityStatus.LOST,
        OpportunityStatus.CLOSED,
    }),
    OpportunityStatus.WAITING_FOR_ADVISOR: frozenset({
        OpportunityStatus.QUOTATION_PENDING,
        OpportunityStatus.QUALIFIED,
        OpportunityStatus.LOST,
        OpportunityStatus.CLOSED,
    }),
    OpportunityStatus.QUOTATION_PENDING: frozenset({
        OpportunityStatus.QUOTATION_SENT,
        OpportunityStatus.LOST,
        OpportunityStatus.CLOSED,
    }),
    OpportunityStatus.QUOTATION_SENT: frozenset({
        OpportunityStatus.FOLLOW_UP_PENDING,
        OpportunityStatus.WON,
        OpportunityStatus.LOST,
        OpportunityStatus.CLOSED,
    }),
    OpportunityStatus.FOLLOW_UP_PENDING: frozenset({
        OpportunityStatus.QUOTATION_SENT,
        OpportunityStatus.WON,
        OpportunityStatus.LOST,
        OpportunityStatus.CLOSED,
    }),
    OpportunityStatus.WON: frozenset({
        OpportunityStatus.CLOSED,
    }),
    OpportunityStatus.LOST: frozenset({
        OpportunityStatus.CLOSED,
    }),
    OpportunityStatus.CLOSED: frozenset(),
}


@dataclass
class Opportunity:
    id: OpportunityId
    organization_id: OrganizationId
    contact_id: ContactId
    agent_id: AgentId
    attention_mode: AttentionMode
    assigned_advisor_id: InternalUserId | None
    status: OpportunityStatus
    channel_type: ChannelType
    started_at: datetime
    last_activity_at: datetime
    closed_at: datetime | None

    def assign_to_advisor(self, advisor_id: InternalUserId) -> None:
        self.attention_mode = AttentionMode.HUMAN
        self.assigned_advisor_id = advisor_id

    def return_to_ai(self) -> None:
        self.attention_mode = AttentionMode.AI
        self.assigned_advisor_id = None

    def transition_to(self, new_status: OpportunityStatus) -> None:
        if self.status == OpportunityStatus.CLOSED:
            raise OpportunityAlreadyClosedError(self.id)
        allowed = _ALLOWED_TRANSITIONS.get(self.status, frozenset())
        if new_status not in allowed:
            raise InvalidStatusTransitionError(self.status, new_status)
        terminal = {OpportunityStatus.WON, OpportunityStatus.LOST, OpportunityStatus.CLOSED}
        if new_status in terminal and self.closed_at is None:
            self.closed_at = datetime.now(tz=UTC)
        self.status = new_status

    def record_activity(self) -> None:
        self.last_activity_at = datetime.now(tz=UTC)
