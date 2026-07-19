"""add_tracking_results_table

Revision ID: a1b2c3d4e5f6
Revises: f8d2d36a2a47
Create Date: 2026-07-16 12:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f8d2d36a2a47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tracking_results",
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("localization_result_id", sa.Integer(), nullable=True),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("smoothed_latitude", sa.Float(), nullable=False),
        sa.Column("smoothed_longitude", sa.Float(), nullable=False),
        sa.Column("velocity_lat", sa.Float(), nullable=False),
        sa.Column("velocity_lon", sa.Float(), nullable=False),
        sa.Column("velocity_mps", sa.Float(), nullable=True),
        sa.Column("heading_deg", sa.Float(), nullable=True),
        sa.Column("error_m", sa.Float(), nullable=True),
        sa.Column("computation_time_ms", sa.Float(), nullable=True),
        sa.Column("algorithm", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["localization_result_id"], ["localization_results.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tracking_results_id"), "tracking_results", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_tracking_results_case_step"),
        "tracking_results",
        ["case_id", "step_number"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_tracking_results_case_step"), table_name="tracking_results")
    op.drop_index(op.f("ix_tracking_results_id"), table_name="tracking_results")
    op.drop_table("tracking_results")
