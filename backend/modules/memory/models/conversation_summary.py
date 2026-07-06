from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class ConversationSummaryModel(Base):
    __tablename__ = "conversation_summaries"
    __table_args__ = (
        sa.Index(
            "ix_conversation_summaries_conversation_id_version",
            "conversation_id",
            "version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    summary: Mapped[str] = mapped_column(sa.Text, nullable=False)
    up_to_sent_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
