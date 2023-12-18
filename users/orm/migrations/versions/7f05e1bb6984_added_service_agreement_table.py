"""Added service_agreement_table

Revision ID: 7f05e1bb6984
Revises: 129f5b9efddb
Create Date: 2022-03-11 14:55:19.554621

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from users.core.models import ServiceAgreement
from users.core.models.states import BusinessModel

# revision identifiers, used by Alembic.
revision = '7f05e1bb6984'
down_revision = '129f5b9efddb'
branch_labels = None
depends_on = None


def seed_service_agreements() -> None:
    """Seed the current existent service agreement."""
    service_agreements_list = [ServiceAgreement(**kwarg) for kwarg in [
        {'id': 0, 'business_model': BusinessModel.NUBI},
        {'id': 1, 'business_model': BusinessModel.NUBIZ},
    ]]

    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    session.add_all(service_agreements_list)
    session.commit()


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    business_model = sa.Enum('NUBI', 'NUBIZ', name='businessmodel')
    op.create_table('service_agreements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_model', business_model, nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    seed_service_agreements()
    op.create_foreign_key('fk_users__service_agreements', 'users', 'service_agreements', ['service_agr_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('fk_users__service_agreements', 'users', type_='foreignkey')
    op.drop_table('service_agreements')
    op.execute('drop type businessmodel;')
    # ### end Alembic commands ###
