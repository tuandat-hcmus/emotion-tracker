from app.services.ai_core.canonical_schema import top_secondary_emotions
from app.services.ai_core.schemas import CanonicalEmotionResult
from app.services.ai_core.text_emotion_service import emotion_dimensions, infer_text_emotion


def _result_dimensions(result) -> tuple[float, float, float]:
    meta = result.source_metadata
    if {"valence", "energy", "stress"} <= set(meta):
        return (round(float(meta["valence"]), 2), round(float(meta["energy"]), 2), round(float(meta["stress"]), 2))
    return emotion_dimensions(result.ranked_emotions)


def infer_emotion_signals(transcript: str, audio_path: str | None = None) -> CanonicalEmotionResult:
    del audio_path
    text_result = infer_text_emotion(transcript)
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
