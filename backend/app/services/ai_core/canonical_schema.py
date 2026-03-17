from collections.abc import Sequence
from enum import StrEnum


class CanonicalEmotion(StrEnum):
    JOY = "joy"
    SADNESS = "sadness"
    ANXIETY = "anxiety"
    ANGER = "anger"
    OVERWHELM = "overwhelm"
    GRATITUDE = "gratitude"
    LONELINESS = "loneliness"
    NEUTRAL = "neutral"


CANONICAL_EMOTIONS: tuple[str, ...] = tuple(item.value for item in CanonicalEmotion)

CANONICAL_DIMENSION_PRIORS: dict[str, tuple[float, float, float]] = {
    CanonicalEmotion.JOY.value: (0.76, 0.66, 0.12),
    CanonicalEmotion.GRATITUDE.value: (0.7, 0.38, 0.1),
    CanonicalEmotion.SADNESS.value: (-0.56, 0.22, 0.36),
    CanonicalEmotion.LONELINESS.value: (-0.62, 0.16, 0.48),
    CanonicalEmotion.ANXIETY.value: (-0.42, 0.74, 0.78),
    CanonicalEmotion.OVERWHELM.value: (-0.5, 0.82, 0.88),
    CanonicalEmotion.ANGER.value: (-0.58, 0.76, 0.74),
    CanonicalEmotion.NEUTRAL.value: (0.0, 0.34, 0.16),
}

_ALIASES = {
    "joy": CanonicalEmotion.JOY.value,
    "happy": CanonicalEmotion.JOY.value,
    "happiness": CanonicalEmotion.JOY.value,
    "enjoyment": CanonicalEmotion.JOY.value,
    "pride": CanonicalEmotion.JOY.value,
    "relief": CanonicalEmotion.JOY.value,
    "hope": CanonicalEmotion.JOY.value,
    "gratitude": CanonicalEmotion.GRATITUDE.value,
    "grateful": CanonicalEmotion.GRATITUDE.value,
    "thankful": CanonicalEmotion.GRATITUDE.value,
    "sadness": CanonicalEmotion.SADNESS.value,
    "sad": CanonicalEmotion.SADNESS.value,
    "emptiness": CanonicalEmotion.SADNESS.value,
    "exhaustion": CanonicalEmotion.SADNESS.value,
    "anxiety": CanonicalEmotion.ANXIETY.value,
    "fear": CanonicalEmotion.ANXIETY.value,
    "concerned": CanonicalEmotion.ANXIETY.value,
    "worry": CanonicalEmotion.ANXIETY.value,
    "overwhelm": CanonicalEmotion.OVERWHELM.value,
    "stress": CanonicalEmotion.OVERWHELM.value,
    "anger": CanonicalEmotion.ANGER.value,
    "disgust": CanonicalEmotion.ANGER.value,
    "loneliness": CanonicalEmotion.LONELINESS.value,
    "lonely": CanonicalEmotion.LONELINESS.value,
    "neutral": CanonicalEmotion.NEUTRAL.value,
    "calm": CanonicalEmotion.NEUTRAL.value,
    "questioning": CanonicalEmotion.NEUTRAL.value,
    "surprise": CanonicalEmotion.NEUTRAL.value,
    "other": CanonicalEmotion.NEUTRAL.value,
}


def canonicalize_emotion(label: str) -> str:
    normalized = label.strip().casefold().replace("_", " ").replace("-", " ")
    return _ALIASES.get(normalized, CanonicalEmotion.NEUTRAL.value)


def canonical_dimensions(ranked_emotions: Sequence[tuple[str, float]]) -> tuple[float, float, float]:
    total_weight = sum(score for _, score in ranked_emotions) or 1.0
    valence = sum(CANONICAL_DIMENSION_PRIORS.get(emotion, CANONICAL_DIMENSION_PRIORS["neutral"])[0] * score for emotion, score in ranked_emotions) / total_weight
    energy = sum(CANONICAL_DIMENSION_PRIORS.get(emotion, CANONICAL_DIMENSION_PRIORS["neutral"])[1] * score for emotion, score in ranked_emotions) / total_weight
    stress = sum(CANONICAL_DIMENSION_PRIORS.get(emotion, CANONICAL_DIMENSION_PRIORS["neutral"])[2] * score for emotion, score in ranked_emotions) / total_weight
    return (
        round(max(-1.0, min(1.0, valence)), 2),
        round(max(0.0, min(1.0, energy)), 2),
        round(max(0.0, min(1.0, stress)), 2),
    )


def top_secondary_emotions(ranked_emotions: Sequence[tuple[str, float]], primary_emotion: str, limit: int = 2) -> list[str]:
    secondary: list[str] = []
    for emotion, _ in ranked_emotions:
        if emotion == primary_emotion or emotion in secondary:
            continue
        secondary.append(emotion)
        if len(secondary) >= limit:
            break
    return secondary
