"""add created_at to waiting_list

Revision ID: 20251213_waiting_list_created
Revises: 20251205_admin_settings
Create Date: 2025-12-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20251213_waiting_list_created"
down_revision = "20251205_admin_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "waiting_list" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("waiting_list")}
    if "created_at" not in columns:
        op.add_column(
            "waiting_list",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    indexes = {idx["name"] for idx in inspector.get_indexes("waiting_list")}
    if "ix_waiting_list_created_at" not in indexes:
        op.create_index("ix_waiting_list_created_at", "waiting_list", ["created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "waiting_list" not in inspector.get_table_names():
        return

    indexes = {idx["name"] for idx in inspector.get_indexes("waiting_list")}
    if "ix_waiting_list_created_at" in indexes:
        op.drop_index("ix_waiting_list_created_at", table_name="waiting_list")

    columns = {col["name"] for col in inspector.get_columns("waiting_list")}
    if "created_at" in columns:
        op.drop_column("waiting_list", "created_at")