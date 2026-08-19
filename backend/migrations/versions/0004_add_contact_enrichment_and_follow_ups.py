"""add contact enrichment and follow-ups

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "contacts",
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "opportunities",
        sa.Column("has_unread_messages", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "contact_notes",
        sa.Column("id", sa.Uuid(native_uuid=False), primary_key=True),
        sa.Column("contact_id", sa.Uuid(native_uuid=False), sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column(
            "author_id", sa.Uuid(native_uuid=False), sa.ForeignKey("internal_users.id"), nullable=False
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_contact_notes_contact_id", "contact_notes", ["contact_id"])

    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Uuid(native_uuid=False), primary_key=True),
        sa.Column(
            "opportunity_id",
            sa.Uuid(native_uuid=False),
            sa.ForeignKey("opportunities.id"),
            nullable=False,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_by", sa.Uuid(native_uuid=False), sa.ForeignKey("internal_users.id"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_follow_ups_opportunity_id", "follow_ups", ["opportunity_id"])


def downgrade() -> None:
    op.drop_index("ix_follow_ups_opportunity_id", table_name="follow_ups")
    op.drop_table("follow_ups")

    op.drop_index("ix_contact_notes_contact_id", table_name="contact_notes")
    op.drop_table("contact_notes")

    op.drop_column("opportunities", "has_unread_messages")
    op.drop_column("contacts", "is_favorite")
    op.drop_column("contacts", "tags")
