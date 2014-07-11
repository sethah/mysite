"""second revision

Revision ID: 22a769ae133f
Revises: b3dc5615e0b
Create Date: 2014-07-10 19:50:01.577000

"""

# revision identifiers, used by Alembic.
revision = '22a769ae133f'
down_revision = 'b3dc5615e0b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('team', sa.Column('yearid', sa.Integer))
    pass


def downgrade():
    op.drop_column('team', 'yearid')
    pass
