from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.enums.channel import ChannelType
from core.enums.opportunity import AttentionMode, OpportunityStatus
from core.value_objects.identifiers import (
    ContactId,
    ConversationId,
    InternalUserId,
    MessageId,
    OpportunityId,
)


@dataclass(frozen=True)
class OpportunityCreated:
    opportunity_id: OpportunityId
    contact_id: ContactId
    channel_type: ChannelType
    occurred_at: datetime


@dataclass(frozen=True)
class OpportunityStatusChanged:
    opportunity_id: OpportunityId
    previous_status: OpportunityStatus
    new_status: OpportunityStatus
    occurred_at: datetime


@dataclass(frozen=True)
class AttentionModeChanged:
    opportunity_id: OpportunityId
    previous_mode: AttentionMode
    new_mode: AttentionMode
    assigned_advisor_id: InternalUserId | None
    occurred_at: datetime


@dataclass(frozen=True)
class MessageReceived:
    message_id: MessageId
    conversation_id: ConversationId
    opportunity_id: OpportunityId
    occurred_at: datetime


@dataclass(frozen=True)
class MessageSent:
    message_id: MessageId
    conversation_id: ConversationId
    opportunity_id: OpportunityId
    occurred_at: datetime


@dataclass(frozen=True)
class ConversationStarted:
    conversation_id: ConversationId
    opportunity_id: OpportunityId
    occurred_at: datetime
