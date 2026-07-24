"""add_movement_events_table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-23 14:00:00.000000

"""

<<<<<<< HEAD
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
=======
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "movement_events",
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("cdr_record_id", sa.Integer(), nullable=True),
        sa.Column("tracking_result_id", sa.Integer(), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("from_cgi", sa.String(length=100), nullable=True),
        sa.Column("to_cgi", sa.String(length=100), nullable=True),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("heading_deg", sa.Float(), nullable=True),
        sa.Column("distance_from_prev_m", sa.Float(), nullable=True),
        sa.Column("dwell_time_seconds", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
<<<<<<< HEAD
        sa.ForeignKeyConstraint(["cdr_record_id"], ["cdr_records.id"], ondelete="SET NULL"),
=======
        sa.ForeignKeyConstraint(
            ["cdr_record_id"], ["cdr_records.id"], ondelete="SET NULL"
        ),
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
        sa.ForeignKeyConstraint(
            ["tracking_result_id"], ["tracking_results.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_movement_events_id"), "movement_events", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_movement_events_case_id"), "movement_events", ["case_id"], unique=False
    )
    op.create_index(
<<<<<<< HEAD
        op.f("ix_movement_events_timestamp"), "movement_events", ["timestamp"], unique=False
=======
        op.f("ix_movement_events_timestamp"),
        "movement_events",
        ["timestamp"],
        unique=False,
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
    )
    op.create_index(
        op.f("ix_movement_events_case_seq"),
        "movement_events",
        ["case_id", "sequence_number"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_movement_events_case_seq"), table_name="movement_events")
    op.drop_index(op.f("ix_movement_events_timestamp"), table_name="movement_events")
    op.drop_index(op.f("ix_movement_events_case_id"), table_name="movement_events")
    op.drop_index(op.f("ix_movement_events_id"), table_name="movement_events")
    op.drop_table("movement_events")
