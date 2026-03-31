from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.services.ai_core.canonical_schema import canonical_dimensions
from app.services.ai_core.language_service import detect_language, normalize_language_code
from app.services.ai_core.schemas import TextEmotionResult

logger = logging.getLogger(__name__)

ARTIFACT_META_NAME = "artifact_meta.json"
LOCAL_PROVIDER_NAME = "local_xlmr"


@dataclass(frozen=True)
class LocalEmotionModelBundle:
    tokenizer: object
    model: object
    device: object
    artifact_meta: dict[str, object]
    model_dir: str


def _prepare_runtime_environment() -> None:
    os.environ.setdefault("USE_TF", "0")
    os.environ.setdefault("USE_FLAX", "0")
    os.environ.setdefault("TRANSFORMERS_NO_TF", "1")


def _resolve_device(device_name: str):
    import torch

    normalized = device_name.strip().lower()
    if normalized in {"", "auto"}:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if normalized == "cuda" and not torch.cuda.is_available():
        return torch.device("cpu")
    return torch.device(normalized)


@lru_cache(maxsize=4)
def _load_local_model_bundle(model_dir: str, device_name: str) -> LocalEmotionModelBundle:
    _prepare_runtime_environment()
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_path = Path(model_dir).resolve()
    logger.info("emotion_provider=%s loading from resolved path=%s", LOCAL_PROVIDER_NAME, model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"emotion_provider={LOCAL_PROVIDER_NAME} model directory not found: {model_path}. "
            "Ensure the model files are mounted or downloaded before starting the service."
        )

    artifact_meta_path = model_path / ARTIFACT_META_NAME
    if not artifact_meta_path.exists():
        raise FileNotFoundError(
            f"emotion_provider={LOCAL_PROVIDER_NAME} missing required file: {artifact_meta_path}. "
            f"Directory contents: {[p.name for p in model_path.iterdir()]}"
        )

    artifact_meta = json.loads(artifact_meta_path.read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    device = _resolve_device(device_name)
    model.to(device)
    model.eval()
    logger.info("emotion_provider=%s model_dir=%s device=%s labels=%s", LOCAL_PROVIDER_NAME, model_path, device, artifact_meta.get("labels"))
    return LocalEmotionModelBundle(
        tokenizer=tokenizer,
        model=model,
        device=device,
        artifact_meta=artifact_meta,
        model_dir=str(model_path),
    )


def _resolved_threshold(artifact_meta: dict[str, object], threshold_override: float | None) -> float:
    if threshold_override is not None:
        return float(threshold_override)
    return float(artifact_meta["threshold"])


def infer_local_text_emotion(text: str) -> TextEmotionResult:
    _prepare_runtime_environment()
    import torch

    settings = get_settings()
    bundle = _load_local_model_bundle(settings.emotion_model_dir, settings.emotion_model_device)
    artifact_meta = bundle.artifact_meta
    labels = [str(label) for label in artifact_meta["labels"]]
    threshold = _resolved_threshold(artifact_meta, settings.emotion_model_threshold)
    max_length = int(artifact_meta["max_length"])

    encoded = bundle.tokenizer(
        text,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    encoded = {key: value.to(bundle.device) for key, value in encoded.items()}

    with torch.no_grad():
        logits = bundle.model(**encoded).logits[0]
        probabilities = torch.sigmoid(logits).detach().cpu().tolist()

    sorted_scores = sorted(
        [(labels[index], float(probability)) for index, probability in enumerate(probabilities)],
        key=lambda item: item[1],
        reverse=True,
    )
    predicted_labels = [label for label, score in sorted_scores if score >= threshold]
    scores = {label: 0.0 for label in labels}
    for label, score in sorted_scores:
        scores[label] = round(score, 4)
    ranked_emotions = sorted(
        [(label, float(scores[label])) for label in labels],
        key=lambda item: item[1],
        reverse=True,
    )

    return TextEmotionResult(
        language=normalize_language_code(detect_language(text)),
        provider_name=LOCAL_PROVIDER_NAME,
        raw_model_labels=predicted_labels,
        ranked_emotions=ranked_emotions,
        confidence=round(sorted_scores[0][1], 4),
        source_metadata={
            "mode": "local_hf_multilabel",
            "model_dir": bundle.model_dir,
            "model_name": str(artifact_meta.get("model_name", LOCAL_PROVIDER_NAME)),
            "threshold": threshold,
            "max_length": max_length,
            "device": str(bundle.device),
            "labels": labels,
            "scores": scores,
            "predicted_labels": predicted_labels,
            "ranked_labels": [[label, round(score, 4)] for label, score in sorted_scores],
            "valence": canonical_dimensions(ranked_emotions)[0],
            "energy": canonical_dimensions(ranked_emotions)[1],
            "stress": canonical_dimensions(ranked_emotions)[2],
        },
    )
