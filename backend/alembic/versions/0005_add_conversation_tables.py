"""add conversation tables

Revision ID: 0005_add_conversation_tables
Revises: 0004_add_text_checkin_fields
Create Date: 2026-03-21 00:00:01
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_add_conversation_tables"
down_revision = "0004_add_text_checkin_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "conversation_sessions" not in tables:
        op.create_table(
            "conversation_sessions",
            sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_conversation_sessions_user_id", "conversation_sessions", ["user_id"], unique=False)

    if "conversation_turns" not in tables:
        op.create_table(
            "conversation_turns",
            sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column("session_id", sa.String(length=36), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("audio_path", sa.String(length=512), nullable=True),
            sa.Column("emotion_snapshot", sa.Text(), nullable=True),
            sa.Column("state_snapshot", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_conversation_turns_session_id", "conversation_turns", ["session_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "conversation_turns" in tables:
        indexes = {index["name"] for index in inspector.get_indexes("conversation_turns")}
        if "ix_conversation_turns_session_id" in indexes:
            op.drop_index("ix_conversation_turns_session_id", table_name="conversation_turns")
        op.drop_table("conversation_turns")

    if "conversation_sessions" in tables:
        indexes = {index["name"] for index in inspector.get_indexes("conversation_sessions")}
        if "ix_conversation_sessions_user_id" in indexes:
            op.drop_index("ix_conversation_sessions_user_id", table_name="conversation_sessions")
        op.drop_table("conversation_sessions")
