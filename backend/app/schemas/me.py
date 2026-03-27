from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.schemas.user import JournalHistoryItemResponse


class PreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    locale: str
    timezone: str
    quote_opt_in: bool
    reminder_enabled: bool
    reminder_time: str | None
    preferred_tree_type: str
    checkin_goal_per_day: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime, _info: Any) -> str:
        return value.isoformat()


class UserProfileResponse(BaseModel):
    id: str
    email: str
    display_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    preferences: PreferenceResponse | None = None

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime, _info: Any) -> str:
        return value.isoformat()


class UpdateMeRequest(BaseModel):
    display_name: str | None = None


class UpsertPreferenceRequest(BaseModel):
    locale: str = "vi"
    timezone: str = "Asia/Bangkok"
    quote_opt_in: bool = True
    reminder_enabled: bool = False
    reminder_time: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    preferred_tree_type: str = "default"
    checkin_goal_per_day: int = Field(default=1, ge=1, le=5)


class QuoteResponse(BaseModel):
    short_text: str
    tone: str
    source_type: str


class HomeUserSummaryResponse(BaseModel):
    id: str
    email: str
    display_name: str | None


class HomePreferencesSummaryResponse(BaseModel):
    quote_opt_in: bool
    reminder_enabled: bool
    reminder_time: str | None
    preferred_tree_type: str
    checkin_goal_per_day: int


class CheckinStatusResponse(BaseModel):
    date: str
    has_morning_checkin: bool
    has_evening_checkin: bool
    total_entries: int
    session_types_present: list[str]
    latest_entry_id: str | None
    latest_emotion_label: str | None
    latest_risk_level: str | None


class HomeTodayResponse(CheckinStatusResponse):
    total_entries_today: int


class HomeTreeResponse(BaseModel):
    vitality_score: int
    streak_days: int
    current_stage: str | None
    leaf_state: str | None
    weather_state: str | None
    last_checkin_date: date | None

    @field_serializer("last_checkin_date")
    def serialize_tree_date(self, value: date | None, _info: Any) -> str | None:
        return value.isoformat() if value else None


class HomeRecentTrendResponse(BaseModel):
    last_7_days_average_valence: float | None
    last_7_days_average_stress: float | None
    entries_last_7_days: int


class HomeLatestWrapupMetaResponse(BaseModel):
    latest_weekly_wrapup_at: datetime | None
    latest_monthly_wrapup_at: datetime | None

    @field_serializer("latest_weekly_wrapup_at", "latest_monthly_wrapup_at")
    def serialize_wrapup_datetime(self, value: datetime | None, _info: Any) -> str | None:
        return value.isoformat() if value else None


class HomeResponse(BaseModel):
    user: HomeUserSummaryResponse
    preferences_summary: HomePreferencesSummaryResponse
    today: HomeTodayResponse
    tree: HomeTreeResponse
    recent_trend: HomeRecentTrendResponse
    quote: QuoteResponse | None
    latest_wrapup_meta: HomeLatestWrapupMetaResponse


class CalendarDayItemResponse(BaseModel):
    date: str
    entry_count: int
    has_morning_checkin: bool
    has_evening_checkin: bool
    primary_emotion_label: str | None
    average_valence_score: float | None
    average_stress_score: float | None
    max_risk_level: str | None
    topic_tags_top: list[str]
    mood_color_token: str


class CalendarResponse(BaseModel):
    user_id: str
    days: int
    items: list[CalendarDayItemResponse]


class WrapupDayHighlightResponse(BaseModel):
    date: str
    average_valence_score: float | None = None
    average_stress_score: float | None = None
    dominant_emotion_label: str | None = None
    risk_level: str | None = None


class WrapupStreakHighlightResponse(BaseModel):
    longest_streak_days: int
    current_streak_days: int


class WrapupConsistencyResponse(BaseModel):
    completed_days: int
    total_days: int
    ratio: float


class WrapupInsightCardResponse(BaseModel):
    kind: str
    title: str
    summary: str
    emphasis: str | None = None
    items: list[str] = Field(default_factory=list)


class WrapupTrendBlockResponse(BaseModel):
    emotional_direction_trend: str
    high_stress_frequency: float
    high_stress_entry_count: int
    workload_pattern_detected: bool
    positive_anchor_count: int
    recurring_trigger_count: int


