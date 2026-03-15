from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TreeState(Base):
    __tablename__ = "tree_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    vitality_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_stage: Mapped[str] = mapped_column(String(50), default="sapling", nullable=False)
    leaf_state: Mapped[str] = mapped_column(String(50), default="steady", nullable=False)
    weather_state: Mapped[str] = mapped_column(String(50), default="partly_cloudy", nullable=False)
    last_checkin_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
