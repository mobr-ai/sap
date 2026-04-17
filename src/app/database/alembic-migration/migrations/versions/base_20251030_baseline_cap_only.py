"""baseline (SAP bootstrap)

Revision ID: base_20251030
Revises:
Create Date: 2025-10-30 21:44:14.594556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "base_20251030"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("user_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("google_id", sa.String(), nullable=True),
        sa.Column("wallet_address", sa.String(length=128), nullable=True),
        sa.Column("username", sa.String(length=30), nullable=True),
        sa.Column("display_name", sa.String(length=30), nullable=True),
        sa.Column("settings", sa.String(), nullable=True),
        sa.Column("refer_id", sa.Integer(), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=True),
        sa.Column("confirmation_token", sa.String(length=128), nullable=True),
        sa.Column("avatar", sa.String(), nullable=True),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)
    op.create_index("ix_user_google_id", "user", ["google_id"], unique=True)
    op.create_index("ix_user_wallet_address", "user", ["wallet_address"], unique=False)
    op.create_index("ix_user_username", "user", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_username", table_name="user")
    op.drop_index("ix_user_wallet_address", table_name="user")
    op.drop_index("ix_user_google_id", table_name="user")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")