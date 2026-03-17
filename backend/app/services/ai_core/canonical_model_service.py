from functools import lru_cache
import json
import os
from pathlib import Path

from app.core.config import get_settings
from app.services.ai_core.canonical_schema import CANONICAL_EMOTIONS, canonical_dimensions
from app.services.ai_core.public_text_emotion_service import augment_text_with_public_features, infer_public_text_emotion
from app.services.ai_core.model_registry import get_model_spec
from app.services.ai_core.schemas import TextEmotionResult


PROJECT_ROOT = Path(__file__).resolve().parents[3]
METADATA_NAME = "metadata.json"


def _language_artifact_dir(language: str, variant: str = "active") -> Path:
    settings = get_settings()
    if variant == "lightweight":
        return PROJECT_ROOT / "models" / f"{language}_canonical_emotion_lightweight"
    configured_map = {
        "en": settings.en_canonical_model_dir,
        "vi": settings.vi_canonical_model_dir,
        "zh": settings.zh_canonical_model_dir,
    }
    configured = configured_map.get(language, settings.en_canonical_model_dir)
    configured_path = Path(configured)
    if configured_path.is_absolute():
        return configured_path
    return PROJECT_ROOT.parent / configured_path if str(configured_path).startswith("backend/") else PROJECT_ROOT / configured_path


def canonical_model_available(language: str, variant: str = "active") -> bool:
    artifact_dir = _language_artifact_dir(language, variant=variant)
    return (artifact_dir / METADATA_NAME).exists() and (
        (artifact_dir / "model.joblib").exists() or (artifact_dir / "transformer_model").exists()
    )


@lru_cache(maxsize=8)
def _load_metadata(language: str, variant: str = "active") -> dict[str, object]:
    artifact_dir = _language_artifact_dir(language, variant=variant)
    return json.loads((artifact_dir / METADATA_NAME).read_text(encoding="utf-8"))


@lru_cache(maxsize=8)
def _load_lightweight_artifact(language: str, variant: str = "active") -> dict[str, object]:
    import joblib

    artifact_dir = _language_artifact_dir(language, variant=variant)
    return joblib.load(artifact_dir / "model.joblib")


@lru_cache(maxsize=8)
def _load_transformer_artifact(language: str, variant: str = "active") -> dict[str, object]:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    artifact_dir = _language_artifact_dir(language, variant=variant) / "transformer_model"
    local_files_only = os.getenv("HF_HUB_OFFLINE") == "1"
    tokenizer = AutoTokenizer.from_pretrained(artifact_dir, local_files_only=local_files_only)
    model = AutoModelForSequenceClassification.from_pretrained(artifact_dir, local_files_only=local_files_only)
    return {"tokenizer": tokenizer, "model": model}


def _temperature_scale(probabilities: list[float], temperature: float) -> list[float]:
    if temperature <= 0:
        return probabilities
    scaled = [pow(max(probability, 1e-8), 1.0 / temperature) for probability in probabilities]
    total = sum(scaled) or 1.0
    return [value / total for value in scaled]


def _metadata_result(
    *,
    language: str,
    metadata: dict[str, object],
    ranked_emotions: list[tuple[str, float]],
    confidence: float,
    variant: str,
) -> TextEmotionResult:
    valence, energy, stress = canonical_dimensions(ranked_emotions)
    backbone_name = str(metadata.get("backbone_name", "unknown"))
    backbone_spec = get_model_spec(backbone_name)
    threshold = float(metadata.get("confidence_threshold", get_settings().ai_confidence_threshold))
    return TextEmotionResult(
        language=language,
        provider_name=f"{language}_canonical_emotion" if variant == "active" else f"{language}_canonical_emotion_lightweight",
        raw_model_labels=[f"{label}:{round(score, 4)}" for label, score in ranked_emotions],
        ranked_emotions=ranked_emotions,
        confidence=round(confidence, 2),
        source_metadata={
            "mode": "canonical_classifier",
            "artifact_dir": str(_language_artifact_dir(language, variant=variant)),
            "temperature": float(metadata.get("temperature", 1.0)),
            "confidence_threshold": threshold,
            "low_confidence": confidence < threshold,
            "coverage_passed": confidence >= threshold,
            "valence": valence,
            "energy": energy,
            "stress": stress,
            "backbone_name": backbone_name,
            "backbone_runtime_status": backbone_spec.runtime_status if backbone_spec is not None else "unknown",
            "label_schema_version": metadata.get("label_schema_version", "v1"),
            "training_mode": metadata.get("training_mode", "unknown"),
            "dataset_name": metadata.get("dataset_name", "seed"),
            "split_policy": metadata.get("split_policy", "unknown"),
            "labels": [label for label, _ in ranked_emotions if label in CANONICAL_EMOTIONS],
        },
    )


