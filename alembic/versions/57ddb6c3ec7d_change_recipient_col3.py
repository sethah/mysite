"""change recipient col3

Revision ID: 57ddb6c3ec7d
Revises: 2dbbfc59c83a
Create Date: 2014-08-12 15:03:13.859225

"""

# revision identifiers, used by Alembic.
revision = '57ddb6c3ec7d'
down_revision = '2dbbfc59c83a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('pbp','recipient',type_=sa.VARCHAR(140))
    pass


def downgrade():
    pass
