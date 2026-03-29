import logging

from app.services.ai_core.canonical_schema import (
    CANONICAL_EMOTIONS,
    canonical_dimensions,
    top_secondary_emotions,
)
from app.services.ai_core.schemas import AudioEmotionResult, CanonicalEmotionResult, TextEmotionResult

logger = logging.getLogger(__name__)

_K = 60  # standard RRF constant


def _rrf(
    ranked_lists: list[list[tuple[str, float]]],
    weights: list[float],
) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion over multiple ranked emotion lists.

    Returns a normalized ranked list of (label, score) pairs summing to 1.
    """
    totals: dict[str, float] = {label: 0.0 for label in CANONICAL_EMOTIONS}

    for ranked, weight in zip(ranked_lists, weights):
        scores = dict(ranked)
        # Rank all canonical labels (fill missing with 0)
        all_sorted = sorted(
            [(label, scores.get(label, 0.0)) for label in CANONICAL_EMOTIONS],
            key=lambda x: x[1],
            reverse=True,
        )
        for rank_idx, (label, _) in enumerate(all_sorted, start=1):
            totals[label] += weight * (1.0 / (_K + rank_idx))

    total = sum(totals.values()) or 1.0
    normalized = [(label, round(score / total, 4)) for label, score in totals.items()]
    return sorted(normalized, key=lambda x: x[1], reverse=True)


def fuse_emotion_signals(
    text_result: TextEmotionResult,
    audio_result: AudioEmotionResult | None = None,
    face_result: AudioEmotionResult | None = None,
) -> CanonicalEmotionResult:
    """Fuse text, audio, and face emotion via Reciprocal Rank Fusion.

    Falls back to text-only when audio/face results are absent (identical to existing behaviour).
    """
    ranked_lists: list[list[tuple[str, float]]] = [text_result.ranked_emotions]
    raw_weights: list[float] = [1.0]
    fusion_weights: dict[str, float] = {"text": 1.0, "audio": 0.0, "face": 0.0}

    if audio_result is not None and audio_result.ranked_emotions:
        ranked_lists.append(audio_result.ranked_emotions)
        raw_weights.append(1.0)
        fusion_weights = {"text": 0.50, "audio": 0.50, "face": 0.0}

    if face_result is not None and face_result.ranked_emotions:
        ranked_lists.append(face_result.ranked_emotions)
        raw_weights.append(1.0)
        if audio_result is not None:
            fusion_weights = {"text": 0.40, "audio": 0.35, "face": 0.25}
        else:
            fusion_weights = {"text": 0.60, "audio": 0.0, "face": 0.40}

    # Build normalized weight list matching the order of ranked_lists
    modality_keys = (
        ["text"]
        + (["audio"] if audio_result is not None and audio_result.ranked_emotions else [])
        + (["face"] if face_result is not None and face_result.ranked_emotions else [])
    )
    total_w = sum(fusion_weights[k] for k in modality_keys) or 1.0
    weights = [fusion_weights[k] / total_w for k in modality_keys]

    fused = _rrf(ranked_lists, weights)
    valence, energy, stress = canonical_dimensions(fused)

    source = "fused" if (audio_result is not None or face_result is not None) else "text"

    return CanonicalEmotionResult(
        language=text_result.language,
        primary_emotion=fused[0][0],
        secondary_emotions=top_secondary_emotions(fused, fused[0][0]),
        valence=valence,
        energy=energy,
        stress=stress,
        confidence=fused[0][1],
        source=source,  # type: ignore[arg-type]
        raw_model_labels=[label for label, score in fused if score > 0],
        provider_name=text_result.provider_name,
        source_metadata={
            **text_result.source_metadata,
            "text": text_result.model_dump(),
            "audio": audio_result.model_dump() if audio_result else None,
            "face": face_result.model_dump() if face_result else None,
            "fusion_weights": fusion_weights,
        },
    )
