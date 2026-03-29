import logging

from app.services.ai_core.canonical_schema import top_secondary_emotions
from app.services.ai_core.schemas import CanonicalEmotionResult
from app.services.ai_core.text_emotion_service import emotion_dimensions, infer_text_emotion

logger = logging.getLogger(__name__)


def _result_dimensions(result) -> tuple[float, float, float]:
    meta = result.source_metadata
    if {"valence", "energy", "stress"} <= set(meta):
        return (round(float(meta["valence"]), 2), round(float(meta["energy"]), 2), round(float(meta["stress"]), 2))
    return emotion_dimensions(result.ranked_emotions)


def infer_emotion_signals(transcript: str, audio_path: str | None = None) -> CanonicalEmotionResult:
    text_result = infer_text_emotion(transcript)

    # Optionally enrich with audio prosody when enabled and an audio file is available
    audio_result = None
    if audio_path is not None:
        try:
            from app.core.config import get_settings
            if getattr(get_settings(), "audio_emotion_model_enabled", False):
                from app.services.ai_core.audio_emotion_service import infer_audio_emotion
                audio_result = infer_audio_emotion(audio_path)
        except Exception:
            logger.exception("fusion_service.audio_emotion_failed audio_path=%s", audio_path)

    if audio_result is not None:
        from app.services.ai_core.multimodal_fusion_service import fuse_emotion_signals
        return fuse_emotion_signals(text_result, audio_result=audio_result)

    # Text-only path (original behaviour, preserved unchanged)
    valence, energy, stress = _result_dimensions(text_result)
    ranked = text_result.ranked_emotions
    return CanonicalEmotionResult(
        language=text_result.language,
        primary_emotion=ranked[0][0],
        secondary_emotions=top_secondary_emotions(ranked, ranked[0][0]),
        valence=valence,
        energy=energy,
        stress=stress,
        confidence=text_result.confidence,
        source="text",
        raw_model_labels=text_result.raw_model_labels,
        provider_name=text_result.provider_name,
        source_metadata={
            **text_result.source_metadata,
            "text": text_result.model_dump(),
            "audio": None,
            "fusion_weights": {"text": 1.0, "audio": 0.0},
        },
    )
