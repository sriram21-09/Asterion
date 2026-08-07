"""Add is_simulated and source to measurements table

Revision ID: a1b2c3d4e5f6
Revises: 9e7beaae84db
Create Date: 2026-08-06 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9e7beaae84db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "measurements",
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "measurements",
        sa.Column(
            "source", sa.String(length=50), nullable=False, server_default="REAL"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("measurements", "source")
    op.drop_column("measurements", "is_simulated")
