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
        sa.Index("ix_messages_conversation_id_sent_at", "conversation_id", "sent_at"),
        # Evita procesar el mismo mensaje entrante dos veces si el proveedor lo entrega por más
        # de una ruta (ej. dos instancias de WhatsApp vinculadas al mismo número a la vez). NULL
        # nunca choca consigo mismo en un índice único (ANSI SQL estándar), así que los mensajes
        # sin provider_message_id (ej. las respuestas de la IA, que no vienen de un webhook) no
        # se ven afectados.
        sa.Index(
            "ix_messages_channel_type_provider_message_id",
            "channel_type",
            "provider_message_id",
            unique=True,
            sqlite_where=sa.text("provider_message_id IS NOT NULL"),
            postgresql_where=sa.text("provider_message_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    sender_role: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    content_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    channel_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", sa.JSON, nullable=True
    )
