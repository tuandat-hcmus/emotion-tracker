from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Emotion Voice Backend"
    main_language: str = "en"
    ai_render_language: str = "en"
    database_url: str = "sqlite:///./app.db"
    uploads_dir: str = "uploads"
    emotion_provider: str = "model_local"
    enable_canonical_models: bool = True
    enable_public_text_models: bool = True
    enable_text_emotion: bool = True
    enable_audio_emotion: bool = False
    enable_heuristic_fallback: bool = True
    hf_home: str | None = None
    model_cache_dir: str | None = None
    hf_token: str | None = None
    default_text_provider: str = "public"
    default_audio_provider: str = "sensevoice"
    default_fallback_provider: str = "multilingual"
    ai_core_demo_response_provider: str = "gemini"
    en_public_model_provider: str = "hf_pipeline"
    en_public_model_name: str = "SamLowe/roberta-base-go_emotions"
    en_secondary_model_name: str = "j-hartmann/emotion-english-distilroberta-base"
    en_canonical_model_dir: str = "backend/models/en_canonical_emotion"
    en_canonical_backbone: str = "roberta-base"
    vi_public_model_provider: str = "hf_pipeline"
    vi_public_model_name: str = "visolex/phobert-emotion"
    vi_canonical_model_dir: str = "backend/models/vi_canonical_emotion"
    vi_canonical_backbone: str = "visolex/phobert-emotion"
    zh_public_model_provider: str = "hf_pipeline"
    zh_public_model_name: str = "Johnson8187/Chinese-Emotion-Small"
    zh_canonical_model_dir: str = "backend/models/zh_canonical_emotion"
    zh_canonical_backbone: str = "Johnson8187/Chinese-Emotion-Small"
    multilingual_model_provider: str = "hf_pipeline"
    multilingual_model_name: str = "MilaNLProc/xlm-emo-t"
    enable_english_canonical_models: bool = True
    supported_en_models: str = "SamLowe/roberta-base-go_emotions,j-hartmann/emotion-english-distilroberta-base,j-hartmann/emotion-english-roberta-large"
    supported_vi_models: str = "visolex/phobert-emotion,uitnlp/visobert,vinai/phobert-large"
    supported_zh_models: str = "Johnson8187/Chinese-Emotion-Small,hfl/chinese-roberta-wwm-ext,Langboat/mengzi-bert-base"
    supported_multilingual_models: str = "MilaNLProc/xlm-emo-t"
    supported_audio_models: str = "SenseVoiceSmall"
    demo_locale: str = "en"
    enable_ai_core_demo: bool = False
    ai_core_demo_language: str = "en"
    ai_core_demo_use_canonical: bool = True
    ai_core_demo_disable_zh: bool = True
    text_model_en: str = "SamLowe/roberta-base-go_emotions"
    text_model_vi: str = "visolex/phobert-emotion"
    text_model_zh: str = "Johnson8187/Chinese-Emotion-Small"
    text_model_fallback: str = "MilaNLProc/xlm-emo-t"
    enable_canonical_emotion: bool = True
    canonical_model_root: str = "models"
    canonical_confidence_threshold: float = 0.58
    canonical_hybrid_weight: float = 0.7
    ai_confidence_threshold: float = 0.5
    ai_low_confidence_hybrid: bool = True
    audio_emotion_provider: str = "sensevoice"
    audio_emotion_model_name: str | None = "SenseVoiceSmall"
    audio_stt_provider: str = "existing"
    audio_use_text_transcript: bool = True
    ai_device: str = "cpu"
    ai_batch_size: int = 4
    use_mock_stt: bool = True
    use_mock_response: bool = True
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    stt_provider: str = "mock"
    response_provider: str = "mock"
    openai_text_model: str = "gpt-4o-mini"
    gemini_text_model: str = "gemini-2.5-flash"
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

    def split_csv(self, value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
