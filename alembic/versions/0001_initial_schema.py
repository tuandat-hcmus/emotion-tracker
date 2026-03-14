"""initial schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-03-13 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    def maybe_create_index(index_name: str, table_name: str, columns: list[str], unique: bool) -> None:
        existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, columns, unique=unique)

    if "journal_entries" not in existing_tables:
        op.create_table(
            "journal_entries",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=255), nullable=False),
            sa.Column("session_type", sa.String(length=50), nullable=False),
            sa.Column("audio_path", sa.String(length=512), nullable=False),
            sa.Column("processing_status", sa.String(length=50), nullable=False),
            sa.Column("transcript_text", sa.Text(), nullable=True),
            sa.Column("transcript_confidence", sa.Float(), nullable=True),
            sa.Column("ai_response", sa.Text(), nullable=True),
            sa.Column("emotion_label", sa.String(length=50), nullable=True),
            sa.Column("valence_score", sa.Float(), nullable=True),
            sa.Column("energy_score", sa.Float(), nullable=True),
            sa.Column("stress_score", sa.Float(), nullable=True),
            sa.Column("topic_tags_text", sa.Text(), nullable=True),
            sa.Column("risk_level", sa.String(length=20), nullable=True),
            sa.Column("risk_flags_text", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        existing_tables.add("journal_entries")
    maybe_create_index(op.f("ix_journal_entries_user_id"), "journal_entries", ["user_id"], unique=False)

    if "processing_attempts" not in existing_tables:
        op.create_table(
            "processing_attempts",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("entry_id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=255), nullable=False),
            sa.Column("trigger_type", sa.String(length=20), nullable=False),
            sa.Column("provider_stt", sa.String(length=50), nullable=False),
            sa.Column("provider_response", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("used_override_transcript", sa.Boolean(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        existing_tables.add("processing_attempts")
    maybe_create_index(op.f("ix_processing_attempts_entry_id"), "processing_attempts", ["entry_id"], unique=False)
    maybe_create_index(op.f("ix_processing_attempts_user_id"), "processing_attempts", ["user_id"], unique=False)

    if "tree_states" not in existing_tables:
        op.create_table(
            "tree_states",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=255), nullable=False),
            sa.Column("vitality_score", sa.Integer(), nullable=False),
            sa.Column("streak_days", sa.Integer(), nullable=False),
            sa.Column("current_stage", sa.String(length=50), nullable=False),
            sa.Column("leaf_state", sa.String(length=50), nullable=False),
            sa.Column("weather_state", sa.String(length=50), nullable=False),
            sa.Column("last_checkin_date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        existing_tables.add("tree_states")
    maybe_create_index(op.f("ix_tree_states_user_id"), "tree_states", ["user_id"], unique=True)

    if "tree_state_events" not in existing_tables:
        op.create_table(
            "tree_state_events",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=255), nullable=False),
            sa.Column("entry_id", sa.String(length=36), nullable=False),
            sa.Column("event_date", sa.Date(), nullable=False),
            sa.Column("vitality_delta", sa.Integer(), nullable=False),
            sa.Column("vitality_score_after", sa.Integer(), nullable=False),
            sa.Column("current_stage", sa.String(length=50), nullable=False),
            sa.Column("leaf_state", sa.String(length=50), nullable=False),
            sa.Column("weather_state", sa.String(length=50), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        existing_tables.add("tree_state_events")
    maybe_create_index(op.f("ix_tree_state_events_entry_id"), "tree_state_events", ["entry_id"], unique=False)
    maybe_create_index(op.f("ix_tree_state_events_user_id"), "tree_state_events", ["user_id"], unique=False)

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        existing_tables.add("users")
    maybe_create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    if "user_preferences" not in existing_tables:
        op.create_table(
            "user_preferences",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("locale", sa.String(length=20), nullable=False),
            sa.Column("timezone", sa.String(length=100), nullable=False),
            sa.Column("quote_opt_in", sa.Boolean(), nullable=False),
            sa.Column("reminder_enabled", sa.Boolean(), nullable=False),
            sa.Column("reminder_time", sa.String(length=5), nullable=True),
            sa.Column("preferred_tree_type", sa.String(length=50), nullable=False),
            sa.Column("checkin_goal_per_day", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        existing_tables.add("user_preferences")
    maybe_create_index(op.f("ix_user_preferences_user_id"), "user_preferences", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_preferences_user_id"), table_name="user_preferences")
    op.drop_table("user_preferences")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_tree_state_events_user_id"), table_name="tree_state_events")
    op.drop_index(op.f("ix_tree_state_events_entry_id"), table_name="tree_state_events")
    op.drop_table("tree_state_events")
    op.drop_index(op.f("ix_tree_states_user_id"), table_name="tree_states")
    op.drop_table("tree_states")
    op.drop_index(op.f("ix_processing_attempts_user_id"), table_name="processing_attempts")
    op.drop_index(op.f("ix_processing_attempts_entry_id"), table_name="processing_attempts")
    op.drop_table("processing_attempts")
    op.drop_index(op.f("ix_journal_entries_user_id"), table_name="journal_entries")
    op.drop_table("journal_entries")
