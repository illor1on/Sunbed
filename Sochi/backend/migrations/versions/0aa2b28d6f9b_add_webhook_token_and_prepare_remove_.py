"""add webhook_token and prepare remove webhook_secret

Revision ID: 0aa2b28d6f9b
Revises: 60f686e32e69
Create Date: 2025-12-27 21:14:18.097795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0aa2b28d6f9b'
down_revision = '60f686e32e69'
branch_labels = None
depends_on = None


def upgrade():
    # 1️⃣ добавляем колонку webhook_token (пока nullable)
    op.add_column(
        "owner_payment_accounts",
        sa.Column("webhook_token", sa.String(length=128), nullable=True),
    )

    # 2️⃣ индекс (НЕ unique пока)
    op.create_index(
        "ix_owner_payment_accounts_webhook_token",
        "owner_payment_accounts",
        ["webhook_token"],
    )


def downgrade():
    op.drop_index(
        "ix_owner_payment_accounts_webhook_token",
        table_name="owner_payment_accounts",
    )
    op.drop_column("owner_payment_accounts", "webhook_token")