"""run share

Revision ID: 7ed974341957
Revises: bf1c0ec511d1
Create Date: 2022-05-13 08:25:41.252432

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ed974341957'
down_revision = 'bf1c0ec511d1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('run', sa.Column('share', sa.String(length=140), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('run', 'share')
    # ### end Alembic commands ###