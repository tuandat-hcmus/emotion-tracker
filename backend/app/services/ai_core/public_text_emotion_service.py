from functools import lru_cache
from math import isfinite
import os
from typing import Any

from app.core.config import get_settings
from app.services.ai_core.adapters import adapt_ranked_labels, sorted_unique_emotions
from app.services.ai_core.canonical_schema import canonical_dimensions
from app.services.ai_core.language_service import detect_language
from app.services.ai_core.model_download import get_model_status
from app.services.ai_core.model_registry import ModelSpec, get_model_spec, selected_public_model
from app.services.ai_core.schemas import TextEmotionResult
from app.services.provider_errors import ProviderExecutionError


_FALLBACK_EMOTION_BY_SENTIMENT = {
    "positive": "joy",
    "negative": "sadness",
    "neutral": "neutral",
}


def _build_heuristic_fallback_result(text: str, language: str, *, reason: str | None = None) -> TextEmotionResult:
    normalized = text.casefold()
    ranked_emotions: list[tuple[str, float]] = []
    keyword_map = {
        "loneliness": ("cô đơn", "mot minh", "một mình", "khong ai", "孤独", "寂寞", "alone", "lonely"),
        "overwhelm": ("deadline", "áp lực", "ap luc", "ngộp", "压力", "压得", "overwhelmed", "崩潰", "崩溃"),
        "anxiety": ("lo lắng", "lo lang", "bất an", "焦虑", "担心", "anxious", "tense"),
        "anger": ("bực", "tức", "ức chế", "生气", "愤怒", "angry", "frustrated"),
        "sadness": ("buồn", "that vong", "thất vọng", "难过", "伤心", "sad", "low", "empty", "numb", "tired", "mệt"),
        "gratitude": ("biết ơn", "cam kich", "感激", "感谢", "grateful", "gratitude", "thankful"),
        "joy": ("vui", "hạnh phúc", "开心", "快乐", "happy", "relieved", "hopeful", "proud"),
    }
    for emotion, tokens in keyword_map.items():
        score = sum(0.22 for token in tokens if token in normalized)
        if score > 0:
            ranked_emotions.append((emotion, min(score, 0.95)))
    if not ranked_emotions:
        sentiment = "negative" if any(token in normalized for token in ("sad", "stress", "buồn", "căng", "难过")) else "neutral"
        ranked_emotions.append((_FALLBACK_EMOTION_BY_SENTIMENT[sentiment], 0.45 if sentiment != "neutral" else 0.35))
    ranked = sorted_unique_emotions(ranked_emotions)
    valence, energy, stress = canonical_dimensions(ranked)
    return TextEmotionResult(
        language=language,
        provider_name="heuristic_fallback",
        raw_model_labels=[emotion for emotion, _ in ranked],
        ranked_emotions=ranked,
        confidence=round(min(max(ranked[0][1], 0.35), 0.78), 2),
        source_metadata={
            "mode": "heuristic_fallback",
            "low_confidence": True,
            "fallback_reason": reason,
            "valence": valence,
            "energy": energy,
            "stress": stress,
        },
    )


@lru_cache(maxsize=8)
def _load_text_pipeline(model_name: str, device: str, cache_dir: str | None):
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise ProviderExecutionError("Transformers is not installed for text emotion inference") from exc

    kwargs: dict[str, Any] = {
        "task": "text-classification",
        "model": model_name,
        "tokenizer": model_name,
    }
    if os.getenv("HF_HUB_OFFLINE") == "1":
        kwargs["local_files_only"] = True
    if cache_dir:
        kwargs["model_kwargs"] = {"cache_dir": cache_dir}
    if device == "cpu":
        kwargs["device"] = -1
    return pipeline(**kwargs)


def _coerce_predictions(raw_output: Any) -> list[dict[str, Any]]:
    if isinstance(raw_output, list) and raw_output and isinstance(raw_output[0], list):
        raw_output = raw_output[0]
    if not isinstance(raw_output, list):
        raise ProviderExecutionError("Unexpected text emotion model output")
    return [item for item in raw_output if isinstance(item, dict) and "label" in item]


