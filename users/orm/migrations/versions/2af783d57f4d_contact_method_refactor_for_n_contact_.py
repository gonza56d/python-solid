"""Contact method refactor for n contact method types

Revision ID: 2af783d57f4d
Revises: ccd4f7fb49ed
Create Date: 2022-01-24 18:05:26.201720

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2af783d57f4d'
down_revision = 'ccd4f7fb49ed'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    contact_method_type = sa.Enum('EMAIL', 'PHONE_NUMBER', 'ADDRESS', name='contactmethodtype')
    contact_method_type.create(op.get_bind())
    op.add_column('contact_methods', sa.Column('type', contact_method_type, nullable=False, server_default='EMAIL'))
    op.add_column('contact_methods', sa.Column('value', sa.String(), nullable=False, server_default=''))
    op.add_column('contact_methods', sa.Column('confirmed', sa.Boolean(), nullable=False))
    op.drop_column('contact_methods', 'phone_number')
    op.drop_column('contact_methods', 'email')
    op.create_unique_constraint('uix_1', 'contact_methods', ['user_id', 'type', 'value'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contact_methods', sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=True, server_default='some@email.com'))
    op.add_column('contact_methods', sa.Column('phone_number', sa.VARCHAR(), autoincrement=False, nullable=True, server_default=''))
    op.drop_column('contact_methods', 'confirmed')
    op.drop_column('contact_methods', 'value')
    op.drop_column('contact_methods', 'type')
    op.execute(
        'drop type contactmethodtype; '
        'alter table contact_methods drop constraint if exists uix_1;'
    )
    # ### end Alembic commands ###
