from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.use_cases.get_conversation_history import ConversationHistory
from core.entities.message import Message
from core.entities.opportunity import Opportunity


class AssignAdvisorRequest(BaseModel):
    advisor_id: str


class OpportunityResponse(BaseModel):
    id: str
    contact_id: str
    agent_id: str
    attention_mode: str
    status: str
    channel_type: str
    started_at: datetime
    last_activity_at: datetime
    closed_at: datetime | None

    @classmethod
    def from_domain(cls, opportunity: Opportunity) -> OpportunityResponse:
        return cls(
            id=str(opportunity.id),
            contact_id=str(opportunity.contact_id),
            agent_id=str(opportunity.agent_id),
            attention_mode=opportunity.attention_mode.value,
            status=opportunity.status.value,
            channel_type=opportunity.channel_type.value,
            started_at=opportunity.started_at,
            last_activity_at=opportunity.last_activity_at,
            closed_at=opportunity.closed_at,
        )


class MessageResponse(BaseModel):
    id: str
    sender_role: str
    content: str
    content_type: str
    sent_at: datetime

    @classmethod
    def from_domain(cls, message: Message) -> MessageResponse:
        return cls(
            id=str(message.id),
            sender_role=message.sender_role.value,
            content=message.content,
            content_type=message.content_type.value,
            sent_at=message.sent_at,
        )


class ConversationHistoryResponse(BaseModel):
    opportunity: OpportunityResponse
    messages: list[MessageResponse]

    @classmethod
    def from_domain(cls, history: ConversationHistory) -> ConversationHistoryResponse:
        return cls(
            opportunity=OpportunityResponse.from_domain(history.opportunity),
            messages=[MessageResponse.from_domain(m) for m in history.messages],
        )
