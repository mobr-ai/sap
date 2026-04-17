"""baseline (SAP bootstrap)

Revision ID: base_20251030
Revises:
Create Date: 2025-10-30 21:44:14.594556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "base_20251030"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user
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
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("avatar_blob", sa.LargeBinary(), nullable=True),
        sa.Column("avatar_mime", sa.String(length=64), nullable=True),
        sa.Column("avatar_etag", sa.String(length=64), nullable=True),
        sa.Column("avatar", sa.String(), nullable=True),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)
    op.create_index("ix_user_google_id", "user", ["google_id"], unique=True)
    op.create_index("ix_user_wallet_address", "user", ["wallet_address"], unique=False)
    op.create_index("ix_user_username", "user", ["username"], unique=True)

    # admin_setting
    op.create_table(
        "admin_setting",
        sa.Column("key", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("value", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )

    # kg_metrics
    op.create_table(
        "kg_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("triples_loaded", sa.Integer(), nullable=True),
        sa.Column("load_duration_ms", sa.Integer(), nullable=True),
        sa.Column("load_succeeded", sa.Boolean(), nullable=False),
        sa.Column("ontology_aligned", sa.Boolean(), nullable=True),
        sa.Column("has_offchain_metadata", sa.Boolean(), nullable=True),
        sa.Column("batch_number", sa.Integer(), nullable=True),
        sa.Column("graph_uri", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_kg_metrics_created_at", "kg_metrics", ["created_at"], unique=False)
    op.create_index("ix_kg_metrics_entity_type", "kg_metrics", ["entity_type"], unique=False)
    op.create_index("idx_kg_metrics_entity_date", "kg_metrics", ["entity_type", "created_at"], unique=False)

    # query_metrics
    op.create_table(
        "query_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=True),
        sa.Column("nl_query", sa.Text(), nullable=False),
        sa.Column("normalized_query", sa.Text(), nullable=False),
        sa.Column("detected_language", sa.String(length=10), nullable=False),
        sa.Column("sparql_query", sa.Text(), nullable=False),
        sa.Column("is_sequential", sa.Boolean(), nullable=True),
        sa.Column("is_federated", sa.Boolean(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=True),
        sa.Column("result_type", sa.String(length=50), nullable=True),
        sa.Column("kv_results", sa.JSON(), nullable=True),
        sa.Column("sparql_valid", sa.Boolean(), nullable=False),
        sa.Column("semantic_valid", sa.Boolean(), nullable=False),
        sa.Column("query_succeeded", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("complexity_score", sa.Integer(), nullable=True),
        sa.Column("has_multi_relationship", sa.Boolean(), nullable=True),
        sa.Column("has_aggregation", sa.Boolean(), nullable=True),
        sa.Column("has_temporal", sa.Boolean(), nullable=True),
        sa.Column("has_offchain_metadata", sa.Boolean(), nullable=True),
        sa.Column("llm_latency_ms", sa.Integer(), nullable=True),
        sa.Column("sparql_latency_ms", sa.Integer(), nullable=True),
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_query_metrics_user_id", "query_metrics", ["user_id"], unique=False)
    op.create_index("ix_query_metrics_normalized_query", "query_metrics", ["normalized_query"], unique=False)
    op.create_index("ix_query_metrics_detected_language", "query_metrics", ["detected_language"], unique=False)
    op.create_index("ix_query_metrics_created_at", "query_metrics", ["created_at"], unique=False)
    op.create_index("idx_query_metrics_language_date", "query_metrics", ["detected_language", "created_at"], unique=False)
    op.create_index("idx_query_metrics_user_date", "query_metrics", ["user_id", "created_at"], unique=False)
    op.create_index("idx_query_metrics_performance", "query_metrics", ["total_latency_ms", "created_at"], unique=False)

    # conversation
    op.create_table(
        "conversation",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_conversation_user_id", "conversation", ["user_id"], unique=False)

    # conversation_message
    op.create_table(
        "conversation_message",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("nl_query_id", sa.Integer(), sa.ForeignKey("query_metrics.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_conversation_message_conversation_id", "conversation_message", ["conversation_id"], unique=False)
    op.create_index("ix_conversation_message_user_id", "conversation_message", ["user_id"], unique=False)
    op.create_index("ix_conversation_message_nl_query_id", "conversation_message", ["nl_query_id"], unique=False)

    # conversation_artifact
    op.create_table(
        "conversation_artifact",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nl_query_id", sa.Integer(), sa.ForeignKey("query_metrics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("conversation_message_id", sa.Integer(), sa.ForeignKey("conversation_message.id", ondelete="SET NULL"), nullable=True),
        sa.Column("artifact_type", sa.String(length=50), nullable=False),
        sa.Column("kv_type", sa.String(length=50), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("artifact_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_conversation_artifact_conversation_id", "conversation_artifact", ["conversation_id"], unique=False)
    op.create_index("ix_conversation_artifact_nl_query_id", "conversation_artifact", ["nl_query_id"], unique=False)
    op.create_index("ix_conversation_artifact_conversation_message_id", "conversation_artifact", ["conversation_message_id"], unique=False)
    op.create_index("ix_conversation_artifact_created_at", "conversation_artifact", ["created_at"], unique=False)
    op.create_index(
        "idx_conversation_artifact_convo_created",
        "conversation_artifact",
        ["conversation_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "uq_conversation_artifact_convo_hash",
        "conversation_artifact",
        ["conversation_id", "artifact_hash"],
        unique=True,
    )

    # dashboard
    op.create_table(
        "dashboard",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_dashboard_user_id", "dashboard", ["user_id"], unique=False)

    # dashboard_item
    op.create_table(
        "dashboard_item",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("dashboard_id", sa.Integer(), sa.ForeignKey("dashboard.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "conversation_message_id",
            sa.Integer(),
            sa.ForeignKey("conversation_message.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversation.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("artifact_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("source_query", sa.String(length=1000), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_dashboard_item_dashboard_id", "dashboard_item", ["dashboard_id"], unique=False)
    op.create_index("ix_dashboard_item_conversation_message_id", "dashboard_item", ["conversation_message_id"], unique=False)
    op.create_index("ix_dashboard_item_conversation_id", "dashboard_item", ["conversation_id"], unique=False)

    # dashboard_metrics
    op.create_table(
        "dashboard_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("dashboard_id", sa.Integer(), sa.ForeignKey("dashboard.id"), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("artifact_type", sa.String(length=50), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=True),
        sa.Column("unique_artifact_types", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_dashboard_metrics_user_id", "dashboard_metrics", ["user_id"], unique=False)
    op.create_index("ix_dashboard_metrics_created_at", "dashboard_metrics", ["created_at"], unique=False)
    op.create_index("idx_dashboard_metrics_user_date", "dashboard_metrics", ["user_id", "created_at"], unique=False)

    # shared_image
    op.create_table(
        "shared_image",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("access_token", sa.String(length=64), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("mime", sa.String(length=64), nullable=False),
        sa.Column("bytes", sa.Integer(), nullable=False),
        sa.Column("etag", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_shared_image_user_id", "shared_image", ["user_id"], unique=False)
    op.create_index("ix_shared_image_access_token", "shared_image", ["access_token"], unique=False)
    op.create_index("ix_shared_image_created_at", "shared_image", ["created_at"], unique=False)
    op.create_index("ix_shared_image_expires_at", "shared_image", ["expires_at"], unique=False)
    op.create_index("uq_shared_image_user_sha", "shared_image", ["user_id", "content_sha256"], unique=True)
    op.create_index("idx_shared_image_expires", "shared_image", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_shared_image_expires", table_name="shared_image")
    op.drop_index("uq_shared_image_user_sha", table_name="shared_image")
    op.drop_index("ix_shared_image_expires_at", table_name="shared_image")
    op.drop_index("ix_shared_image_created_at", table_name="shared_image")
    op.drop_index("ix_shared_image_access_token", table_name="shared_image")
    op.drop_index("ix_shared_image_user_id", table_name="shared_image")
    op.drop_table("shared_image")

    op.drop_index("idx_dashboard_metrics_user_date", table_name="dashboard_metrics")
    op.drop_index("ix_dashboard_metrics_created_at", table_name="dashboard_metrics")
    op.drop_index("ix_dashboard_metrics_user_id", table_name="dashboard_metrics")
    op.drop_table("dashboard_metrics")

    op.drop_index("ix_dashboard_item_conversation_id", table_name="dashboard_item")
    op.drop_index("ix_dashboard_item_conversation_message_id", table_name="dashboard_item")
    op.drop_index("ix_dashboard_item_dashboard_id", table_name="dashboard_item")
    op.drop_table("dashboard_item")

    op.drop_index("ix_dashboard_user_id", table_name="dashboard")
    op.drop_table("dashboard")

    op.drop_index("uq_conversation_artifact_convo_hash", table_name="conversation_artifact")
    op.drop_index("idx_conversation_artifact_convo_created", table_name="conversation_artifact")
    op.drop_index("ix_conversation_artifact_created_at", table_name="conversation_artifact")
    op.drop_index("ix_conversation_artifact_conversation_message_id", table_name="conversation_artifact")
    op.drop_index("ix_conversation_artifact_nl_query_id", table_name="conversation_artifact")
    op.drop_index("ix_conversation_artifact_conversation_id", table_name="conversation_artifact")
    op.drop_table("conversation_artifact")

    op.drop_index("ix_conversation_message_nl_query_id", table_name="conversation_message")
    op.drop_index("ix_conversation_message_user_id", table_name="conversation_message")
    op.drop_index("ix_conversation_message_conversation_id", table_name="conversation_message")
    op.drop_table("conversation_message")

    op.drop_index("ix_conversation_user_id", table_name="conversation")
    op.drop_table("conversation")

    op.drop_index("idx_query_metrics_performance", table_name="query_metrics")
    op.drop_index("idx_query_metrics_user_date", table_name="query_metrics")
    op.drop_index("idx_query_metrics_language_date", table_name="query_metrics")
    op.drop_index("ix_query_metrics_created_at", table_name="query_metrics")
    op.drop_index("ix_query_metrics_detected_language", table_name="query_metrics")
    op.drop_index("ix_query_metrics_normalized_query", table_name="query_metrics")
    op.drop_index("ix_query_metrics_user_id", table_name="query_metrics")
    op.drop_table("query_metrics")

    op.drop_index("idx_kg_metrics_entity_date", table_name="kg_metrics")
    op.drop_index("ix_kg_metrics_entity_type", table_name="kg_metrics")
    op.drop_index("ix_kg_metrics_created_at", table_name="kg_metrics")
    op.drop_table("kg_metrics")

    op.drop_table("admin_setting")

    op.drop_index("ix_user_username", table_name="user")
    op.drop_index("ix_user_wallet_address", table_name="user")
    op.drop_index("ix_user_google_id", table_name="user")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")