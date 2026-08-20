"""add admin governance

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "internal_users",
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_internal_users_primary_admin",
        "internal_users",
        ["organization_id"],
        unique=True,
        sqlite_where=sa.text("is_primary = 1"),
    )

    # Backfill: si ya existe algún Administrator (ej. el sembrado manualmente en spec 008 para
    # validar OAuth), el más antiguo por organización se marca principal. No-op si no hay ninguno.
    op.execute(
        """
        UPDATE internal_users
        SET is_primary = 1
        WHERE id IN (
            SELECT id FROM internal_users iu
            WHERE role = 'administrator'
            AND created_at = (
                SELECT MIN(created_at) FROM internal_users
                WHERE organization_id = iu.organization_id AND role = 'administrator'
            )
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_internal_users_primary_admin", table_name="internal_users")
    op.drop_column("internal_users", "is_primary")
