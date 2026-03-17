import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.services.ai_core.canonical_model_service import infer_canonical_text_emotion
from app.services.ai_core.model_registry import selected_multilingual_model, selected_public_model
from app.services.ai_core.text_emotion_service import infer_public_only_text_emotion, infer_text_emotion
from app.services.legacy_emotion_service import infer_legacy_emotion
from training.dataset_utils import GROUPED_SPLIT_POLICY, group_distribution, label_distribution, load_realistic_dataset, split_dataset


REPORT_PATH = Path(__file__).parent / "reports" / "canonical_emotion_generalization_report.md"
MODEL_ROOT = ROOT / "models"


def _accuracy(gold: list[str], pred: list[str]) -> float:
    return round(sum(1 for g, p in zip(gold, pred, strict=False) if g == p) / len(gold), 3)


def _per_class_f1(gold: list[str], pred: list[str]) -> dict[str, float]:
    labels = sorted(set(gold) | set(pred))
    scores: dict[str, float] = {}
    for label in labels:
        tp = sum(1 for g, p in zip(gold, pred, strict=False) if g == label and p == label)
        fp = sum(1 for g, p in zip(gold, pred, strict=False) if g != label and p == label)
        fn = sum(1 for g, p in zip(gold, pred, strict=False) if g == label and p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores[label] = round(0.0 if precision + recall == 0 else (2 * precision * recall) / (precision + recall), 3)
    return scores


def _macro_f1(gold: list[str], pred: list[str]) -> float:
    per_class = _per_class_f1(gold, pred)
    return round(sum(per_class.values()) / len(per_class), 3)


def _confusion_matrix(gold: list[str], pred: list[str]) -> dict[str, dict[str, int]]:
    labels = sorted(set(gold) | set(pred))
    matrix = {gold_label: {pred_label: 0 for pred_label in labels} for gold_label in labels}
    for gold_label, pred_label in zip(gold, pred, strict=False):
        matrix[gold_label][pred_label] += 1
    return matrix


def _to_dict(result) -> dict[str, object]:
    payload = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    if "primary_emotion" not in payload:
        ranked = list(payload.get("ranked_emotions", []))
        payload["primary_emotion"] = ranked[0][0] if ranked else "neutral"
    if "source_metadata" not in payload:
        payload["source_metadata"] = {}
    return payload


def _evaluate_system(name: str, predictor, records: list[dict[str, object]]) -> tuple[dict[str, object], list[dict[str, object]]]:
    predictions: list[dict[str, object]] = []
    for item in records:
        result = predictor(str(item["text"]), str(item["language"]))
        predictions.append(
            {
                "id": item["id"],
                "language": item["language"],
                "source_group": item["source_group"],
                "text": item["text"],
                "gold": item["primary_emotion"],
                "pred": result["primary_emotion"],
                "confidence": result.get("confidence", 0.0),
                "provider_name": result.get("provider_name", "unknown"),
                "low_confidence": bool(result.get("source_metadata", {}).get("low_confidence", False)),
            }
        )
    gold = [item["gold"] for item in predictions]
    pred = [item["pred"] for item in predictions]
    per_language: dict[str, dict[str, float]] = {}
    for language in sorted({str(item["language"]) for item in records}):
        scoped = [item for item in predictions if item["language"] == language]
        scoped_gold = [item["gold"] for item in scoped]
        scoped_pred = [item["pred"] for item in scoped]
        per_language[language] = {
            "accuracy": _accuracy(scoped_gold, scoped_pred),
            "macro_f1": _macro_f1(scoped_gold, scoped_pred),
        }
    metrics = {
        "accuracy": _accuracy(gold, pred),
        "macro_f1": _macro_f1(gold, pred),
        "per_class_f1": _per_class_f1(gold, pred),
        "coverage": round(sum(1 for item in predictions if not item["low_confidence"]) / len(predictions), 3),
        "per_language": per_language,
        "confusion_matrix": _confusion_matrix(gold, pred),
    }
    print(f"{name}: {metrics}")
    return metrics, predictions


def _format_matrix(matrix: dict[str, dict[str, int]]) -> str:
    labels = list(matrix)
    rows = ["| gold \\ pred | " + " | ".join(labels) + " |", "| --- | " + " | ".join(["---:"] * len(labels)) + " |"]
    for gold_label in labels:
        rows.append("| " + gold_label + " | " + " | ".join(str(matrix[gold_label][pred_label]) for pred_label in labels) + " |")
    return "\n".join(rows)


def _format_failures(title: str, rows: list[dict[str, object]], limit: int = 10) -> str:
    selected = [row for row in rows if row["gold"] != row["pred"]][:limit]
    lines = [f"## {title}", "| id | language | group | gold | pred | confidence | provider | text |", "| --- | --- | --- | --- | --- | ---: | --- | --- |"]
    for row in selected:
        lines.append(
            f"| {row['id']} | {row['language']} | {row['source_group']} | {row['gold']} | {row['pred']} | {row['confidence']} | {row['provider_name']} | {row['text']} |"
        )
    return "\n".join(lines)


def _metadata(language: str, variant: str = "active") -> dict[str, object] | None:
    path = MODEL_ROOT / (f"{language}_canonical_emotion" if variant == "active" else f"{language}_canonical_emotion_lightweight") / "metadata.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def main() -> None:
    settings = get_settings()
    records = load_realistic_dataset(language="en")
    _, _, test_records = split_dataset(records)

    legacy_metrics, legacy_rows = _evaluate_system(
        "legacy",
        lambda text, _lang: infer_legacy_emotion(text),
        test_records,
    )
    public_metrics, public_rows = _evaluate_system(
        "public",
        lambda text, _lang: _to_dict(infer_public_only_text_emotion(text)),
        test_records,
    )
    lightweight_metrics, lightweight_rows = _evaluate_system(
        "lightweight_canonical",
        lambda text, lang: _to_dict(infer_canonical_text_emotion(text, lang, variant="lightweight") or infer_public_only_text_emotion(text)),
        test_records,
    )
    transformer_metrics, transformer_rows = _evaluate_system(
        "transformer_canonical",
        lambda text, _lang: _to_dict(infer_text_emotion(text)),
        test_records,
    )

    selected_stack = {
        "main_language": settings.main_language,
        "en_public_model": selected_public_model("en").model_name if selected_public_model("en") else None,
        "vi_public_model": selected_public_model("vi").model_name if selected_public_model("vi") else None,
        "zh_public_model": selected_public_model("zh").model_name if selected_public_model("zh") else None,
        "multilingual_model": selected_multilingual_model().model_name if selected_multilingual_model() else None,
        "en_canonical_dir": settings.en_canonical_model_dir,
        "vi_canonical_dir": settings.vi_canonical_model_dir,
        "zh_canonical_dir": settings.zh_canonical_model_dir,
        "en_canonical_backbone": settings.en_canonical_backbone,
        "vi_canonical_backbone": settings.vi_canonical_backbone,
        "zh_canonical_backbone": settings.zh_canonical_backbone,
        "ai_confidence_threshold": settings.ai_confidence_threshold,
        "ai_low_confidence_hybrid": settings.ai_low_confidence_hybrid,
    }
    metadata = {
        "en_lightweight": _metadata("en", "lightweight"),
        "en_transformer": _metadata("en", "active"),
        "vi_lightweight": _metadata("vi", "lightweight"),
        "zh_lightweight": _metadata("zh", "lightweight"),
        "vi_transformer": _metadata("vi", "active"),
        "zh_transformer": _metadata("zh", "active"),
    }
    report = f"""# Canonical Emotion Generalization Report

Grouped split policy:
- {GROUPED_SPLIT_POLICY}
- `source_group` is the split boundary. No group appears across train/validation/test.

Selected stack:
```json
{json.dumps(selected_stack, ensure_ascii=False, indent=2)}
```

Dataset sizes:
- total: {len(records)}
- test: {len(test_records)}
- en total: {len([item for item in records if item['language'] == 'en'])}

Label distribution:
```json
{json.dumps(label_distribution(records), ensure_ascii=False, indent=2)}
```

Source-group distribution:
```json
{json.dumps(group_distribution(records), ensure_ascii=False, indent=2)}
```

Artifact metadata:
```json
{json.dumps(metadata, ensure_ascii=False, indent=2)}
```

## Metrics

| system | accuracy | macro_f1 | coverage |
| --- | ---: | ---: | ---: |
| legacy heuristic | {legacy_metrics['accuracy']} | {legacy_metrics['macro_f1']} | {legacy_metrics['coverage']} |
| public direct-mapping | {public_metrics['accuracy']} | {public_metrics['macro_f1']} | {public_metrics['coverage']} |
| lightweight canonical | {lightweight_metrics['accuracy']} | {lightweight_metrics['macro_f1']} | {lightweight_metrics['coverage']} |
| transformer canonical | {transformer_metrics['accuracy']} | {transformer_metrics['macro_f1']} | {transformer_metrics['coverage']} |

## Per-Class F1
```json
{json.dumps({
    "legacy": legacy_metrics["per_class_f1"],
    "public": public_metrics["per_class_f1"],
    "lightweight": lightweight_metrics["per_class_f1"],
    "transformer": transformer_metrics["per_class_f1"],
}, ensure_ascii=False, indent=2)}
```

## Per-Language Breakdown
```json
{json.dumps({
    "legacy": legacy_metrics["per_language"],
    "public": public_metrics["per_language"],
    "lightweight": lightweight_metrics["per_language"],
    "transformer": transformer_metrics["per_language"],
}, ensure_ascii=False, indent=2)}
```

## Confusion Matrix: Transformer Canonical
{_format_matrix(transformer_metrics['confusion_matrix'])}

{_format_failures("Representative Transformer Errors", transformer_rows, limit=10)}

{_format_failures("Representative Lightweight Errors", lightweight_rows, limit=10)}

{_format_failures("Representative Public Errors", public_rows, limit=10)}

Conclusion:
- Transformer canonical {"beats" if transformer_metrics['accuracy'] > lightweight_metrics['accuracy'] else "does not beat"} the old lightweight canonical head on the grouped realistic holdout.
- Transformer canonical {"beats" if transformer_metrics['accuracy'] > public_metrics['accuracy'] else "does not beat"} the public direct-mapping path.
- Transformer canonical {"beats" if transformer_metrics['accuracy'] > legacy_metrics['accuracy'] else "does not beat"} the legacy heuristic path.
"""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
