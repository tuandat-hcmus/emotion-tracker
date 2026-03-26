from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class UploadCheckinResponse(BaseModel):
    entry_id: str
    status: str
    source_type: str = "voice"


class ProcessCheckinRequest(BaseModel):
    override_transcript: str | None = None


class CreateTextCheckinRequest(BaseModel):
    text: str = Field(min_length=1)
    session_type: str = "free"
    user_id: str | None = None


class TranscribeAudioResponse(BaseModel):
    transcript: str = Field(min_length=1)
    confidence: float | None = None
    provider: str


class EmotionAnalysisResponse(BaseModel):
    primary_label: str | None
    secondary_labels: list[str] = Field(default_factory=list)
    all_labels: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    threshold: float | None = None
    valence_score: float | None
    energy_score: float | None
    stress_score: float | None
    social_need_score: float | None
    confidence: float | None
    dominant_signals: list[str]
    context_tags: list[str] = Field(default_factory=list)
    enrichment_notes: list[str] = Field(default_factory=list)
    response_mode: str | None
    language: str | None = None
    source: str | None = None
    provider_name: str | None = None


class ResponsePlanResponse(BaseModel):
    opening_style: str
    acknowledgment_focus: str
    suggestion_allowed: bool
    suggestion_style: str
    suggestion_family: str | None = None
    quote_allowed: bool
    avoid_advice: bool
    tone: str
    max_sentences: int
    follow_up_question_allowed: bool
    response_variant: str | None = None
    response_mode: str | None = None
    evidence_bound: bool = True


class ResponseQuoteResponse(BaseModel):
    short_text: str
    tone: str
    source_type: str


class AIEmotionContractResponse(BaseModel):
    primary_label: str | None = None
    secondary_labels: list[str] = Field(default_factory=list)
    all_labels: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    threshold: float | None = None
    valence_score: float | None = None
    energy_score: float | None = None
    stress_score: float | None = None
    social_need_score: float | None = None
    confidence: float | None = None
    dominant_signals: list[str] = Field(default_factory=list)
    context_tags: list[str] = Field(default_factory=list)
    enrichment_notes: list[str] = Field(default_factory=list)
    response_mode: str | None = None
    language: str | None = None
    provider_name: str | None = None
    source: str | None = None


class AIRiskContractResponse(BaseModel):
    level: str | None = None
    flags: list[str] = Field(default_factory=list)


class AITopicsContractResponse(BaseModel):
    tags: list[str] = Field(default_factory=list)


class AIResponseContractResponse(BaseModel):
    plan: ResponsePlanResponse | None = None
    empathetic_text: str | None = None
    follow_up_question: str | None = None
    suggestion_text: str | None = None
    composed_text: str | None = None
    quote: ResponseQuoteResponse | None = None


class AIStateContractResponse(BaseModel):
    primary_label: str | None = None
    secondary_labels: list[str] = Field(default_factory=list)
    valence_score: float | None = None
    energy_score: float | None = None
    stress_score: float | None = None
    emotion_owner: str | None = None
    social_context: str | None = None
    event_type: str | None = None
    concern_target: str | None = None
    uncertainty: float | None = None
    confidence: float | None = None
    response_mode: str | None = None
    risk_level: str | None = None


class AIStrategyContractResponse(BaseModel):
    support_focus: str | None = None
    strategy_type: str | None = None
    suggestion_budget: str | None = None
    personalization_tone: str | None = None
    response_goal: str | None = None
    rationale: list[str] = Field(default_factory=list)


class AIInsightFeaturesContractResponse(BaseModel):
    is_negative_checkin: bool | None = None
    is_positive_checkin: bool | None = None
    work_trigger: bool | None = None
    relationship_strain: bool | None = None
    deadline_related: bool | None = None
    loneliness_related: bool | None = None
    positive_anchor_candidate: bool | None = None
    social_support_signal: bool | None = None
    high_stress_flag: bool | None = None


