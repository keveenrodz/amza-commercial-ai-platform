from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.value_objects.identifiers import ConversationId, ConversationSummaryId


@dataclass
class ConversationSummary:
    id: ConversationSummaryId
    conversation_id: ConversationId
    summary: str
    up_to_sent_at: datetime
    version: int
    created_at: datetime
