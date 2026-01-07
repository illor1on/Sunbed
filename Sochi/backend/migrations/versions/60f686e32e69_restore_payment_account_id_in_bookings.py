"""restore payment_account_id in bookings

Revision ID: 60f686e32e69
Revises: 4da4796d91b9
Create Date: 2025-12-27 12:29:08.957137

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '60f686e32e69'
down_revision = '4da4796d91b9'
branch_labels = None
depends_on = None


def upgrade():
    # если колонка была удалена вручную — просто добавляем её обратно
    op.add_column(
        "bookings",
        sa.Column(
            "payment_account_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_bookings_payment_account",
        "bookings",
        "owner_payment_accounts",
        ["payment_account_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "idx_booking_payment_account",
        "bookings",
        ["payment_account_id"],
    )


def downgrade():
    op.drop_index(
        "idx_booking_payment_account",
        table_name="bookings",
    )

    op.drop_constraint(
        "fk_bookings_payment_account",
        "bookings",
        type_="foreignkey",
    )

    op.drop_column(
        "bookings",
        "payment_account_id",
    )