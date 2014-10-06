"""remove year2

Revision ID: d78b9c2888f
Revises: 201d9d64479d
Create Date: 2014-09-17 23:32:53.435650

"""

# revision identifiers, used by Alembic.
revision = 'd78b9c2888f'
down_revision = '201d9d64479d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    #op.drop_column('game', 'yearid')
    op.drop_column('team', 'yearid')
    #op.drop_column('raw_game', 'yearid')
    pass


def downgrade():
    pass
