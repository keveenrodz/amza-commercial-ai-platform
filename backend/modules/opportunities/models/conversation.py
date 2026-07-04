from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class ConversationModel(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        sa.Index("ix_conversations_opportunity_id", "opportunity_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(native_uuid=False), nullable=False, unique=True
    )
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
