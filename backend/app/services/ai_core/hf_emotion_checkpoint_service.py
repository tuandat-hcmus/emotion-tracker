from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ARTIFACT_CONFIG_NAME = "goemotions_baseline_config.json"


@dataclass(frozen=True)
class EmotionLabelScore:
    label: str
    probability: float


@dataclass(frozen=True)
class EmotionCheckpointPrediction:
    top_labels: list[EmotionLabelScore]
    probabilities: dict[str, float]
    threshold: float
    model_name: str


def _prepare_runtime_environment() -> None:
    os.environ.setdefault("USE_TF", "0")
    os.environ.setdefault("USE_FLAX", "0")
    os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")


@lru_cache(maxsize=4)
def _load_bundle(model_dir: str) -> tuple[object, object, dict[str, object]]:
    _prepare_runtime_environment()
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    path = Path(model_dir)
    config = json.loads((path / ARTIFACT_CONFIG_NAME).read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path)
    model.eval()
    return tokenizer, model, config


def predict_checkpoint_emotions(
    text: str,
    *,
    model_dir: str,
    threshold: float | None = None,
    top_k: int = 5,
) -> EmotionCheckpointPrediction:
    _prepare_runtime_environment()
    import torch

    tokenizer, model, config = _load_bundle(model_dir)
    resolved_threshold = float(threshold if threshold is not None else config["training"]["threshold"])
    encoded = tokenizer(text, truncation=True, padding=True, max_length=int(config["training"]["max_length"]), return_tensors="pt")
    with torch.no_grad():
        logits = model(**encoded).logits[0]
        probabilities_tensor = torch.sigmoid(logits).cpu()

    labels = config["label_names"]
    probabilities = {label: round(float(probabilities_tensor[idx]), 4) for idx, label in enumerate(labels)}
    ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    filtered = [(label, score) for label, score in ranked if score >= resolved_threshold]
    if not filtered:
        filtered = ranked[:top_k]
    top_labels = [EmotionLabelScore(label=label, probability=score) for label, score in filtered[:top_k]]
    return EmotionCheckpointPrediction(
        top_labels=top_labels,
        probabilities=probabilities,
        threshold=resolved_threshold,
        model_name=str(config["training"]["model_name"]),
    )
