from app.services.ai_core.audio_emotion_service import infer_audio_emotion
from app.services.ai_core.canonical_schema import top_secondary_emotions
from app.services.ai_core.schemas import CanonicalEmotionResult
from app.services.ai_core.text_emotion_service import emotion_dimensions, infer_text_emotion


def _result_dimensions(result) -> tuple[float, float, float]:
    meta = result.source_metadata
    if {"valence", "energy", "stress"} <= set(meta):
        return (round(float(meta["valence"]), 2), round(float(meta["energy"]), 2), round(float(meta["stress"]), 2))
    return emotion_dimensions(result.ranked_emotions)


def infer_emotion_signals(transcript: str, audio_path: str | None = None) -> CanonicalEmotionResult:
    text_result = infer_text_emotion(transcript)
    audio_result = infer_audio_emotion(audio_path)

    if audio_result is None:
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
                "text": text_result.model_dump(),
                "audio": None,
                "fusion_weights": {"text": 1.0, "audio": 0.0},
            },
        )

    weighted_rank: dict[str, float] = {}
    for emotion, score in text_result.ranked_emotions:
        weighted_rank[emotion] = weighted_rank.get(emotion, 0.0) + score * 0.7
    for emotion, score in audio_result.ranked_emotions:
        weighted_rank[emotion] = weighted_rank.get(emotion, 0.0) + score * 0.3

    ranked = sorted(weighted_rank.items(), key=lambda item: item[1], reverse=True)
    valence_text, energy_text, stress_text = _result_dimensions(text_result)
    valence_audio, energy_audio, stress_audio = _result_dimensions(audio_result)
    return CanonicalEmotionResult(
        language=text_result.language,
        primary_emotion=ranked[0][0],
        secondary_emotions=top_secondary_emotions(ranked, ranked[0][0]),
        valence=round(valence_text * 0.7 + valence_audio * 0.3, 2),
        energy=round(energy_text * 0.7 + energy_audio * 0.3, 2),
        stress=round(stress_text * 0.7 + stress_audio * 0.3, 2),
        confidence=round(min(1.0, text_result.confidence * 0.7 + audio_result.confidence * 0.3), 2),
        source="fused",
        raw_model_labels=text_result.raw_model_labels + audio_result.raw_model_labels,
        provider_name=f"{text_result.provider_name}+{audio_result.provider_name}",
        source_metadata={
            "text": text_result.model_dump(),
            "audio": audio_result.model_dump(),
            "fusion_weights": {"text": 0.7, "audio": 0.3},
        },
    )
