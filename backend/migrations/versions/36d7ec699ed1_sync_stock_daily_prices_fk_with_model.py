"""sync stock_daily_prices FK with model

Revision ID: 36d7ec699ed1
Revises: 128077f8d4fe
Create Date: 2026-02-24 23:39:41.911223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36d7ec699ed1'
down_revision: Union[str, None] = '128077f8d4fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        'fk_stock_daily_prices_stock_id', 'stock_daily_prices', 'stocks', ['stock_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_stock_daily_prices_stock_id', 'stock_daily_prices', type_='foreignkey')
