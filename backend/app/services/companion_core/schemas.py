from datetime import datetime, timezone

from pydantic import BaseModel, Field


class NormalizedEmotionalState(BaseModel):
    language: str
    primary_emotion: str
    secondary_emotions: list[str] = Field(default_factory=list)
    valence: float
    energy: float
    stress: float
    emotion_owner: str = "user"
    user_stance: str = "processing_self"
    social_context: str = "solo"
    event_type: str = "uncertain_mixed_state"
    concern_target: str | None = None
    relationship_role: str | None = None
    uncertainty: float = 0.0
    confidence: float
    owner_confidence: float = 0.0
    event_confidence: float = 0.0
    target_confidence: float = 0.0
    stance_confidence: float = 0.0
    response_mode: str
    risk_level: str
    topic_tags: list[str] = Field(default_factory=list)
    evidence_spans: list[str] = Field(default_factory=list)
    source_provider: str = "unknown"


class RenderContext(BaseModel):
    utterance_type: str = "reflective_checkin"
    event_type: str = "uncertain_mixed_state"
    relationship_target: str | None = None
    relationship_role: str | None = None
    relationship_concern: bool = False
    health_related_update: bool = False
    short_personal_update: bool = False
    short_event_flag: bool = False
    low_energy_update: bool = False
    appreciation_or_recognition: bool = False
    positive_personal_update: bool = False
    reflective_checkin: bool = False
    responsibility_tension: bool = False
    distress_checkin: bool = False
    user_stance: str = "processing_self"
    social_context: str = "solo"
    concern_target: str | None = None
    other_person_state_mentioned: bool = False
    other_person_emotion_word: str | None = None
    emotion_owner_hint: str = "user"
    greeting_only: bool = False
    suggestion_allowed: bool = True
    evidence_spans: list[str] = Field(default_factory=list)


class SupportStrategy(BaseModel):
    support_focus: str
    strategy_type: str
    suggestion_budget: str
    personalization_tone: str
    response_goal: str
    rationale: list[str] = Field(default_factory=list)


class InsightFeatures(BaseModel):
    is_negative_checkin: bool = False
    is_positive_checkin: bool = False
    work_trigger: bool = False
    relationship_strain: bool = False
    deadline_related: bool = False
    loneliness_related: bool = False
    positive_anchor_candidate: bool = False
    social_support_signal: bool = False
    high_stress_flag: bool = False


class MemorySummary(BaseModel):
    recent_checkin_count: int = 0
    dominant_negative_patterns: list[str] = Field(default_factory=list)
    dominant_positive_patterns: list[str] = Field(default_factory=list)
    recurring_triggers: list[str] = Field(default_factory=list)
    recurring_social_contexts: list[str] = Field(default_factory=list)
    last_seen_emotional_direction: str = "mixed"
    pattern_detected: bool = False


class EmotionalMemoryRecord(BaseModel):
    user_id: str
    transcript: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str = "en"
    normalized_state: NormalizedEmotionalState
    support_strategy: SupportStrategy
    topic_tags: list[str] = Field(default_factory=list)
    risk_level: str = "low"
    suggestion_given: bool = False
    response_provider: str = "unknown"
    response_mode: str
    support_metadata: dict[str, object] = Field(default_factory=dict)
    insight_features: InsightFeatures = Field(default_factory=InsightFeatures)


class WeeklyInsight(BaseModel):
    user_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    days_considered: int = 7
    period_start: datetime | None = None
    period_end: datetime | None = None
    total_checkins: int
    emotional_trend: str = "mixed"
    common_negative_triggers: list[str] = Field(default_factory=list)
    common_positive_anchors: list[str] = Field(default_factory=list)
    recurring_contexts: list[str] = Field(default_factory=list)
    stress_heavy_contexts: list[str] = Field(default_factory=list)
    recurring_relational_patterns: list[str] = Field(default_factory=list)
    dominant_emotions: list[str] = Field(default_factory=list)
    suggested_reflection_focus: str | None = None
    records_considered_for_insight: int = 0
    summary: str
    insight_summary_text: str
