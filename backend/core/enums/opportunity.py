from __future__ import annotations

from enum import Enum


class OpportunityStatus(Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    WAITING_FOR_ADVISOR = "waiting_for_advisor"
    QUOTATION_PENDING = "quotation_pending"
    QUOTATION_SENT = "quotation_sent"
    FOLLOW_UP_PENDING = "follow_up_pending"
    WON = "won"
    LOST = "lost"
    CLOSED = "closed"


class AttentionMode(Enum):
    AI = "ai"
    HUMAN = "human"
