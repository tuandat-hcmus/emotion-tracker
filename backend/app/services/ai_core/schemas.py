from typing import Literal

from pydantic import BaseModel, Field


EmotionSource = Literal["text", "audio", "fused"]


class CanonicalEmotionResult(BaseModel):
    language: str
    primary_emotion: str
    secondary_emotions: list[str] = Field(default_factory=list)
    valence: float
    energy: float
    stress: float
    confidence: float
    source: EmotionSource
    raw_model_labels: list[str] = Field(default_factory=list)
    provider_name: str
    source_metadata: dict[str, object] = Field(default_factory=dict)


class TextEmotionResult(BaseModel):
    language: str
    provider_name: str
    raw_model_labels: list[str] = Field(default_factory=list)
    ranked_emotions: list[tuple[str, float]] = Field(default_factory=list)
    confidence: float
    source_metadata: dict[str, object] = Field(default_factory=dict)


class AudioEmotionResult(BaseModel):
    provider_name: str
    raw_model_labels: list[str] = Field(default_factory=list)
    ranked_emotions: list[tuple[str, float]] = Field(default_factory=list)
    confidence: float
    source_metadata: dict[str, object] = Field(default_factory=dict)
