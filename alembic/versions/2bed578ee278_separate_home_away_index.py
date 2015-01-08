"""separate home away index

Revision ID: 2bed578ee278
Revises: aaa82d6cb94
Create Date: 2014-10-08 00:41:36.029072

"""

# revision identifiers, used by Alembic.
revision = '2bed578ee278'
down_revision = 'aaa82d6cb94'

from alembic import op
import sqlalchemy as sa


def upgrade():
    #op.drop_index('ix_game_team','game')
    op.drop_index('ix_away_team','game')
    op.drop_index('ix_home_team','game')
    op.drop_index('ix_date','game')
    op.create_index('ix_home_team', 'game', ['home_team'])
    op.create_index('ix_away_team', 'game', ['away_team'])
    op.create_index('ix_date', 'game', ['date'])

    pass


def downgrade():
    pass
