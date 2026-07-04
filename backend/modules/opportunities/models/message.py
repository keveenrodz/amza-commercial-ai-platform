from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class MessageModel(Base):
    __tablename__ = "messages"
    __table_args__ = (
        sa.Index("ix_messages_conversation_id", "conversation_id"),
        sa.Index("ix_messages_sent_at", "sent_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    sender_role: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    channel_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", sa.JSON, nullable=True
    )
