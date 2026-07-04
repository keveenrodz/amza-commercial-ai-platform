from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class AgentModel(Base):
    __tablename__ = "agents"
    __table_args__ = (
        sa.Index("ix_agents_organization_id", "organization_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    system_prompt: Mapped[str] = mapped_column(sa.Text, nullable=False)
    model: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
