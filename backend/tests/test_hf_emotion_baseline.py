import numpy as np

from app.services.ai_core.hf_emotion_checkpoint_service import EmotionLabelScore
from training.hf_emotion_baseline import (
    infer_goemotions_labels,
    multilabel_metrics,
    select_backbone,
    sweep_thresholds,
    validate_label_mapping_consistency,
)


def test_select_backbone_prefers_cpu_safe_model_for_smoke() -> None:
    assert select_backbone(None, smoke=True, cpu_only=True) == "distilroberta-base"


def test_infer_goemotions_labels_excludes_metadata_columns() -> None:
    class _Split:
        features = {
            "text": object(),
            "id": object(),
            "joy": object(),
            "sadness": object(),
            "neutral": object(),
        }

    labels = infer_goemotions_labels({"train": _Split()})  # type: ignore[arg-type]

    assert labels == ["joy", "sadness", "neutral"]


def test_multilabel_metrics_returns_expected_keys() -> None:
    logits = np.array([[3.0, -1.0], [-2.0, 2.5]])
    labels = np.array([[1.0, 0.0], [0.0, 1.0]])

    metrics = multilabel_metrics(logits, labels, threshold=0.5)

    assert metrics["macro_f1"] == 1.0
    assert metrics["micro_f1"] == 1.0
    assert sorted(metrics) == [
        "macro_f1",
        "macro_precision",
        "macro_recall",
        "micro_f1",
        "micro_precision",
        "micro_recall",
    ]


def test_threshold_sweep_and_label_mapping_consistency() -> None:
    logits = np.array([[0.1, -3.0], [-3.0, 0.1]])
    labels = np.array([[1.0, 0.0], [0.0, 1.0]])
    label_names = ["joy", "sadness"]

    sweep = sweep_thresholds(logits, labels, label_names, candidates=(0.05, 0.5))

    assert sweep["best"]["threshold"] == 0.05
    assert sweep["best"]["micro_f1"] == 1.0
    assert sweep["best"]["avg_true_labels_per_sample"] == 1.0
    assert sweep["best"]["avg_predicted_labels_per_sample"] == 1.0

    mapping = validate_label_mapping_consistency(
        label_names,
        {"joy": 0, "sadness": 1},
        {0: "joy", 1: "sadness"},
    )
    assert mapping["ordered_labels_match"] is True
    assert mapping["label2id_matches_order"] is True
    assert mapping["id2label_matches_order"] is True
