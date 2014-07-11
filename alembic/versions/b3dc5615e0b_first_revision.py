"""first revision

Revision ID: b3dc5615e0b
Revises: None
Create Date: 2014-07-10 19:49:36.383000

"""

# revision identifiers, used by Alembic.
revision = 'b3dc5615e0b'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('team',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ncaaID', sa.String(length=140), nullable=True),
    sa.Column('statsheet', sa.String(length=140), nullable=True),
    sa.Column('ncaa', sa.String(length=140), nullable=True),
    sa.Column('espn_name', sa.String(length=140), nullable=True),
    sa.Column('espn', sa.String(length=140), nullable=True),
    sa.Column('cbs1', sa.String(length=140), nullable=True),
    sa.Column('cbs2', sa.String(length=140), nullable=True),
    sa.Column('rpi_rank', sa.String(length=140), nullable=True),
    sa.Column('wins', sa.String(length=140), nullable=True),
    sa.Column('losses', sa.String(length=140), nullable=True),
    sa.Column('rpi', sa.String(length=140), nullable=True),
    sa.Column('sos', sa.String(length=140), nullable=True),
    sa.Column('sos_rank', sa.String(length=140), nullable=True),
    sa.Column('conference', sa.String(length=140), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('year',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nickname', sa.String(length=64), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('role', sa.SmallInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_name', 'users', ['name'], unique=True)
    op.create_index('ix_users_nickname', 'users', ['nickname'], unique=True)
    op.create_table('raw_teams_year',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('home_team', sa.String(length=100), nullable=True),
    sa.Column('away_team', sa.String(length=100), nullable=True),
    sa.Column('home_outcome', sa.String(length=1), nullable=True),
    sa.Column('home_score', sa.Integer(), nullable=True),
    sa.Column('away_score', sa.Integer(), nullable=True),
    sa.Column('neutral_site', sa.Boolean(), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('players',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('teamid', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=140), nullable=True),
    sa.Column('first_name', sa.String(length=140), nullable=True),
    sa.Column('last_name', sa.String(length=140), nullable=True),
    sa.Column('pclass', sa.String(length=140), nullable=True),
    sa.Column('height', sa.String(length=140), nullable=True),
    sa.Column('position', sa.String(length=140), nullable=True),
    sa.ForeignKeyConstraint(['teamid'], [u'team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('box_stat',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('gameid', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=140), nullable=True),
    sa.Column('first_name', sa.String(length=140), nullable=True),
    sa.Column('last_name', sa.String(length=140), nullable=True),
    sa.Column('started', sa.Integer(), nullable=True),
    sa.Column('min', sa.Integer(), nullable=True),
    sa.Column('pts', sa.Integer(), nullable=True),
    sa.Column('fgm', sa.Integer(), nullable=True),
    sa.Column('fga', sa.Integer(), nullable=True),
    sa.Column('tpm', sa.Integer(), nullable=True),
    sa.Column('tpa', sa.Integer(), nullable=True),
    sa.Column('ftm', sa.Integer(), nullable=True),
    sa.Column('fta', sa.Integer(), nullable=True),
    sa.Column('oreb', sa.Integer(), nullable=True),
    sa.Column('dreb', sa.Integer(), nullable=True),
    sa.Column('reb', sa.Integer(), nullable=True),
    sa.Column('ast', sa.Integer(), nullable=True),
    sa.Column('stl', sa.Integer(), nullable=True),
    sa.Column('blk', sa.Integer(), nullable=True),
    sa.Column('to', sa.Integer(), nullable=True),
    sa.Column('pf', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['gameid'], [u'game.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('raw_game',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('yearid', sa.Integer(), nullable=True),
    sa.Column('home_team', sa.String(length=140), nullable=True),
    sa.Column('away_team', sa.String(length=140), nullable=True),
    sa.Column('date', sa.String(length=140), nullable=True),
    sa.Column('location', sa.String(length=140), nullable=True),
    sa.Column('home_outcome', sa.String(length=140), nullable=True),
    sa.ForeignKeyConstraint(['yearid'], [u'year.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pbp',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('gameid', sa.Integer(), nullable=True),
    sa.Column('time', sa.Float(), nullable=True),
    sa.Column('player', sa.String(length=140), nullable=True),
    sa.Column('stat_type', sa.String(length=70), nullable=True),
    sa.Column('teamID', sa.Integer(), nullable=True),
    sa.Column('home_score', sa.Integer(), nullable=True),
    sa.Column('away_score', sa.Integer(), nullable=True),
    sa.Column('diff_score', sa.Integer(), nullable=True),
    sa.Column('possession', sa.Integer(), nullable=True),
    sa.Column('point_type', sa.String(length=20), nullable=True),
    sa.Column('result', sa.Integer(), nullable=True),
    sa.Column('value', sa.Integer(), nullable=True),
    sa.Column('worth', sa.Integer(), nullable=True),
    sa.Column('and_one', sa.String(length=2), nullable=True),
    sa.Column('rebound_type', sa.Integer(), nullable=True),
    sa.Column('recipient', sa.Integer(), nullable=True),
    sa.Column('assisted', sa.Integer(), nullable=True),
    sa.Column('charge', sa.Integer(), nullable=True),
    sa.Column('stolen', sa.Integer(), nullable=True),
    sa.Column('blocked', sa.Integer(), nullable=True),
    sa.Column('possession_change', sa.Integer(), nullable=True),
    sa.Column('home_fouls', sa.Float(), nullable=True),
    sa.Column('away_fouls', sa.Float(), nullable=True),
    sa.Column('second_chance', sa.Integer(), nullable=True),
    sa.Column('to_points', sa.Integer(), nullable=True),
    sa.Column('timeout_points', sa.Integer(), nullable=True),
    sa.Column('possession_time', sa.Integer(), nullable=True),
    sa.Column('possession_time_adj', sa.Integer(), nullable=True),
    sa.Column('home_lineup', sa.String(length=300), nullable=True),
    sa.Column('away_lineup', sa.String(length=300), nullable=True),
    sa.ForeignKeyConstraint(['gameid'], [u'game.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('raw_teams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('yearid', sa.Integer(), nullable=True),
    sa.Column('ncaaID', sa.String(length=140), nullable=True),
    sa.Column('statsheet', sa.String(length=140), nullable=True),
    sa.Column('ncaa', sa.String(length=140), nullable=True),
    sa.Column('espn_name', sa.String(length=140), nullable=True),
    sa.Column('espn', sa.String(length=140), nullable=True),
    sa.Column('cbs1', sa.String(length=140), nullable=True),
    sa.Column('cbs2', sa.String(length=140), nullable=True),
    sa.ForeignKeyConstraint(['yearid'], [u'raw_teams_year.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('raw_box',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('raw_game_id', sa.Integer(), nullable=True),
    sa.Column('soup_string', sa.String(length=1000), nullable=True),
    sa.ForeignKeyConstraint(['raw_game_id'], [u'raw_game.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('raw_play',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('raw_game_id', sa.Integer(), nullable=True),
    sa.Column('soup_string', sa.String(length=1000), nullable=True),
    sa.ForeignKeyConstraint(['raw_game_id'], [u'raw_game.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('raw_play')
    op.drop_table('raw_box')
    op.drop_table('raw_teams')
    op.drop_table('pbp')
    op.drop_table('raw_game')
    op.drop_table('box_stat')
    op.drop_table('players')
    op.drop_table('game')
    op.drop_table('raw_teams_year')
    op.drop_index('ix_users_nickname', table_name='users')
    op.drop_index('ix_users_name', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.drop_table('year')
    op.drop_table('team')
    ### end Alembic commands ###