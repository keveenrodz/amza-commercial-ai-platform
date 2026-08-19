from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.api.dto.contact import ContactSummaryResponse
from app.api.dto.follow_up import FollowUpResponse
from app.use_cases.get_conversation_history import ConversationHistory
from app.use_cases.list_open_opportunities import OpenOpportunity
from core.entities.message import Message
from core.entities.opportunity import Opportunity


class AssignAdvisorRequest(BaseModel):
    advisor_id: str


class SendMessageRequest(BaseModel):
    advisor_id: str
    content: str


class SetUnreadRequest(BaseModel):
    unread: bool


class OpportunityResponse(BaseModel):
    id: str
    contact_id: str
    agent_id: str
    assigned_advisor_id: str | None
    attention_mode: str
    status: str
    channel_type: str
    started_at: datetime
    last_activity_at: datetime
    closed_at: datetime | None
    has_unread_messages: bool

    @classmethod
    def from_domain(cls, opportunity: Opportunity) -> OpportunityResponse:
        return cls(
            id=str(opportunity.id),
            contact_id=str(opportunity.contact_id),
            agent_id=str(opportunity.agent_id),
            assigned_advisor_id=(
                str(opportunity.assigned_advisor_id)
                if opportunity.assigned_advisor_id
                else None
            ),
            attention_mode=opportunity.attention_mode.value,
            status=opportunity.status.value,
            channel_type=opportunity.channel_type.value,
            started_at=opportunity.started_at,
            last_activity_at=opportunity.last_activity_at,
            closed_at=opportunity.closed_at,
            has_unread_messages=opportunity.has_unread_messages,
        )


class OpenOpportunityResponse(BaseModel):
    opportunity: OpportunityResponse
    contact: ContactSummaryResponse
    follow_up: FollowUpResponse | None

    @classmethod
    def from_domain(cls, item: OpenOpportunity) -> OpenOpportunityResponse:
        return cls(
            opportunity=OpportunityResponse.from_domain(item.opportunity),
            contact=ContactSummaryResponse.from_domain(item.contact),
            follow_up=FollowUpResponse.from_domain(item.follow_up) if item.follow_up else None,
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
    contact: ContactSummaryResponse
    follow_up: FollowUpResponse | None
    messages: list[MessageResponse]

    @classmethod
    def from_domain(cls, history: ConversationHistory) -> ConversationHistoryResponse:
        return cls(
            opportunity=OpportunityResponse.from_domain(history.opportunity),
            contact=ContactSummaryResponse.from_domain(history.contact),
            follow_up=FollowUpResponse.from_domain(history.follow_up)
            if history.follow_up
            else None,
            messages=[MessageResponse.from_domain(m) for m in history.messages],
        )
