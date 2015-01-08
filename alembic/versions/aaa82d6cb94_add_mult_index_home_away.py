"""add mult index home/away

Revision ID: aaa82d6cb94
Revises: 2c523580685
Create Date: 2014-10-08 00:35:23.885009

"""

# revision identifiers, used by Alembic.
revision = 'aaa82d6cb94'
down_revision = '2c523580685'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('ix_game_team', 'game', ['home_team','away_team'])
    pass


def downgrade():
    pass
