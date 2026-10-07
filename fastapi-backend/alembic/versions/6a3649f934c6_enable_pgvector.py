"""enable pgvector

Revision ID: 6a3649f934c6
Revises: 8c923781cb03
Create Date: 2026-10-07 15:20:41.747245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a3649f934c6'
down_revision: Union[str, Sequence[str], None] = '8c923781cb03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
