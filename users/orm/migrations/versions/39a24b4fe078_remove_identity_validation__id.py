"""remove identity_validation_
id

Revision ID: 39a24b4fe078
Revises: c93acbd5d2d1
Create Date: 2022-08-02 14:07:03.483077

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '39a24b4fe078'
down_revision = 'c93acbd5d2d1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'identity_validation_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('identity_validation_id', postgresql.UUID(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###