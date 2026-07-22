"""add_import_jobs_and_cdr_records

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-20 10:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "8361cc10ba52"

branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("operator", sa.String(length=50), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parsed_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("case_id", sa.Integer(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_jobs_id"), "import_jobs", ["id"], unique=False)

    op.create_table(
        "cdr_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("import_job_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("operator", sa.String(length=50), nullable=False),
        sa.Column("target_number", sa.String(length=50), nullable=True),
        sa.Column("b_party_number", sa.String(length=50), nullable=True),
        sa.Column("call_type", sa.String(length=50), nullable=True),
        sa.Column("service_type", sa.String(length=50), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("first_cgi", sa.String(length=100), nullable=True),
        sa.Column("first_bts_location", sa.Text(), nullable=True),
        sa.Column("last_latitude", sa.Float(), nullable=True),
        sa.Column("last_longitude", sa.Float(), nullable=True),
        sa.Column("last_cgi", sa.String(length=100), nullable=True),
        sa.Column("last_bts_location", sa.Text(), nullable=True),
        sa.Column("imei", sa.String(length=50), nullable=True),
        sa.Column("imsi", sa.String(length=50), nullable=True),
        sa.Column("smsc_number", sa.String(length=50), nullable=True),
        sa.Column("roaming_network", sa.String(length=100), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["import_job_id"], ["import_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cdr_records_id"), "cdr_records", ["id"], unique=False)
    op.create_index(
        op.f("ix_cdr_records_import_job_id"), "cdr_records", ["import_job_id"], unique=False
    )
    op.create_index(op.f("ix_cdr_records_case_id"), "cdr_records", ["case_id"], unique=False)
    op.create_index(
        op.f("ix_cdr_records_target_number"), "cdr_records", ["target_number"], unique=False
    )
    op.create_index(
        op.f("ix_cdr_records_timestamp"), "cdr_records", ["timestamp"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_cdr_records_timestamp"), table_name="cdr_records")
    op.drop_index(op.f("ix_cdr_records_target_number"), table_name="cdr_records")
    op.drop_index(op.f("ix_cdr_records_case_id"), table_name="cdr_records")
    op.drop_index(op.f("ix_cdr_records_import_job_id"), table_name="cdr_records")
    op.drop_index(op.f("ix_cdr_records_id"), table_name="cdr_records")
    op.drop_table("cdr_records")

    op.drop_index(op.f("ix_import_jobs_id"), table_name="import_jobs")
    op.drop_table("import_jobs")
