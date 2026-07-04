from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class ContactModel(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        sa.UniqueConstraint(
            "external_id", "channel_type", "organization_id",
            name="uq_contacts_external_id_channel_org",
        ),
        sa.Index("ix_contacts_organization_id", "organization_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    external_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    channel_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
