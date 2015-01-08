"""add mult col index

Revision ID: 2d82b1419ff
Revises: 364d4c7170be
Create Date: 2014-10-07 01:51:43.090042

"""

# revision identifiers, used by Alembic.
revision = '2d82b1419ff'
down_revision = '364d4c7170be'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('ix_game', 'game', ['date', 'home_team','away_team'])


def downgrade():
    pass
