from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from datasets import Dataset, DatasetDict, load_dataset
from sklearn.metrics import f1_score, precision_score, recall_score


GOEMOTIONS_DATASET_NAME = "go_emotions"
GOEMOTIONS_CONFIG = "raw"
GOEMOTIONS_REPO_ID = "monologg/distilroberta-base-goemotions-style"
DEFAULT_CPU_BACKBONE = "distilroberta-base"
DEFAULT_GPU_BACKBONE = "roberta-base"
DEFAULT_THRESHOLD = 0.35
DEFAULT_THRESHOLD_CANDIDATES = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35)
DEFAULT_SEED = 42
ARTIFACT_NAME = "goemotions_baseline_config.json"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache" / "hf"

GOEMOTIONS_METADATA_COLUMNS = {
    "text",
    "id",
    "author",
    "subreddit",
    "link_id",
    "parent_id",
    "created_utc",
    "rater_id",
    "example_very_unclear",
}


@dataclass(frozen=True)
class DatasetBundle:
    dataset: DatasetDict
    label_names: list[str]
    label2id: dict[str, int]
    id2label: dict[int, str]


@dataclass(frozen=True)
class TrainingConfig:
    model_name: str
    dataset_name: str
    dataset_config: str
    output_dir: str
    cache_dir: str
    max_length: int
    epochs: int
    train_batch_size: int
    eval_batch_size: int
    learning_rate: float
    threshold: float
    seed: int
    smoke: bool
    train_limit: int | None
    validation_limit: int | None
    test_limit: int | None
    cpu_only: bool


def set_global_seed(seed: int = DEFAULT_SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def prepare_runtime_environment(cpu_only: bool = False) -> None:
    os.environ.setdefault("USE_TF", "0")
    os.environ.setdefault("USE_FLAX", "0")
    os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
    if cpu_only:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""


def gpu_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def select_backbone(model_name: str | None = None, *, smoke: bool = False, cpu_only: bool = False) -> str:
    if model_name:
        return model_name
    if smoke or cpu_only or not gpu_available():
        return DEFAULT_CPU_BACKBONE
    return DEFAULT_GPU_BACKBONE


def resolve_device(*, cpu_only: bool = False) -> tuple[str, bool]:
    if cpu_only:
        return "cpu", False
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda", True
    except Exception:
        pass
    return "cpu", False


def cache_dir(path: str | None = None) -> Path:
    resolved = Path(path) if path else DEFAULT_CACHE_DIR
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def infer_goemotions_labels(dataset: DatasetDict) -> list[str]:
    train_features = dataset["train"].features
    return [name for name in train_features if name not in GOEMOTIONS_METADATA_COLUMNS]


def _build_multilabel_vector(example: dict[str, Any], label_names: list[str]) -> dict[str, Any]:
    example["labels"] = [float(example[name]) for name in label_names]
    return example


def _limit_split(split: Dataset, limit: int | None) -> Dataset:
    if limit is None or limit >= len(split):
        return split
    return split.select(range(limit))


def load_goemotions_bundle(
    *,
    dataset_name: str = GOEMOTIONS_DATASET_NAME,
    dataset_config: str = GOEMOTIONS_CONFIG,
    cache_path: str | None = None,
    smoke: bool = False,
    train_limit: int | None = None,
    validation_limit: int | None = None,
    test_limit: int | None = None,
) -> DatasetBundle:
    dataset = load_dataset(dataset_name, dataset_config, cache_dir=str(cache_dir(cache_path)))
    if set(dataset.keys()) == {"train"}:
        train_and_holdout = dataset["train"].train_test_split(test_size=0.2, seed=DEFAULT_SEED)
        validation_and_test = train_and_holdout["test"].train_test_split(test_size=0.5, seed=DEFAULT_SEED)
        dataset = DatasetDict(
            {
                "train": train_and_holdout["train"],
                "validation": validation_and_test["train"],
                "test": validation_and_test["test"],
            }
        )
    if smoke:
        train_limit = train_limit or 128
        validation_limit = validation_limit or 64
        test_limit = test_limit or 64
    dataset = DatasetDict(
        {
            "train": _limit_split(dataset["train"], train_limit),
            "validation": _limit_split(dataset["validation"], validation_limit),
            "test": _limit_split(dataset["test"], test_limit),
        }
    )
    label_names = infer_goemotions_labels(dataset)
    label2id = {label: idx for idx, label in enumerate(label_names)}
    id2label = {idx: label for label, idx in label2id.items()}
    dataset = dataset.map(lambda batch: _build_multilabel_vector(batch, label_names))
    return DatasetBundle(dataset=dataset, label_names=label_names, label2id=label2id, id2label=id2label)


def build_preprocess_function(tokenizer, label_names: list[str], max_length: int):
    def _preprocess(batch: dict[str, list[Any]]) -> dict[str, Any]:
        encoded = tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )
        encoded["labels"] = [
            [float(batch[label][row_idx]) for label in label_names]
            for row_idx in range(len(batch["text"]))
        ]
        return encoded

    return _preprocess


