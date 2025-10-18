"""add_error_and_format_spec_to_conversion_usage

Revision ID: 9c8d3218bf49
Revises: 5787636bbd95
Create Date: 2025-10-18 13:40:09.394356

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c8d3218bf49'
down_revision = '5787636bbd95'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add error tracking columns
    op.add_column('conversion_usage', sa.Column('error_code', sa.String(), nullable=True))
    op.add_column('conversion_usage', sa.Column('error_message', sa.Text(), nullable=True))

    # Add format specification column for debugging
    op.add_column('conversion_usage', sa.Column('format_specification', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove columns in reverse order
    op.drop_column('conversion_usage', 'format_specification')
    op.drop_column('conversion_usage', 'error_message')
    op.drop_column('conversion_usage', 'error_code')