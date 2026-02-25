"""add upside_pct generated column to predictions

Revision ID: 67fa22f6433e
Revises: 5c3a9111b753
Create Date: 2026-02-25 21:15:33.653116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67fa22f6433e'
down_revision: Union[str, None] = '5c3a9111b753'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE predictions
        ADD COLUMN upside_pct DECIMAL(8,2)
        GENERATED ALWAYS AS (
            ROUND((target_price - price_at_prediction) / NULLIF(price_at_prediction, 0) * 100, 2)
        ) STORED
        """
    )


def downgrade() -> None:
    op.drop_column("predictions", "upside_pct")
