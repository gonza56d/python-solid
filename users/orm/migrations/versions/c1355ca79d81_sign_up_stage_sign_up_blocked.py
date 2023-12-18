"""Sign up stage SIGN_UP_BLOCKED

Revision ID: c1355ca79d81
Revises: eb5b3bd97117
Create Date: 2022-07-18 14:01:57.293892

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1355ca79d81'
down_revision = 'eb5b3bd97117'
branch_labels = None
depends_on = None


def upgrade():
    # Add 'SIGN_UP_BLOCKED' value to sign_up.stage
    op.execute(
        "ALTER TABLE sign_ups ALTER COLUMN stage TYPE VARCHAR(255);"
        "DROP TYPE IF EXISTS signupstage;"
        "CREATE TYPE signupstage AS ENUM ("
        "'EMAIL_CONFIRMATION',"
        "'IDENTITY_VALIDATION',"
        "'LEGAL_VALIDATION',"
        "'PHONE_CONFIRMATION',"
        "'GENERATE_CREDENTIALS',"
        "'SIGN_UP_BLOCKED'"
        ");"
        "ALTER TABLE sign_ups ALTER COLUMN stage TYPE signupstage USING (stage::signupstage);"
    )
    # Add 'PENDING_AUTHORIZATION' value to user.status
    op.execute(
        "ALTER TABLE users ALTER COLUMN status TYPE VARCHAR(255);"
        "UPDATE users SET status = 'PENDING_VALIDATION' WHERE status = 'PENDIGN_VALIDATION';"
        "DROP TYPE IF EXISTS userstatus;"
        "CREATE TYPE userstatus AS ENUM ("
        "'PENDING_VALIDATION',"
        "'VALIDATION_REJECTED',"
        "'BANNED',"
        "'BANNED_NOTIFIED',"
        "'VALIDATED',"
        "'ACTIVE',"
        "'BLOCKED',"
        "'PENDING_AUTHORIZATION'"
        ");"
        "ALTER TABLE users ALTER COLUMN status TYPE userstatus USING (status::userstatus);"
    )


def downgrade():
    # Remove 'SIGN_UP_BLOCKED' value from sign_up.stage
    op.execute(
        "ALTER TABLE sign_ups ALTER COLUMN stage TYPE VARCHAR(255);"
        "DROP TYPE IF EXISTS signupstage;"
        "CREATE TYPE signupstage AS ENUM ("
        "'EMAIL_CONFIRMATION',"
        "'IDENTITY_VALIDATION',"
        "'LEGAL_VALIDATION',"
        "'PHONE_CONFIRMATION',"
        "'GENERATE_CREDENTIALS'"
        ");"
        "UPDATE sign_ups SET stage='IDENTITY_VALIDATION' WHERE stage='SIGN_UP_BLOCKED';"
        "ALTER TABLE sign_ups ALTER COLUMN stage TYPE signupstage USING (stage::signupstage);"
    )
    # Remove 'PENDING_AUTHORIZATION' value from user.status
    op.execute(
        "ALTER TABLE users ALTER COLUMN status TYPE VARCHAR(255);"
        "DROP TYPE IF EXISTS userstatus;"
        "CREATE TYPE userstatus AS ENUM ("
        "'PENDING_VALIDATION',"
        "'VALIDATION_REJECTED',"
        "'BANNED',"
        "'BANNED_NOTIFIED',"
        "'VALIDATED',"
        "'ACTIVE',"
        "'BLOCKED'"
        ");"
        "UPDATE users SET status='PENDING_VALIDATION' WHERE status='PENDING_AUTHORIZATION';"
        "ALTER TABLE users ALTER COLUMN status TYPE userstatus USING (status::userstatus);"
    )
