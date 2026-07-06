from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class _BaseId:
    value: uuid.UUID

    @classmethod
    def generate(cls) -> Self:
        return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, value: str) -> Self:
        return cls(value=uuid.UUID(value))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class OrganizationId(_BaseId):
    pass


@dataclass(frozen=True)
class ContactId(_BaseId):
    pass


@dataclass(frozen=True)
class InternalUserId(_BaseId):
    pass


@dataclass(frozen=True)
class AgentId(_BaseId):
    pass


@dataclass(frozen=True)
class OpportunityId(_BaseId):
    pass


@dataclass(frozen=True)
class ConversationId(_BaseId):
    pass


@dataclass(frozen=True)
class MessageId(_BaseId):
    pass


@dataclass(frozen=True)
class ConversationSummaryId(_BaseId):
    pass
