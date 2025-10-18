"""add_parsing_method_to_conversion_usage

Revision ID: 05687ddc8ff3
Revises: 9c8d3218bf49
Create Date: 2025-10-18 13:57:42.869271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05687ddc8ff3'
down_revision = '9c8d3218bf49'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add parsing_method column to track which parsing route was used
    op.add_column('conversion_usage', sa.Column('parsing_method', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove parsing_method column
    op.drop_column('conversion_usage', 'parsing_method')