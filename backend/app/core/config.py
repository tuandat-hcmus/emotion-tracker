from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Emotion Voice Backend"
    main_language: str = "en"
    ai_render_language: str = "en"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/emotion_app"
    uploads_dir: str = "uploads"
    emotion_model_enabled: bool = True
    emotion_model_dir: str = "models/artifacts/emotion_xlmr"
    emotion_model_threshold: float | None = None
    emotion_model_device: str = "auto"
    ai_core_demo_response_provider: str = "gemini"
    ai_render_debug: bool = False
    gemini_enabled: bool = True
    demo_locale: str = "en"
    enable_ai_core_demo: bool = False
    ai_core_demo_language: str = "en"
    ai_core_demo_disable_zh: bool = True
    use_mock_stt: bool = True
    use_mock_response: bool = True
    openai_api_key: str | None = None
    gemini_api_key: str | None = Field(default=None, validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"))
    stt_provider: str = "mock"
    response_provider: str = "mock"
    response_default_language: str = "en"
    response_use_structured_output: bool = True
    openai_text_model: str = "gpt-4o-mini"
    gemini_text_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias=AliasChoices("GEMINI_TEXT_MODEL", "GEMINI_MODEL"),
    )
    openai_audio_model: str = "gpt-4o-mini-transcribe"
    openai_request_timeout_seconds: float = 30.0
    max_upload_mb: int = 20
    allowed_audio_extensions: str = ".wav,.mp3,.m4a,.ogg,.webm"
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    auth_optional_for_dev: bool = True
    enable_dev_seed_endpoints: bool = False
    db_echo: bool = False
    auto_create_tables_for_dev: bool = False
    backend_cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("emotion_model_threshold", mode="before")
    @classmethod
    def normalize_optional_threshold(cls, value: object) -> object:
        if value in {"", None}:
            return None
        return value

    def cors_origins(self) -> list[str]:
        if not self.backend_cors_origins.strip():
            return []
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
