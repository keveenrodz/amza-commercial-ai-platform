"""add user creation audit and real unread count

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # batch mode obligatorio aquí -- a diferencia de is_primary (0005, sin FK), SQLite no soporta
    # ALTER TABLE ADD COLUMN cuando la columna nueva trae una constraint (ver
    # sqlite.py::add_constraint), solo la estrategia de copiar-y-mover de batch_alter_table.
    with op.batch_alter_table("internal_users") as batch_op:
        batch_op.add_column(sa.Column("created_by", sa.Uuid(native_uuid=False), nullable=True))
        # batch mode reconstruye la tabla completa, y esa reconstrucción exige que cada
        # constraint tenga nombre explícito (a diferencia de un ForeignKey() inline en
        # op.create_table, que sí puede quedar sin nombre) -- de ahí create_foreign_key en vez
        # de pasar ForeignKey() directo en la columna.
        batch_op.create_foreign_key(
            "fk_internal_users_created_by",
            "internal_users",
            ["created_by"],
            ["id"],
        )

    op.add_column(
        "opportunities",
        sa.Column("unread_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute("UPDATE opportunities SET unread_count = 1 WHERE has_unread_messages = 1")
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_column("has_unread_messages")


def downgrade() -> None:
    op.add_column(
        "opportunities",
        sa.Column("has_unread_messages", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("UPDATE opportunities SET has_unread_messages = 1 WHERE unread_count > 0")
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_column("unread_count")

    with op.batch_alter_table("internal_users") as batch_op:
        batch_op.drop_column("created_by")
