"""change raw game date type and fix recipient column

Revision ID: 494173a8038b
Revises: 242705309f71
Create Date: 2014-08-21 01:01:19.964205

"""

# revision identifiers, used by Alembic.
revision = '494173a8038b'
down_revision = '242705309f71'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('pbp','recipient',type_=sa.VARCHAR(140))
    op.alter_column('raw_game','date',type_=sa.types.DateTime)


def downgrade():
    pass
