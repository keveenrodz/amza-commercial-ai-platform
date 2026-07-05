"""fix entity model alignment

Revision ID: 0002
Revises: da934eca16fd
Create Date: 2026-07-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "da934eca16fd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("content_type", sa.String(50), nullable=False, server_default="text"),
    )
    op.add_column(
        "messages",
        sa.Column("provider_message_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "contacts",
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
    )


def downgrade() -> None:
    # SQLite no soporta DROP COLUMN en versiones < 3.35.
    # En PostgreSQL se implementaría con op.drop_column().
    pass
