"""remove year table

Revision ID: 520c438567e
Revises: 1bc5a967fef3
Create Date: 2014-09-18 00:15:31.343081

"""

# revision identifiers, used by Alembic.
revision = '520c438567e'
down_revision = '1bc5a967fef3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('year')
    pass


def downgrade():
    pass