def tokenize_bundle(bundle: DatasetBundle, tokenizer, max_length: int) -> DatasetDict:
    processed = bundle.dataset.map(
        build_preprocess_function(tokenizer, bundle.label_names, max_length),
        batched=True,
        remove_columns=bundle.dataset["train"].column_names,
    )
    processed.set_format(type="torch")
    return processed


def logits_to_probabilities(logits: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-logits))


def prediction_matrix(probabilities: np.ndarray, threshold: float) -> np.ndarray:
    return (probabilities >= threshold).astype(int)


def _normalize_prediction_shapes(predictions: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if predictions.ndim == 1:
        predictions = predictions.reshape(1, -1)
    if labels.ndim == 1:
        labels = labels.reshape(1, -1)
    return predictions, labels


def multilabel_metrics(
    logits: np.ndarray,
    labels: np.ndarray,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict[str, float]:
    probabilities = logits_to_probabilities(logits)
    predictions = prediction_matrix(probabilities, threshold)
    predictions, labels = _normalize_prediction_shapes(predictions, labels)

    zero_division = 0
    return {
        "macro_f1": round(float(f1_score(labels, predictions, average="macro", zero_division=zero_division)), 4),
        "micro_f1": round(float(f1_score(labels, predictions, average="micro", zero_division=zero_division)), 4),
        "macro_precision": round(float(precision_score(labels, predictions, average="macro", zero_division=zero_division)), 4),
        "micro_precision": round(float(precision_score(labels, predictions, average="micro", zero_division=zero_division)), 4),
        "macro_recall": round(float(recall_score(labels, predictions, average="macro", zero_division=zero_division)), 4),
        "micro_recall": round(float(recall_score(labels, predictions, average="micro", zero_division=zero_division)), 4),
    }


def multilabel_debug_metrics(
    logits: np.ndarray,
    labels: np.ndarray,
    label_names: list[str],
    threshold: float,
) -> dict[str, Any]:
    probabilities = logits_to_probabilities(logits)
    predictions = prediction_matrix(probabilities, threshold)
    predictions, labels = _normalize_prediction_shapes(predictions, labels)

    per_label_support = {
        label_names[idx]: int(labels[:, idx].sum())
        for idx in range(len(label_names))
    }
    per_label_f1 = {
        label_names[idx]: round(
            float(f1_score(labels[:, idx], predictions[:, idx], average="binary", zero_division=0)),
            4,
        )
        for idx in range(len(label_names))
    }
    true_label_counts = labels.sum(axis=1)
    predicted_label_counts = predictions.sum(axis=1)

    return {
        "avg_true_labels_per_sample": round(float(true_label_counts.mean()), 4),
        "avg_predicted_labels_per_sample": round(float(predicted_label_counts.mean()), 4),
        "percent_zero_predicted_samples": round(float((predicted_label_counts == 0).mean() * 100.0), 2),
        "mean_probability": round(float(probabilities.mean()), 4),
        "max_probability_mean": round(float(probabilities.max(axis=1).mean()), 4),
        "per_label_support": per_label_support,
        "per_label_f1": per_label_f1,
    }


def sweep_thresholds(
    logits: np.ndarray,
    labels: np.ndarray,
    label_names: list[str],
    candidates: tuple[float, ...] = DEFAULT_THRESHOLD_CANDIDATES,
) -> dict[str, Any]:
    sweep_results: list[dict[str, Any]] = []
    best_result: dict[str, Any] | None = None

    for threshold in candidates:
        metrics = multilabel_metrics(logits, labels, threshold=threshold)
        debug = multilabel_debug_metrics(logits, labels, label_names, threshold)
        result = {
            "threshold": threshold,
            **metrics,
            **debug,
        }
        sweep_results.append(result)
        if best_result is None:
            best_result = result
            continue
        if result["micro_f1"] > best_result["micro_f1"]:
            best_result = result
            continue
        if result["micro_f1"] == best_result["micro_f1"] and result["macro_f1"] > best_result["macro_f1"]:
            best_result = result
            continue
        if (
            result["micro_f1"] == best_result["micro_f1"]
            and result["macro_f1"] == best_result["macro_f1"]
            and result["percent_zero_predicted_samples"] < best_result["percent_zero_predicted_samples"]
        ):
            best_result = result

    return {
        "best": best_result or {},
        "candidates": sweep_results,
    }


def validate_label_mapping_consistency(label_names: list[str], label2id: dict[str, int], id2label: dict[int, str]) -> dict[str, Any]:
    ordered_labels = [id2label[idx] for idx in range(len(label_names))]
    return {
        "label_count": len(label_names),
        "ordered_labels_match": ordered_labels == label_names,
        "label2id_matches_order": all(label2id[label] == idx for idx, label in enumerate(label_names)),
        "id2label_matches_order": all(id2label[idx] == label for idx, label in enumerate(label_names)),
    }


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def build_per_label_report(metrics: dict[str, Any]) -> dict[str, Any]:
    per_label_support = metrics.get("per_label_support", {})
    per_label_f1 = metrics.get("per_label_f1", {})
    rows = [
        {
            "label": label,
            "support": int(per_label_support.get(label, 0)),
            "f1": float(per_label_f1.get(label, 0.0)),
        }
        for label in per_label_support
    ]
    by_support = sorted(rows, key=lambda row: (-row["support"], -row["f1"], row["label"]))
    by_f1 = sorted(rows, key=lambda row: (-row["f1"], -row["support"], row["label"]))
    zero_f1 = [row["label"] for row in by_f1 if row["f1"] == 0.0]

    def bucket_name(support: int) -> str:
        if support == 0:
            return "zero_support"
        if support <= 4:
            return "low_support"
        if support <= 19:
            return "medium_support"
        return "high_support"

    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = bucket_name(row["support"])
        grouped.setdefault(
            bucket,
            {
                "label_count": 0,
                "nonzero_f1_count": 0,
                "avg_support": 0.0,
                "avg_f1": 0.0,
                "labels": [],
            },
        )
        entry = grouped[bucket]
        entry["label_count"] += 1
        entry["nonzero_f1_count"] += int(row["f1"] > 0.0)
        entry["avg_support"] += row["support"]
        entry["avg_f1"] += row["f1"]
        entry["labels"].append(row["label"])

    for entry in grouped.values():
        count = max(entry["label_count"], 1)
        entry["avg_support"] = round(entry["avg_support"] / count, 4)
        entry["avg_f1"] = round(entry["avg_f1"] / count, 4)

    return {
        "sorted_by_support": by_support,
        "sorted_by_f1": by_f1,
        "zero_f1_labels": zero_f1,
        "grouped_summary": grouped,
    }


def save_per_label_report(path: Path, metrics: dict[str, Any]) -> None:
    save_json(path, build_per_label_report(metrics))


def export_artifact_config(path: Path, config: TrainingConfig, label_names: list[str], extra: dict[str, Any] | None = None) -> None:
    payload = {
        "training": asdict(config),
        "label_names": label_names,
        "label2id": {label: idx for idx, label in enumerate(label_names)},
        "id2label": {idx: label for idx, label in enumerate(label_names)},
    }
    if extra:
        payload.update(extra)
    save_json(path / ARTIFACT_NAME, payload)


def dataset_summary(bundle: DatasetBundle) -> dict[str, Any]:
    return {
        "dataset_name": GOEMOTIONS_DATASET_NAME,
        "dataset_config": GOEMOTIONS_CONFIG,
        "num_labels": len(bundle.label_names),
        "labels": bundle.label_names,
        "split_sizes": {split_name: len(split) for split_name, split in bundle.dataset.items()},
    }
