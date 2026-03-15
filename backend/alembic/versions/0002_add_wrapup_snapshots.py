"""add wrapup snapshots

Revision ID: 0002_add_wrapup_snapshots
Revises: 0001_initial_schema
Create Date: 2026-03-13 00:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_wrapup_snapshots"
down_revision = "0001_initial_schema"
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

    if "wrapup_snapshots" not in existing_tables:
        op.create_table(
            "wrapup_snapshots",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("period_type", sa.String(length=10), nullable=False),
            sa.Column("period_start", sa.Date(), nullable=False),
            sa.Column("period_end", sa.Date(), nullable=False),
            sa.Column("payload_text", sa.Text(), nullable=False),
            sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "period_type",
                "period_start",
                "period_end",
                name="uq_wrapup_snapshot_period",
            ),
        )
        existing_tables.add("wrapup_snapshots")

    maybe_create_index(op.f("ix_wrapup_snapshots_user_id"), "wrapup_snapshots", ["user_id"], unique=False)
    maybe_create_index(op.f("ix_wrapup_snapshots_period_type"), "wrapup_snapshots", ["period_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_wrapup_snapshots_period_type"), table_name="wrapup_snapshots")
    op.drop_index(op.f("ix_wrapup_snapshots_user_id"), table_name="wrapup_snapshots")
    op.drop_table("wrapup_snapshots")
