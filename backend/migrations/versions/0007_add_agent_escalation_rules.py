"""add agent escalation rules

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Columna simple, sin constraint -- a diferencia de created_by (0006, con FK), esto no
    # necesita batch mode.
    op.add_column(
        "agents",
        sa.Column("escalation_rules", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("agents", "escalation_rules")
