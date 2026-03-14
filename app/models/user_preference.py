from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    locale: Mapped[str] = mapped_column(String(20), default="vi", nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), default="Asia/Bangkok", nullable=False)
    quote_opt_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    preferred_tree_type: Mapped[str] = mapped_column(String(50), default="default", nullable=False)
    checkin_goal_per_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
