from pydantic import BaseModel, Field


class DemoAICoreRequest(BaseModel):
    text: str = Field(min_length=1)
    user_name: str | None = Field(default=None, max_length=80)
    context_tag: str | None = Field(default=None, max_length=80)


class DemoEmotionResponse(BaseModel):
    primary_label: str
    secondary_labels: list[str] = Field(default_factory=list)
    all_labels: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    threshold: float | None = None
    valence_score: float
    energy_score: float
    stress_score: float
    confidence: float
    provider_name: str
    source: str = "text"
    dominant_signals: list[str] = Field(default_factory=list)
    context_tags: list[str] = Field(default_factory=list)
    response_mode: str

    @property
    def primary_emotion(self) -> str:
        if self.primary_label == "fear":
            if "overwhelm_load" in self.dominant_signals:
                return "overwhelm"
            return "anxiety"
        if self.primary_label == "joy":
            if "gratitude_warmth" in self.dominant_signals:
                return "gratitude"
            if "pride_growth" in self.dominant_signals:
                return "pride"
        if self.primary_label == "sadness" and "connection_need" in self.dominant_signals:
            return "loneliness"
        return self.primary_label

    @property
    def secondary_emotions(self) -> list[str]:
        return list(
            DemoEmotionResponse(
                primary_label=label,
                secondary_labels=[],
                all_labels=[],
                scores={},
                threshold=self.threshold,
                valence_score=self.valence_score,
                energy_score=self.energy_score,
                stress_score=self.stress_score,
                confidence=self.confidence,
                provider_name=self.provider_name,
                source=self.source,
                dominant_signals=self.dominant_signals,
                context_tags=self.context_tags,
                response_mode=self.response_mode,
            ).primary_emotion
            for label in self.secondary_labels
        )

    @property
    def emotion_label(self) -> str:
        mapping = {
            "anger": "anger",
            "disgust": "disgust",
            "fear": "lo lắng",
            "joy": "joy",
            "sadness": "sadness",
            "surprise": "surprise",
            "neutral": "neutral",
        }
        return mapping.get(self.primary_label, self.primary_label)


class DemoSupportResponse(BaseModel):
    empathetic_response: str
    gentle_suggestion: str | None = None
    safety_note: str | None = None
    provider_name: str = "template"


class DemoRenderDebugResponse(BaseModel):
    selected_provider: str
    gemini_call_attempted: bool = False
    gemini_call_succeeded: bool = False
    fallback_used: bool = False
    fallback_reason: str | None = None
    error_stage: str | None = None
    response_parse_status: str | None = None
    validation_error_summary: str | None = None


class DemoNormalizedStateResponse(BaseModel):
    primary_emotion: str
    secondary_emotions: list[str] = Field(default_factory=list)
    valence: float
    energy: float
    stress: float
    emotion_owner: str
    social_context: str
    event_type: str
    concern_target: str | None = None
    uncertainty: float
    confidence: float
    response_mode: str
    risk_level: str


class DemoSupportStrategyResponse(BaseModel):
    support_focus: str
    strategy_type: str
    suggestion_budget: str
    personalization_tone: str
    response_goal: str
    rationale: list[str] = Field(default_factory=list)


class DemoMemorySummaryResponse(BaseModel):
    recent_checkin_count: int = 0
    dominant_negative_patterns: list[str] = Field(default_factory=list)
    dominant_positive_patterns: list[str] = Field(default_factory=list)
    recurring_triggers: list[str] = Field(default_factory=list)
    recurring_social_contexts: list[str] = Field(default_factory=list)
    last_seen_emotional_direction: str = "mixed"
    pattern_detected: bool = False


class DemoInsightFeaturesResponse(BaseModel):
    is_negative_checkin: bool = False
    is_positive_checkin: bool = False
    work_trigger: bool = False
    relationship_strain: bool = False
    deadline_related: bool = False
    loneliness_related: bool = False
    positive_anchor_candidate: bool = False
    social_support_signal: bool = False
    high_stress_flag: bool = False


class DemoAICoreDetailsResponse(BaseModel):
    normalized_state: DemoNormalizedStateResponse
    support_strategy: DemoSupportStrategyResponse
    memory_summary: DemoMemorySummaryResponse | None = None
    insight_features: DemoInsightFeaturesResponse | None = None
    memory_records_used: int = 0


class DemoWeeklyInsightResponse(BaseModel):
    period_start: str | None = None
    period_end: str | None = None
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
    insight_summary_text: str | None = None


class DemoAICoreResponse(BaseModel):
    input_text: str
    language: str
    topic_tags: list[str] = Field(default_factory=list)
    risk_level: str
    risk_flags: list[str] = Field(default_factory=list)
    emotion: DemoEmotionResponse
    support: DemoSupportResponse
    ai_core: DemoAICoreDetailsResponse | None = None
    debug: DemoRenderDebugResponse | None = None
