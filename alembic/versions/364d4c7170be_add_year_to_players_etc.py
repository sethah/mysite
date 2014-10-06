"""add year to players, etc

Revision ID: 364d4c7170be
Revises: 520c438567e
Create Date: 2014-09-18 00:20:56.428156

"""

# revision identifiers, used by Alembic.
revision = '364d4c7170be'
down_revision = '520c438567e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('raw_teams_year')
    op.add_column('players',sa.Column('year',sa.INTEGER))
    pass


def downgrade():
    pass
