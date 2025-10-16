"""add_token_tracking_to_conversion_usage

Revision ID: 5787636bbd95
Revises: 0b1e3f2d7e69
Create Date: 2025-10-16 12:35:27.237299

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5787636bbd95'
down_revision = '0b1e3f2d7e69'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add token tracking columns to conversion_usage table
    op.add_column('conversion_usage', sa.Column('input_tokens', sa.Integer(), nullable=True))
    op.add_column('conversion_usage', sa.Column('output_tokens', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove token tracking columns
    op.drop_column('conversion_usage', 'output_tokens')
    op.drop_column('conversion_usage', 'input_tokens')