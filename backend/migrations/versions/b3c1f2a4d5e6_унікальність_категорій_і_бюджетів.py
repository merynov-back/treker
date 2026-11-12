"""унікальність категорій без регістру, загальний бюджет NULLS NOT DISTINCT

Revision ID: b3c1f2a4d5e6
Revises: 90d594eac026
Create Date: 2026-10-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c1f2a4d5e6'
down_revision: Union[str, Sequence[str], None] = '90d594eac026'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # «Кафе» і «кафе» тепер одна категорія і на рівні БД
    op.drop_constraint('uq_categories_user_name_type', 'categories', type_='unique')
    op.create_index(
        'uq_categories_user_lower_name_type',
        'categories',
        ['user_id', sa.text('lower(name)'), 'type'],
        unique=True,
    )

    # Два загальні ліміти (category_id = NULL) на один місяць більше не пройдуть
    op.drop_constraint('uq_budgets_user_category_period', 'budgets', type_='unique')
    op.create_unique_constraint(
        'uq_budgets_user_category_period',
        'budgets',
        ['user_id', 'category_id', 'year', 'month'],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_budgets_user_category_period', 'budgets', type_='unique')
    op.create_unique_constraint(
        'uq_budgets_user_category_period',
        'budgets',
        ['user_id', 'category_id', 'year', 'month'],
    )

    op.drop_index('uq_categories_user_lower_name_type', table_name='categories')
    op.create_unique_constraint('uq_categories_user_name_type', 'categories', ['user_id', 'name', 'type'])
