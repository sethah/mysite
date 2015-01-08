"""add col index stat type

Revision ID: 2c523580685
Revises: 2d82b1419ff
Create Date: 2014-10-07 03:20:00.248502

"""

# revision identifiers, used by Alembic.
revision = '2c523580685'
down_revision = '2d82b1419ff'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('ix_stat_type', 'pbp', ['stat_type'])
    pass


def downgrade():
    pass
