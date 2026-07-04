from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.value_objects.identifiers import ConversationId, OpportunityId


@dataclass
class Conversation:
    id: ConversationId
    opportunity_id: OpportunityId
    created_at: datetime
    updated_at: datetime
