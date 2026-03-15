from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class TreeStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    vitality_score: int
    streak_days: int
    current_stage: str
    leaf_state: str
    weather_state: str
    last_checkin_date: date | None
    updated_at: datetime

    @field_serializer("last_checkin_date")
    def serialize_date(self, value: date | None, _info: Any) -> str | None:
        return value.isoformat() if value else None

    @field_serializer("updated_at")
    def serialize_datetime(self, value: datetime, _info: Any) -> str:
        return value.isoformat()


class UserSummaryResponse(BaseModel):
    user_id: str
    days: int
    total_entries: int
    emotion_counts: dict[str, int]
    average_valence_score: float | None
    average_energy_score: float | None
    average_stress_score: float | None
    top_topics: list[str]
    risk_counts: dict[str, int]
    latest_entry_at: str | None


class JournalHistoryItemResponse(BaseModel):
    entry_id: str
    status: str
    session_type: str
    transcript_text: str | None
    ai_response: str | None
    emotion_label: str | None
    valence_score: float | None
    energy_score: float | None
    stress_score: float | None
    risk_level: str | None
    topic_tags: list[str]
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_history_datetime(self, value: datetime, _info: Any) -> str:
        return value.isoformat()


class JournalHistoryResponse(BaseModel):
    user_id: str
    total: int
    limit: int
    offset: int
    items: list[JournalHistoryItemResponse]


class TreeTimelineItemResponse(BaseModel):
    date: str
    entry_count: int
    average_valence_score: float | None
    average_stress_score: float | None
    dominant_emotion_label: str | None
    vitality_score_after_day: int | None
    leaf_state: str | None
    weather_state: str | None


class TreeTimelineResponse(BaseModel):
    user_id: str
    days: int
    items: list[TreeTimelineItemResponse]
