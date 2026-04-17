"""add solana wallet auth fields and fix user wallet timestamps

Revision ID: 20260416_add_solana_wallet_auth_fields
Revises: 3ea19d5efaa6
Create Date: 2026-04-16 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260416_solana_auth"
down_revision = "20251221_add_shared_image_table"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("user")}

    if "wallet_auth_chain" not in columns:
        op.add_column("user", sa.Column("wallet_auth_chain", sa.String(length=32), nullable=True))

    if "wallet_challenge_hash" not in columns:
        op.add_column("user", sa.Column("wallet_challenge_hash", sa.String(length=128), nullable=True))

    if "wallet_challenge_expires_at" not in columns:
        op.add_column(
            "user",
            sa.Column("wallet_challenge_expires_at", sa.DateTime(timezone=True), nullable=True),
        )
    else:
        op.execute(
            """
            ALTER TABLE "user"
            ALTER COLUMN wallet_challenge_expires_at
            TYPE TIMESTAMPTZ
            USING wallet_challenge_expires_at AT TIME ZONE 'America/Sao_Paulo'
            """
        )

    if "wallet_last_signed_at" not in columns:
        op.add_column(
            "user",
            sa.Column("wallet_last_signed_at", sa.DateTime(timezone=True), nullable=True),
        )
    else:
        op.execute(
            """
            ALTER TABLE "user"
            ALTER COLUMN wallet_last_signed_at
            TYPE TIMESTAMPTZ
            USING wallet_last_signed_at AT TIME ZONE 'America/Sao_Paulo'
            """
        )


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("user")}

    if "wallet_last_signed_at" in columns:
        op.execute(
            """
            ALTER TABLE "user"
            ALTER COLUMN wallet_last_signed_at
            TYPE TIMESTAMP
            USING wallet_last_signed_at AT TIME ZONE 'UTC'
            """
        )

    if "wallet_challenge_expires_at" in columns:
        op.execute(
            """
            ALTER TABLE "user"
            ALTER COLUMN wallet_challenge_expires_at
            TYPE TIMESTAMP
            USING wallet_challenge_expires_at AT TIME ZONE 'UTC'
            """
        )

    if "wallet_challenge_hash" in columns:
        op.drop_column("user", "wallet_challenge_hash")

    if "wallet_auth_chain" in columns:
        op.drop_column("user", "wallet_auth_chain")

    if "wallet_last_signed_at" in columns:
        op.drop_column("user", "wallet_last_signed_at")

    if "wallet_challenge_expires_at" in columns:
        op.drop_column("user", "wallet_challenge_expires_at")