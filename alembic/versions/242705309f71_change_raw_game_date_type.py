"""change raw game date type

Revision ID: 242705309f71
Revises: 57ddb6c3ec7d
Create Date: 2014-08-21 00:53:28.845343

"""

# revision identifiers, used by Alembic.
revision = '242705309f71'
down_revision = '57ddb6c3ec7d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('pbp','recipient',type_=sa.types.DateTime)


def downgrade():
    pass