class WrapupPayloadResponse(BaseModel):
    period_type: str
    period_start: str
    period_end: str
    total_entries: int
    total_checkin_days: int
    emotion_counts: dict[str, int]
    average_valence_score: float | None
    average_stress_score: float | None
    top_topics: list[str]
    strongest_positive_day: WrapupDayHighlightResponse | None
    heaviest_day: WrapupDayHighlightResponse | None
    streak_highlight: WrapupStreakHighlightResponse
    checkin_consistency: WrapupConsistencyResponse
    notable_shift: str
    dominant_emotional_patterns: list[str] = Field(default_factory=list)
    recurring_triggers: list[str] = Field(default_factory=list)
    workload_deadline_patterns: list[str] = Field(default_factory=list)
    positive_anchors: list[str] = Field(default_factory=list)
    emotional_direction_trend: str = "mixed"
    high_stress_frequency: float = 0.0
    summary_text: str | None = None
    insight_cards: list[WrapupInsightCardResponse] = Field(default_factory=list)
    trend_block: WrapupTrendBlockResponse | None = None
    closing_message: str


class WrapupSnapshotResponse(BaseModel):
    id: str
    user_id: str
    period_type: str
    period_start: date
    period_end: date
    payload: WrapupPayloadResponse
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    @field_serializer("period_start", "period_end")
    def serialize_snapshot_date(self, value: date, _info: Any) -> str:
        return value.isoformat()

    @field_serializer("generated_at", "created_at", "updated_at")
    def serialize_snapshot_datetime(self, value: datetime, _info: Any) -> str:
        return value.isoformat()


class WrapupRegenerateRequest(BaseModel):
    period_type: str = Field(pattern=r"^(week|month)$")
    anchor_date: date | None = None


class MonthlyWrapupPeriodResponse(BaseModel):
    year: int
    month: int
    label: str
    date_from: str
    date_to: str


class MonthlyWrapupOverviewResponse(BaseModel):
    summary_text: str | None = None
    dominant_emotion: str | None = None
    emotional_direction_trend: str = "mixed"
    overall_checkin_count: int
    high_stress_frequency: float


class MonthlyWrapupHeadlineCardResponse(BaseModel):
    id: str
    title: str
    subtitle: str | None = None
    value: str | int | float | None = None
    supporting_text: str | None = None
    icon_key: str
    color_token: str
    priority: int
    source_type: str


class MonthlyWrapupStatsResponse(BaseModel):
    total_checkins: int
    active_days: int
    avg_stress_score: float | None = None
    top_emotion: str | None = None
    top_trigger: str | None = None
    top_positive_anchor: str | None = None
    longest_gap_days: int | None = None
    best_streak_days: int | None = None


class MonthlyWrapupDistributionItemResponse(BaseModel):
    label: str
    count: int
    percent: float


class MonthlyWrapupWeeklyMetricResponse(BaseModel):
    week_label: str
    date_from: str
    date_to: str
    avg_stress_score: float | None = None
    count: int


class MonthlyWrapupDistributionsResponse(BaseModel):
    emotion_distribution: list[MonthlyWrapupDistributionItemResponse] = Field(default_factory=list)
    weekly_stress_trend: list[MonthlyWrapupWeeklyMetricResponse] = Field(default_factory=list)
    weekly_checkin_counts: list[MonthlyWrapupWeeklyMetricResponse] = Field(default_factory=list)


class MonthlyWrapupPatternItemResponse(BaseModel):
    label: str
    count: int
    weight: float | None = None
    icon_key: str
    color_token: str


class MonthlyWrapupPatternListsResponse(BaseModel):
    recurring_triggers: list[MonthlyWrapupPatternItemResponse] = Field(default_factory=list)
    positive_anchors: list[MonthlyWrapupPatternItemResponse] = Field(default_factory=list)
    workload_deadline_patterns: list[MonthlyWrapupPatternItemResponse] = Field(default_factory=list)
    dominant_emotional_patterns: list[MonthlyWrapupPatternItemResponse] = Field(default_factory=list)


class MonthlyWrapupVisualHintsResponse(BaseModel):
    month_mood_color: str
    month_theme_icon: str
    intensity_level: str


class MonthlyWrapupDetailResponse(BaseModel):
    period: MonthlyWrapupPeriodResponse
    overview: MonthlyWrapupOverviewResponse
    headline_cards: list[MonthlyWrapupHeadlineCardResponse] = Field(default_factory=list)
    stats: MonthlyWrapupStatsResponse
    distributions: MonthlyWrapupDistributionsResponse
    pattern_lists: MonthlyWrapupPatternListsResponse
    visual_hints: MonthlyWrapupVisualHintsResponse


class JournalMonthPeriodResponse(BaseModel):
    year: int
    month: int
    label: str
    date_from: str
    date_to: str


class JournalMonthResponse(BaseModel):
    period: JournalMonthPeriodResponse
    calendar_items: list[CalendarDayItemResponse] = Field(default_factory=list)
    entries: list[JournalHistoryItemResponse] = Field(default_factory=list)
    monthly_wrapup: WrapupSnapshotResponse | None = None
