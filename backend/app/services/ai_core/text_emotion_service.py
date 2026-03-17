from app.core.config import get_settings
from app.services.ai_core.canonical_model_service import infer_with_hybrid_fallback
from app.services.ai_core.canonical_schema import canonical_dimensions
from app.services.ai_core.language_service import detect_language
from app.services.ai_core.multilingual_text_emotion_service import infer_multilingual_text_emotion
from app.services.ai_core.public_text_emotion_service import infer_public_text_emotion
from app.services.ai_core.schemas import TextEmotionResult


def infer_text_emotion(text: str) -> TextEmotionResult:
    settings = get_settings()
    language = detect_language(text)

    if settings.enable_canonical_models and language in {"en", "vi", "zh"}:
        canonical = infer_with_hybrid_fallback(text, language)
        if canonical is not None:
            return canonical

    if settings.enable_public_text_models and language in {"en", "vi", "zh"}:
        public_result = infer_public_text_emotion(text, forced_language=language)
        if public_result.provider_name != "heuristic_fallback":
            return public_result

    try:
        return infer_multilingual_text_emotion(text, forced_language=language)
    except Exception:
        return infer_public_text_emotion(text, forced_language=language, allow_heuristic_fallback=True)


def infer_public_only_text_emotion(text: str) -> TextEmotionResult:
    language = detect_language(text)
    if language in {"en", "vi", "zh"}:
        return infer_public_text_emotion(text, forced_language=language)
    return infer_multilingual_text_emotion(text, forced_language=language)


def emotion_dimensions(ranked_emotions: list[tuple[str, float]]) -> tuple[float, float, float]:
    return canonical_dimensions(ranked_emotions)