def infer_canonical_text_emotion(text: str, language: str, variant: str = "active") -> TextEmotionResult | None:
    if not canonical_model_available(language, variant=variant):
        return None

    metadata = _load_metadata(language, variant=variant)
    training_mode = str(metadata.get("training_mode", "lightweight_tfidf_head"))
    if training_mode.startswith("transformer"):
        import torch

        loaded = _load_transformer_artifact(language, variant=variant)
        tokenizer = loaded["tokenizer"]
        model = loaded["model"]
        model.eval()
        encoded = tokenizer(text, truncation=True, padding=True, max_length=256, return_tensors="pt")
        with torch.no_grad():
            logits = model(**encoded).logits[0]
        probabilities = torch.softmax(logits, dim=-1).tolist()
        labels = [str(model.config.id2label[idx]) for idx in range(len(probabilities))]
        calibrated = _temperature_scale(probabilities, float(metadata.get("temperature", 1.0)))
        ranked = sorted(zip(labels, calibrated, strict=False), key=lambda item: item[1], reverse=True)
        return _metadata_result(language=language, metadata=metadata, ranked_emotions=[(str(label), float(score)) for label, score in ranked], confidence=max(calibrated), variant=variant)

    artifact = _load_lightweight_artifact(language, variant=variant)
    augmented_text, _ = augment_text_with_public_features(text, forced_language=language)
    classifier = artifact["classifier"]
    labels = artifact["labels"]
    probabilities = list(classifier.predict_proba([augmented_text])[0])
    calibrated = _temperature_scale(probabilities, float(metadata.get("temperature", 1.0)))
    ranked = sorted(zip(labels, calibrated, strict=False), key=lambda item: item[1], reverse=True)
    return _metadata_result(language=language, metadata=metadata, ranked_emotions=[(str(label), float(score)) for label, score in ranked], confidence=max(calibrated), variant=variant)


def infer_with_hybrid_fallback(text: str, language: str) -> TextEmotionResult:
    canonical_result = infer_canonical_text_emotion(text, language, variant="active")
    if canonical_result is None:
        return infer_public_text_emotion(text, forced_language=language)

    settings = get_settings()
    threshold = float(canonical_result.source_metadata["confidence_threshold"])
    if canonical_result.confidence >= threshold or not settings.ai_low_confidence_hybrid:
        return canonical_result

    public_result = infer_public_text_emotion(text, forced_language=language)
    hybrid_weight = get_settings().canonical_hybrid_weight
    combined_scores: dict[str, float] = {}
    for emotion, score in canonical_result.ranked_emotions:
        combined_scores[emotion] = combined_scores.get(emotion, 0.0) + score * hybrid_weight
    for emotion, score in public_result.ranked_emotions:
        combined_scores[emotion] = combined_scores.get(emotion, 0.0) + score * (1.0 - hybrid_weight)
    ranked = sorted(combined_scores.items(), key=lambda item: item[1], reverse=True)
    return TextEmotionResult(
        language=language,
        provider_name=f"{canonical_result.provider_name}+{public_result.provider_name}",
        raw_model_labels=canonical_result.raw_model_labels + public_result.raw_model_labels,
        ranked_emotions=ranked,
        confidence=round(min(1.0, max(canonical_result.confidence, public_result.confidence)), 2),
        source_metadata={
            "mode": "canonical_hybrid",
            "canonical": canonical_result.model_dump(),
            "public": public_result.model_dump(),
            "low_confidence": True,
            "hybrid_weight": hybrid_weight,
            "coverage_passed": False,
            "valence": canonical_result.source_metadata["valence"],
            "energy": canonical_result.source_metadata["energy"],
            "stress": canonical_result.source_metadata["stress"],
        },
    )
