"""Added outbox messages table

Revision ID: b7c91e3a4f10
Revises: aa484214d022
Create Date: 2026-09-22 16:31:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c91e3a4f10"
down_revision: Union[str, Sequence[str], None] = "aa484214d022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("aggregate_id", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_outbox_messages_event_type"),
        "outbox_messages",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outbox_messages_aggregate_id"),
        "outbox_messages",
        ["aggregate_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outbox_messages_published_at"),
        "outbox_messages",
        ["published_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_outbox_messages_published_at"), table_name="outbox_messages")
    op.drop_index(op.f("ix_outbox_messages_aggregate_id"), table_name="outbox_messages")
    op.drop_index(op.f("ix_outbox_messages_event_type"), table_name="outbox_messages")
    op.drop_table("outbox_messages")
