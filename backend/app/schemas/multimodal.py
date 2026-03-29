from typing import Any

from pydantic import BaseModel


class CreateMultimodalSessionResponse(BaseModel):
    session_id: str
    user_id: str
    status: str
    started_at: str


class EndMultimodalSessionRequest(BaseModel):
    journal_entry_id: str | None = None


class MultimodalSessionDetailResponse(BaseModel):
    session_id: str
    user_id: str
    journal_entry_id: str | None
    status: str
    emotion_label: str | None
    valence_score: float | None
    energy_score: float | None
    stress_score: float | None
    emotion_confidence: float | None
    fusion_source: str | None
    fused_result: dict[str, Any] | None
    started_at: str
    ended_at: str | None
