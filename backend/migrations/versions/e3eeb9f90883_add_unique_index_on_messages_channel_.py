"""add unique index on messages channel_type provider_message_id

Revision ID: e3eeb9f90883
Revises: 0007
Create Date: 2026-08-22 12:23:20.111590

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'e3eeb9f90883'
down_revision: str | None = '0007'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nota: el autogenerate de Alembic también proponía DROP TABLE para `follow_ups` y
    # `contact_notes`, y DROP INDEX para `ix_internal_users_primary_admin` -- un falso positivo,
    # esas tablas siguen en uso (spec 013/014), el problema es que env.py no las tiene en su
    # metadata objetivo. Se descartó esa parte a mano; esta migración solo agrega el índice
    # nuevo.
    op.create_index(
        'ix_messages_channel_type_provider_message_id',
        'messages',
        ['channel_type', 'provider_message_id'],
        unique=True,
        sqlite_where=sa.text('provider_message_id IS NOT NULL'),
        postgresql_where=sa.text('provider_message_id IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index(
        'ix_messages_channel_type_provider_message_id',
        table_name='messages',
        sqlite_where=sa.text('provider_message_id IS NOT NULL'),
        postgresql_where=sa.text('provider_message_id IS NOT NULL'),
    )
