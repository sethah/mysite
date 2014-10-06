"""remove year3

Revision ID: 1bc5a967fef3
Revises: d78b9c2888f
Create Date: 2014-09-18 00:05:25.475684

"""

# revision identifiers, used by Alembic.
revision = '1bc5a967fef3'
down_revision = 'd78b9c2888f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('raw_game','yearid')
    op.drop_column('raw_game','location')
    pass


def downgrade():
    pass
