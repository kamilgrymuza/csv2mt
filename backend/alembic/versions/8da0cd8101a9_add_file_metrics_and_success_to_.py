"""add_file_metrics_and_success_to_conversion_usage

Revision ID: 8da0cd8101a9
Revises: 05687ddc8ff3
Create Date: 2025-10-18 14:18:49.932106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8da0cd8101a9'
down_revision = '05687ddc8ff3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add file size metrics columns
    op.add_column('conversion_usage', sa.Column('file_line_count', sa.Integer(), nullable=True))
    op.add_column('conversion_usage', sa.Column('file_page_count', sa.Integer(), nullable=True))

    # Add conversion success tracking column
    op.add_column('conversion_usage', sa.Column('success', sa.Boolean(), nullable=True))


def downgrade() -> None:
    # Remove columns in reverse order
    op.drop_column('conversion_usage', 'success')
    op.drop_column('conversion_usage', 'file_page_count')
    op.drop_column('conversion_usage', 'file_line_count')