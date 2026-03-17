from app.core.config import get_settings
from app.services.ai_core.language_service import detect_language
from app.services.ai_core.model_registry import selected_multilingual_model
from app.services.ai_core.public_text_emotion_service import infer_specific_public_text_emotion
from app.services.ai_core.schemas import TextEmotionResult
from app.services.provider_errors import ProviderExecutionError


def infer_multilingual_text_emotion(
    text: str,
    *,
    allow_heuristic_fallback: bool = True,
    forced_language: str | None = None,
) -> TextEmotionResult:
    settings = get_settings()
    language = forced_language or detect_language(text)
    spec = selected_multilingual_model()
    if settings.default_fallback_provider.strip().lower() != "multilingual" or spec is None:
        raise ProviderExecutionError("No multilingual fallback provider is configured")
    return infer_specific_public_text_emotion(
        text,
        language=language,
        model_name=spec.model_name,
        allow_heuristic_fallback=allow_heuristic_fallback,
    )
