"""add text checkin fields

Revision ID: 0004_add_text_checkin_fields
Revises: 0003_add_ai_core_quality_fields
Create Date: 2026-03-21 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_add_text_checkin_fields"
down_revision = "0003_add_ai_core_quality_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("journal_entries")}

    if "raw_text" not in existing_columns:
        op.add_column("journal_entries", sa.Column("raw_text", sa.Text(), nullable=True))

    audio_path_column = next((column for column in inspector.get_columns("journal_entries") if column["name"] == "audio_path"), None)
    if audio_path_column is not None and not audio_path_column.get("nullable", False):
        op.alter_column("journal_entries", "audio_path", existing_type=sa.String(length=512), nullable=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("journal_entries")}

    if "raw_text" in existing_columns:
        op.drop_column("journal_entries", "raw_text")

