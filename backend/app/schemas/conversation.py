import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class ConversationSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None

    @field_serializer("started_at", "ended_at")
    def serialize_datetime(self, value: datetime | None, _info: Any) -> str | None:
        return value.isoformat() if value else None


class ConversationSessionListResponse(BaseModel):
    user_id: str
    total: int
    limit: int
    offset: int
    items: list[ConversationSessionResponse]


class ConversationTurnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    text: str
    audio_path: str | None = None
    emotion_snapshot: dict[str, object] | None = None
    state_snapshot: dict[str, object] | None = None
    created_at: datetime

    @field_validator("emotion_snapshot", "state_snapshot", mode="before")
    @classmethod
    def parse_snapshot(cls, value: object) -> dict[str, object] | None:
        if value is None or isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                payload = json.loads(value)
            except json.JSONDecodeError:
                return None
            return payload if isinstance(payload, dict) else None
        return None

    @field_serializer("created_at")
    def serialize_turn_datetime(self, value: datetime, _info: Any) -> str:
        return value.isoformat()


class ConversationTurnListResponse(BaseModel):
    session_id: str
    total: int
    limit: int
    offset: int
    items: list[ConversationTurnResponse]


class ConversationTurnResultResponse(BaseModel):
    session_id: str
    user_turn: ConversationTurnResponse
    assistant_turn: ConversationTurnResponse
    final_transcript: str
    assistant_response: str
    emotion_analysis: dict[str, object]
    response_plan: dict[str, object]
    ai: dict[str, object]


class ConversationAudioFinalRequest(BaseModel):
    extension: str = ".webm"
    text_fallback: str | None = None


class ConversationTextTurnRequest(BaseModel):
    text: str = Field(min_length=1)
