from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TreeStateEvent(Base):
    __tablename__ = "tree_state_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    entry_id: Mapped[str] = mapped_column(String(36), index=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    vitality_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    vitality_score_after: Mapped[int] = mapped_column(Integer, nullable=False)
    current_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    leaf_state: Mapped[str] = mapped_column(String(50), nullable=False)
    weather_state: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
