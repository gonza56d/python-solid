"""Added contact_confirmation and sign_up

Revision ID: f27de9be890a
Revises: 2af783d57f4d
Create Date: 2022-01-31 11:10:17.856289

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f27de9be890a'
down_revision = '2af783d57f4d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'users',
        'customer_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )

    stage = sa.Enum('EMAIL_CONFIRMATION', 'IDENTITY_VALIDATION', 'LEGAL_VALIDATION', 'PHONE_CONFIRMATION', 'GENERATE_CREDENTIALS', name='signupstage')
    op.create_table('sign_ups',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('stage', stage, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    confirmation_type = sa.Enum('TOKEN', 'OTP', name='contactconfirmationtype')
    confirmation_type.create(op.get_bind())
    op.add_column('contact_methods', sa.Column('confirmation_type', confirmation_type, nullable=False))
    op.add_column('contact_methods', sa.Column('confirmation_value', sa.String(), nullable=False))
    op.add_column('contact_methods', sa.Column('confirmation_created_at', sa.DateTime(), nullable=False))
    op.add_column('contact_methods', sa.Column('confirmation_expire_at', sa.DateTime(), nullable=False))
    op.add_column('contact_methods', sa.Column('confirmation_confirmed_at', sa.DateTime(), nullable=True))

    op.add_column('users', sa.Column('terms_and_conditions', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('users', sa.Column('address_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_unique_constraint('u_sign_ups_user_id', 'sign_ups', ['user_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'address_id')
    op.drop_column('users', 'terms_and_conditions')
    op.drop_constraint('u_sign_ups_user_id', 'sign_ups', type_='unique')
    op.drop_table('sign_ups')
    op.drop_column('contact_methods', 'confirmation_confirmed_at')
    op.drop_column('contact_methods', 'confirmation_expire_at')
    op.drop_column('contact_methods', 'confirmation_created_at')
    op.drop_column('contact_methods', 'confirmation_value')
    op.drop_column('contact_methods', 'confirmation_type')
    op.execute(
        'drop type signupstage; '
        'drop type contactconfirmationtype;'
    )
    op.alter_column(
        'users',
        'customer_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )
    # ### end Alembic commands ###
