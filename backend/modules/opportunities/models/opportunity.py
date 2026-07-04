from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class OpportunityModel(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        sa.Index("ix_opportunities_organization_id", "organization_id"),
        sa.Index("ix_opportunities_contact_id", "contact_id"),
        sa.Index("ix_opportunities_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    assigned_advisor_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(native_uuid=False), nullable=True
    )
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    attention_mode: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    channel_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
