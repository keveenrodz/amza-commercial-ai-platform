from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.enums.message import MessageContentType, MessageRole
from core.value_objects.identifiers import ConversationId, MessageId


@dataclass
class Message:
    id: MessageId
    conversation_id: ConversationId
    role: MessageRole
    content_type: MessageContentType
    content: str
    created_at: datetime
    provider_message_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
