from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class UploadCheckinResponse(BaseModel):
    entry_id: str
    status: str


class ProcessCheckinRequest(BaseModel):
    override_transcript: str | None = None


class EmotionAnalysisResponse(BaseModel):
    emotion_label: str | None
    valence_score: float | None
    energy_score: float | None
    stress_score: float | None
    social_need_score: float | None
    confidence: float | None
    dominant_signals: list[str]
    response_mode: str | None
    language: str | None = None
    primary_emotion: str | None = None
    secondary_emotions: list[str] = Field(default_factory=list)
    source: str | None = None
    raw_model_labels: list[str] = Field(default_factory=list)
    provider_name: str | None = None


class ResponsePlanResponse(BaseModel):
    opening_style: str
    acknowledgment_focus: str
    suggestion_allowed: bool
    suggestion_style: str
    quote_allowed: bool
    avoid_advice: bool
    tone: str
    max_sentences: int


class ResponseQuoteResponse(BaseModel):
    short_text: str
    tone: str
    source_type: str


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
    gentle_suggestion: str | None
    quote: ResponseQuoteResponse | None
    ai_response: str


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
    audio_path: str
    transcript_text: str | None
    transcript_confidence: float | None
    ai_response: str | None
    emotion_label: str | None
    valence_score: float | None
    energy_score: float | None
    stress_score: float | None
    social_need_score: float | None = None
    confidence: float | None = None
    dominant_signals: list[str] = Field(default_factory=list)
    response_mode: str | None = None
    language: str | None = None
    primary_emotion: str | None = None
    secondary_emotions: list[str] = Field(default_factory=list)
    source: str | None = None
    raw_model_labels: list[str] = Field(default_factory=list)
    provider_name: str | None = None
    empathetic_response: str | None = None
    gentle_suggestion: str | None = None
    quote_text: str | None = None
    response_metadata: dict[str, Any] | None = None
    topic_tags: list[str]
    risk_level: str | None = None
    risk_flags: list[str]
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime, _info: Any) -> str:
        return value.isoformat()
