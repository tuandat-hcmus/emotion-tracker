"""add ai core quality fields

Revision ID: 0003_add_ai_core_quality_fields
Revises: 0002_add_wrapup_snapshots
Create Date: 2026-03-13 01:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_ai_core_quality_fields"
down_revision = "0002_add_wrapup_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("journal_entries")}

    def maybe_add_column(name: str, column: sa.Column) -> None:
        if name not in existing_columns:
            op.add_column("journal_entries", column)

    maybe_add_column("social_need_score", sa.Column("social_need_score", sa.Float(), nullable=True))
    maybe_add_column("emotion_confidence", sa.Column("emotion_confidence", sa.Float(), nullable=True))
    maybe_add_column("dominant_signals_text", sa.Column("dominant_signals_text", sa.Text(), nullable=True))
    maybe_add_column("response_mode", sa.Column("response_mode", sa.String(length=50), nullable=True))
    maybe_add_column("empathetic_response", sa.Column("empathetic_response", sa.Text(), nullable=True))
    maybe_add_column("gentle_suggestion", sa.Column("gentle_suggestion", sa.Text(), nullable=True))
    maybe_add_column("quote_text", sa.Column("quote_text", sa.Text(), nullable=True))
    maybe_add_column("response_metadata_text", sa.Column("response_metadata_text", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("journal_entries")}

    for column_name in (
        "response_metadata_text",
        "quote_text",
        "gentle_suggestion",
        "empathetic_response",
        "response_mode",
        "dominant_signals_text",
        "emotion_confidence",
        "social_need_score",
    ):
        if column_name in existing_columns:
            op.drop_column("journal_entries", column_name)
