"""create session events

Revision ID: b7a9c4e21d14
Revises: 78c3a218e917
Create Date: 2026-10-27

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7a9c4e21d14"
down_revision: str | None = "78c3a218e917"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "session_events",
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "sequence",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "idempotency_key",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "session_id",
            "sequence",
        ),
        sa.UniqueConstraint(
            "session_id",
            "idempotency_key",
            name=(
                "uq_session_events_session_id_"
                "idempotency_key"
            ),
        ),
    )


def downgrade() -> None:
    op.drop_table("session_events")