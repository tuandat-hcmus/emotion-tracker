"""add multimodal_sessions table

Revision ID: 0006_add_multimodal_sessions
Revises: 0005_add_conversation_tables
Create Date: 2026-03-29 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_add_multimodal_sessions"
down_revision = "0005_add_conversation_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "multimodal_sessions" not in existing_tables:
        op.create_table(
            "multimodal_sessions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(255), nullable=False, index=True),
            sa.Column("journal_entry_id", sa.String(36), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("emotion_label", sa.String(50), nullable=True),
            sa.Column("valence_score", sa.Float(), nullable=True),
            sa.Column("energy_score", sa.Float(), nullable=True),
            sa.Column("stress_score", sa.Float(), nullable=True),
            sa.Column("emotion_confidence", sa.Float(), nullable=True),
            sa.Column("fusion_source", sa.String(20), nullable=True),
            sa.Column("face_results_text", sa.Text(), nullable=True),
            sa.Column("audio_result_text", sa.Text(), nullable=True),
            sa.Column("fused_result_text", sa.Text(), nullable=True),
            sa.Column(
                "started_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_indexes 
                            WHERE indexname = 'ix_multimodal_sessions_user_id'
                        ) THEN
                            CREATE INDEX ix_multimodal_sessions_user_id 
                            ON multimodal_sessions (user_id);
                        END IF;
                    END$$;
                    """)
        op.create_index(
            "ix_multimodal_sessions_journal_entry_id",
            "multimodal_sessions",
            ["journal_entry_id"],
        )


def downgrade() -> None:
    op.drop_table("multimodal_sessions")
