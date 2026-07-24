"""add_cgi_and_confidence_to_towers

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-22 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility when altering column nullability
    with op.batch_alter_table("towers", schema=None) as batch_op:
        batch_op.alter_column("latitude", existing_type=sa.Float(), nullable=True)
        batch_op.alter_column("longitude", existing_type=sa.Float(), nullable=True)
        batch_op.add_column(sa.Column("cgi", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("mcc", sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column("mnc", sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column("lac", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("ci", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("operator", sa.String(length=50), nullable=True))
        batch_op.add_column(
            sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0")
        )
        batch_op.add_column(
            sa.Column(
                "confidence_category",
                sa.String(length=50),
                nullable=False,
                server_default="Known",
            )
        )
        batch_op.add_column(
            sa.Column("resolution_method", sa.String(length=50), nullable=True)
        )
        batch_op.create_index("ix_towers_cgi", ["cgi"], unique=False)
        batch_op.create_index("ix_towers_mcc", ["mcc"], unique=False)
        batch_op.create_index("ix_towers_mnc", ["mnc"], unique=False)
        batch_op.create_index("ix_towers_lac", ["lac"], unique=False)
        batch_op.create_index("ix_towers_ci", ["ci"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("towers", schema=None) as batch_op:
        batch_op.drop_index("ix_towers_ci")
        batch_op.drop_index("ix_towers_lac")
        batch_op.drop_index("ix_towers_mnc")
        batch_op.drop_index("ix_towers_mcc")
        batch_op.drop_index("ix_towers_cgi")
        batch_op.drop_column("resolution_method")
        batch_op.drop_column("confidence_category")
        batch_op.drop_column("confidence")
        batch_op.drop_column("operator")
        batch_op.drop_column("ci")
        batch_op.drop_column("lac")
        batch_op.drop_column("mnc")
        batch_op.drop_column("mcc")
        batch_op.drop_column("cgi")
        batch_op.alter_column("longitude", existing_type=sa.Float(), nullable=False)
        batch_op.alter_column("latitude", existing_type=sa.Float(), nullable=False)
