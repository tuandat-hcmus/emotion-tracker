from pydantic import BaseModel, Field


class DemoAICoreRequest(BaseModel):
    text: str = Field(min_length=1)
    user_name: str | None = Field(default=None, max_length=80)
    context_tag: str | None = Field(default=None, max_length=80)


class DemoEmotionResponse(BaseModel):
    primary_emotion: str
    secondary_emotions: list[str] = Field(default_factory=list)
    emotion_label: str
    valence_score: float
    energy_score: float
    stress_score: float
    confidence: float
    provider_name: str
    response_mode: str


class DemoSupportResponse(BaseModel):
    empathetic_response: str
    gentle_suggestion: str | None = None
    safety_note: str | None = None
    provider_name: str = "template"


class DemoAICoreResponse(BaseModel):
    input_text: str
    language: str
    topic_tags: list[str] = Field(default_factory=list)
    risk_level: str
    risk_flags: list[str] = Field(default_factory=list)
    emotion: DemoEmotionResponse
    support: DemoSupportResponse