class AIMemoryContractResponse(BaseModel):
    recent_checkin_count: int | None = None
    dominant_negative_patterns: list[str] = Field(default_factory=list)
    dominant_positive_patterns: list[str] = Field(default_factory=list)
    recurring_triggers: list[str] = Field(default_factory=list)
    recurring_social_contexts: list[str] = Field(default_factory=list)
    last_seen_emotional_direction: str | None = None
    pattern_detected: bool | None = None
    insight_features: AIInsightFeaturesContractResponse | None = None


class AIContractResponse(BaseModel):
    emotion: AIEmotionContractResponse = Field(default_factory=AIEmotionContractResponse)
    risk: AIRiskContractResponse = Field(default_factory=AIRiskContractResponse)
    topics: AITopicsContractResponse = Field(default_factory=AITopicsContractResponse)
    response: AIResponseContractResponse = Field(default_factory=AIResponseContractResponse)
    state: AIStateContractResponse = Field(default_factory=AIStateContractResponse)
    strategy: AIStrategyContractResponse = Field(default_factory=AIStrategyContractResponse)
    memory: AIMemoryContractResponse = Field(default_factory=AIMemoryContractResponse)


class RespondPreviewRequest(BaseModel):
    transcript: str = Field(min_length=1)
    session_type: str | None = None
    override_risk_level: str | None = Field(default=None, pattern=r"^(low|medium|high)$")
    override_topic_tags: list[str] | None = None


class RespondPreviewResponse(BaseModel):
    emotion_analysis: EmotionAnalysisResponse
    topic_tags: list[str]
    risk_level: str
    risk_flags: list[str]
    response_plan: ResponsePlanResponse
    empathetic_response: str
    follow_up_question: str | None = None
    gentle_suggestion: str | None
    quote: ResponseQuoteResponse | None
    ai_response: str
    ai: AIContractResponse = Field(default_factory=AIContractResponse)


class ProcessAcceptedResponse(BaseModel):
    entry_id: str
    status: str
    message: str


class DeleteCheckinResponse(BaseModel):
    entry_id: str
    deleted: bool
    removed_audio: bool


class ProcessingAttemptItemResponse(BaseModel):
    id: str
    trigger_type: str
    provider_stt: str
    provider_response: str
    status: str
    used_override_transcript: bool
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None

    @field_serializer("started_at", "finished_at")
    def serialize_attempt_datetime(self, value: datetime | None, _info: Any) -> str | None:
        return value.isoformat() if value else None


class ProcessingAttemptListResponse(BaseModel):
    entry_id: str
    total: int
    items: list[ProcessingAttemptItemResponse]


class CheckinDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entry_id: str
    status: str
    user_id: str
    session_type: str
    source_type: str
    audio_path: str | None
    transcript_text: str | None
    transcript_confidence: float | None
    transcript_source: str | None = None
    transcript_provider: str | None = None
    ai_analysis_complete: bool = False
    latest_attempt_status: str | None = None
    processing_started_at: datetime | None = None
    processing_finished_at: datetime | None = None
    ai_response: str | None
    primary_label: str | None
    secondary_labels: list[str] = Field(default_factory=list)
    all_labels: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    threshold: float | None = None
    valence_score: float | None
    energy_score: float | None
    stress_score: float | None
    social_need_score: float | None = None
    confidence: float | None = None
    dominant_signals: list[str] = Field(default_factory=list)
    context_tags: list[str] = Field(default_factory=list)
    enrichment_notes: list[str] = Field(default_factory=list)
    response_mode: str | None = None
    language: str | None = None
    source: str | None = None
    provider_name: str | None = None
    empathetic_response: str | None = None
    follow_up_question: str | None = None
    gentle_suggestion: str | None = None
    quote_text: str | None = None
    response_metadata: dict[str, Any] | None = None
    topic_tags: list[str]
    risk_level: str | None = None
    risk_flags: list[str]
    ai: AIContractResponse = Field(default_factory=AIContractResponse)
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at", "processing_started_at", "processing_finished_at")
    def serialize_datetime(self, value: datetime | None, _info: Any) -> str | None:
        return value.isoformat() if value else None
