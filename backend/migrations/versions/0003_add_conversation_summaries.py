"""add conversation summaries

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.Uuid(native_uuid=False), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(native_uuid=False), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("up_to_sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_conversation_summaries_conversation_id_version",
        "conversation_summaries",
        ["conversation_id", "version"],
    )

    # Reemplaza los dos índices simples por uno compuesto: list_since/count_since filtran por
    # ambas columnas a la vez, y el compuesto también cubre las búsquedas solo por conversation_id
    # (prefijo izquierdo) que hacía el índice simple que se elimina.
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_index("ix_messages_sent_at", table_name="messages")
    op.create_index(
        "ix_messages_conversation_id_sent_at",
        "messages",
        ["conversation_id", "sent_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_id_sent_at", table_name="messages")
    op.create_index("ix_messages_sent_at", "messages", ["sent_at"])
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.drop_index(
        "ix_conversation_summaries_conversation_id_version",
        table_name="conversation_summaries",
    )
    op.drop_table("conversation_summaries")
