"""make access_code_valid_from/to timezone aware

Revision ID: a5065fad68c9
Revises: 9de8c003e054
Create Date: 2025-12-26 06:13:54.707305

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a5065fad68c9'
down_revision = '9de8c003e054'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE bookings
        ALTER COLUMN access_code_valid_from
        TYPE TIMESTAMPTZ
        USING access_code_valid_from AT TIME ZONE 'UTC'
    """)

    op.execute("""
        ALTER TABLE bookings
        ALTER COLUMN access_code_valid_to
        TYPE TIMESTAMPTZ
        USING access_code_valid_to AT TIME ZONE 'UTC'
    """)


    # ### end Alembic commands ###


def downgrade():
    op.execute("""
        ALTER TABLE bookings
        ALTER COLUMN access_code_valid_from
        TYPE TIMESTAMP
        USING access_code_valid_from AT TIME ZONE 'UTC'
    """)

    op.execute("""
        ALTER TABLE bookings
        ALTER COLUMN access_code_valid_to
        TYPE TIMESTAMP
        USING access_code_valid_to AT TIME ZONE 'UTC'
    """)


    # ### end Alembic commands ###
