from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.entities.contact import Contact
from core.entities.message import Message
from core.value_objects.identifiers import AgentId


@dataclass(frozen=True)
class ConversationContext:
    summary: str | None
    recent_messages: list[Message]


@dataclass(frozen=True)
class CompletionRequest:
    model: str
    system_prompt: str
    user_prompt: str
    temperature: float = 0.0
    max_tokens: int | None = None
    timeout: float | None = None


class ChannelProvider(Protocol):
    async def send(self, message: Message, contact: Contact) -> None: ...

    async def health(self) -> bool: ...


class AIProvider(Protocol):
    async def generate(self, context: ConversationContext, agent_id: AgentId) -> str: ...

    async def complete(self, request: CompletionRequest) -> str: ...

    async def health(self) -> bool: ...
