import logging

from app.core.config import get_settings
from app.services.ai_core.canonical_schema import canonical_dimensions
from app.services.ai_core.language_service import detect_language, normalize_language_code
from app.services.ai_core.local_emotion_model_service import infer_local_text_emotion
from app.services.ai_core.schemas import TextEmotionResult
from app.services.legacy_emotion_service import infer_legacy_emotion

logger = logging.getLogger(__name__)
FRONTEND_LABELS = ("anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral")


def _legacy_to_frontend_label(label: str) -> str:
    normalized = label.strip().casefold()
    mapping = {
        "anger": "anger",
        "disgust": "disgust",
        "fear": "fear",
        "anxiety": "fear",
        "overwhelm": "fear",
        "joy": "joy",
        "gratitude": "joy",
        "pride": "joy",
        "relief": "joy",
        "hope": "joy",
        "sadness": "sadness",
        "loneliness": "sadness",
        "emptiness": "sadness",
        "exhaustion": "sadness",
        "surprise": "surprise",
        "neutral": "neutral",
        "calm": "neutral",
    }
    return mapping.get(normalized, "neutral")


def _infer_text_emotion_with_model(text: str, language: str) -> TextEmotionResult:
    del language
    return infer_local_text_emotion(text)


def _infer_text_emotion_with_legacy_fallback(text: str, language: str) -> TextEmotionResult:
    raw = infer_legacy_emotion(text)
    frontend_scores = {label: 0.0 for label in FRONTEND_LABELS}
    for emotion, score in raw["ranked_emotions"]:
        frontend_label = _legacy_to_frontend_label(str(emotion))
        frontend_scores[frontend_label] += float(score)
    ranked_emotions = sorted(
        [(label, round(frontend_scores[label], 4)) for label in FRONTEND_LABELS],
        key=lambda item: item[1],
        reverse=True,
    )
    raw_model_labels = [label for label, score in ranked_emotions if score > 0]
    return TextEmotionResult(
        language=normalize_language_code(language),
        provider_name=str(raw["provider_name"]),
        raw_model_labels=raw_model_labels,
        ranked_emotions=ranked_emotions,
        confidence=max(frontend_scores.values()) if frontend_scores else float(raw["confidence"]),
        source_metadata={
            "mode": "legacy_fallback",
            "scores": {label: round(score, 4) for label, score in frontend_scores.items()},
            "predicted_labels": raw_model_labels,
            "valence": float(raw["valence"]),
            "energy": float(raw["energy"]),
            "stress": float(raw["stress"]),
        },
    )


def infer_text_emotion(text: str) -> TextEmotionResult:
    settings = get_settings()
    language = detect_language(text)
    if settings.emotion_model_enabled:
        try:
            return _infer_text_emotion_with_model(text, language)
        except Exception:
            logger.exception("emotion_provider=local_xlmr fallback=legacy language=%s", language)
            return _infer_text_emotion_with_legacy_fallback(text, language)
    return _infer_text_emotion_with_legacy_fallback(text, language)


def emotion_dimensions(ranked_emotions: list[tuple[str, float]]) -> tuple[float, float, float]:
    return canonical_dimensions(ranked_emotions)
