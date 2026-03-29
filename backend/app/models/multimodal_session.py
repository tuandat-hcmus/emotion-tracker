from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MultimodalSession(Base):
    __tablename__ = "multimodal_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    journal_entry_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    emotion_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    valence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    stress_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    emotion_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    fusion_source: Mapped[str | None] = mapped_column(String(20), nullable=True)
    face_results_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_result_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    fused_result_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
