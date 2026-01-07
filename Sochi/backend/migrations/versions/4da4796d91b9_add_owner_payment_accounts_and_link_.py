"""add owner payment accounts and link bookings

Revision ID: 4da4796d91b9
Revises: a5065fad68c9
Create Date: 2025-12-27 11:56:59.836990

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4da4796d91b9'
down_revision = 'a5065fad68c9'
branch_labels = None
depends_on = None


def upgrade():
    # ───────────────────────────────
    # owner_payment_accounts
    # ───────────────────────────────
    op.create_table(
        "owner_payment_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),

        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),

        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("shop_id", sa.String(length=100), nullable=False),
        sa.Column("secret_key", sa.String(length=255), nullable=False),
        sa.Column("webhook_secret", sa.String(length=255), nullable=False),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # индексы
    op.create_index(
        "idx_owner_payment_owner",
        "owner_payment_accounts",
        ["owner_id"],
    )
    op.create_index(
        "idx_owner_payment_provider",
        "owner_payment_accounts",
        ["provider"],
    )
    op.create_index(
        "idx_owner_payment_active",
        "owner_payment_accounts",
        ["owner_id", "provider", "is_active"],
        unique=True,
    )

    # ───────────────────────────────
    # bookings.payment_account_id
    # ───────────────────────────────
    op.add_column(
        "bookings",
        sa.Column(
            "payment_account_id",
            sa.Integer(),
            sa.ForeignKey("owner_payment_accounts.id"),
            nullable=True,
        ),
    )

    op.create_index(
        "idx_booking_payment_account",
        "bookings",
        ["payment_account_id"],
    )


def downgrade():
    # ───────────────────────────────
    # rollback bookings
    # ───────────────────────────────
    op.drop_index(
        "idx_booking_payment_account",
        table_name="bookings",
    )
    op.drop_column("bookings", "payment_account_id")

    # ───────────────────────────────
    # rollback owner_payment_accounts
    # ───────────────────────────────
    op.drop_index(
        "idx_owner_payment_active",
        table_name="owner_payment_accounts",
    )
    op.drop_index(
        "idx_owner_payment_provider",
        table_name="owner_payment_accounts",
    )
    op.drop_index(
        "idx_owner_payment_owner",
        table_name="owner_payment_accounts",
    )

    op.drop_table("owner_payment_accounts")