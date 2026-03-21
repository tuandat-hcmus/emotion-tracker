from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


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
    dominant_emotional_patterns: list[str] = Field(default_factory=list)
    recurring_triggers: list[str] = Field(default_factory=list)
    workload_deadline_patterns: list[str] = Field(default_factory=list)
    positive_anchors: list[str] = Field(default_factory=list)
    emotional_direction_trend: str = "mixed"
    high_stress_frequency: float = 0.0
    summary_text: str | None = None


class JournalHistoryItemResponse(BaseModel):
    id: str
    entry_id: str
    status: str
    session_type: str
    source_type: str
    transcript_excerpt: str | None
    ai_response_excerpt: str | None
    primary_label: str | None
    secondary_labels: list[str]
    stress_score: float | None
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