def _infer_with_model(text: str, language: str, spec: ModelSpec) -> TextEmotionResult:
    settings = get_settings()
    if not spec.direct_inference:
        raise ProviderExecutionError(
            f"Configured model '{spec.model_name}' is backbone-only and requires fine-tuning before direct inference"
        )
    cache_dir = settings.model_cache_dir or settings.hf_home or None
    model_status = get_model_status(spec.model_name, key=f"{language}-public")
    if os.getenv("HF_HUB_OFFLINE") == "1" and not model_status.completed:
        raise ProviderExecutionError(
            f"Model cache for '{spec.model_name}' is incomplete in offline mode; incomplete_files={len(model_status.incomplete_files)}"
        )
    classifier = _load_text_pipeline(spec.model_name, settings.ai_device, cache_dir)
    raw_predictions = _coerce_predictions(classifier(text, top_k=None, truncation=True))
    filtered_predictions = [
        item for item in raw_predictions if isfinite(float(item.get("score", 0.0)))
    ]
    raw_labels, ranked, (valence, energy, stress) = adapt_ranked_labels(spec.model_name, filtered_predictions)
    if not ranked:
        raise ProviderExecutionError("Text emotion model returned no valid scores")
    confidence = round(min(max(ranked[0][1], 0.0), 1.0), 2)
    return TextEmotionResult(
        language=language,
        provider_name=spec.model_name,
        raw_model_labels=raw_labels,
        ranked_emotions=ranked,
        confidence=confidence,
        source_metadata={
            "mode": "transformers",
            "model_name": spec.model_name,
            "model_key": f"{language}-public",
            "cache_complete": model_status.completed,
            "family": spec.family,
            "task_type": spec.task_type,
            "valence": valence,
            "energy": energy,
            "stress": stress,
        },
    )


def infer_public_text_emotion(
    text: str,
    *,
    allow_heuristic_fallback: bool = True,
    forced_language: str | None = None,
) -> TextEmotionResult:
    settings = get_settings()
    language = forced_language or detect_language(text)
    if not settings.enable_public_text_models or settings.default_text_provider.strip().lower() != "public":
        return _build_heuristic_fallback_result(text, language, reason="public_text_models_disabled")
    spec = selected_public_model(language)
    if spec is None:
        return _build_heuristic_fallback_result(text, language, reason="no_registered_public_model")
    try:
        return _infer_with_model(text, language, spec)
    except Exception as exc:
        if not allow_heuristic_fallback or not settings.enable_heuristic_fallback:
            raise
        return _build_heuristic_fallback_result(text, language, reason=str(exc))


def infer_specific_public_text_emotion(
    text: str,
    *,
    language: str,
    model_name: str,
    allow_heuristic_fallback: bool = True,
) -> TextEmotionResult:
    spec = get_model_spec(model_name)
    if spec is None:
        return _build_heuristic_fallback_result(text, language, reason="unknown_model")
    try:
        return _infer_with_model(text, language, spec)
    except Exception as exc:
        if not allow_heuristic_fallback:
            raise
        return _build_heuristic_fallback_result(text, language, reason=str(exc))


def augment_text_with_public_features(
    text: str,
    result: TextEmotionResult | None = None,
    *,
    forced_language: str | None = None,
) -> tuple[str, TextEmotionResult]:
    public_result = result or infer_public_text_emotion(text, forced_language=forced_language)
    top_secondary = public_result.ranked_emotions[1][0] if len(public_result.ranked_emotions) > 1 else "none"
    meta = public_result.source_metadata
    stress = float(meta.get("stress", canonical_dimensions(public_result.ranked_emotions)[2]))
    energy = float(meta.get("energy", canonical_dimensions(public_result.ranked_emotions)[1]))
    stress_bucket = "high" if stress >= 0.65 else "mid" if stress >= 0.35 else "low"
    energy_bucket = "high" if energy >= 0.65 else "mid" if energy >= 0.35 else "low"
    augmented = (
        f"{text}\n"
        f"[weak_primary={public_result.ranked_emotions[0][0]}] "
        f"[weak_secondary={top_secondary}] "
        f"[weak_stress={stress_bucket}] "
        f"[weak_energy={energy_bucket}] "
        f"[weak_provider={public_result.provider_name}]"
    )
    return augmented, public_result
