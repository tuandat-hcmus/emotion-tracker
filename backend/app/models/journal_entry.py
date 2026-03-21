from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    session_type: Mapped[str] = mapped_column(String(50), default="free")
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="uploaded")
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotion_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    valence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    stress_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    social_need_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    emotion_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    dominant_signals_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic_tags_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk_flags_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    empathetic_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    gentle_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_metadata_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
