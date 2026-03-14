from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Emotion Voice Backend"
    database_url: str = "sqlite:///./app.db"
    uploads_dir: str = "uploads"
    use_mock_stt: bool = True
    use_mock_response: bool = True
    openai_api_key: str | None = None
    stt_provider: str = "mock"
    response_provider: str = "mock"
    openai_text_model: str = "gpt-4o-mini"
    openai_audio_model: str = "gpt-4o-mini-transcribe"
    openai_request_timeout_seconds: float = 30.0
    max_upload_mb: int = 20
    allowed_audio_extensions: str = ".wav,.mp3,.m4a,.ogg,.webm"
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    auth_optional_for_dev: bool = True
    enable_dev_seed_endpoints: bool = False
    db_echo: bool = False
    auto_create_tables_for_dev: bool = True
    backend_cors_origins: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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
