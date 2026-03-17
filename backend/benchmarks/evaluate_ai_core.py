import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ai_core.fusion_service import infer_emotion_signals
from app.services.legacy_emotion_service import infer_legacy_emotion


DATASET_PATH = Path(__file__).with_name("eval_dataset.json")
REPORT_PATH = Path(__file__).parent / "reports" / "ai_core_eval_report.md"


def _load_dataset() -> list[dict[str, object]]:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def _provider_route(pred: dict[str, object]) -> str:
    provider_name = str(pred.get("provider_name") or "")
    if provider_name == "visolex/phobert-emotion":
        return "vi_model"
    if provider_name == "Johnson8187/Chinese-Emotion-Small":
        return "zh_model"
    if provider_name == "MilaNLProc/xlm-emo-t":
        return "fallback_model"
    return "heuristic_fallback"


def _accuracy(gold: list[str], pred: list[str]) -> float:
    return round(sum(1 for g, p in zip(gold, pred, strict=False) if g == p) / len(gold), 3)


def _macro_f1(gold: list[str], pred: list[str]) -> float:
    labels = sorted(set(gold) | set(pred))
    f1_scores: list[float] = []
    for label in labels:
        tp = sum(1 for g, p in zip(gold, pred, strict=False) if g == label and p == label)
        fp = sum(1 for g, p in zip(gold, pred, strict=False) if g != label and p == label)
        fn = sum(1 for g, p in zip(gold, pred, strict=False) if g == label and p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1_scores.append(0.0 if precision + recall == 0 else (2 * precision * recall) / (precision + recall))
    return round(sum(f1_scores) / len(f1_scores), 3)


def _mae(gold: list[float], pred: list[float]) -> float:
    return round(sum(abs(g - p) for g, p in zip(gold, pred, strict=False)) / len(gold), 3)


def _evaluate(run_name: str, predictor, dataset: list[dict[str, object]]) -> tuple[dict[str, float], list[dict[str, object]]]:
    predictions: list[dict[str, object]] = []
    for item in dataset:
        result = predictor(str(item["text"]))
        predictions.append({"id": item["id"], "gold": item, "pred": result})

    gold_labels = [str(item["gold"]["primary_emotion"]) for item in predictions]
    pred_labels = [str(item["pred"]["primary_emotion"]) for item in predictions]
    gold_valence = [float(item["gold"]["valence"]) for item in predictions]
    pred_valence = [float(item["pred"]["valence"]) for item in predictions]
    gold_energy = [float(item["gold"]["energy"]) for item in predictions]
    pred_energy = [float(item["pred"]["energy"]) for item in predictions]
    gold_stress = [float(item["gold"]["stress"]) for item in predictions]
    pred_stress = [float(item["pred"]["stress"]) for item in predictions]

    metrics = {
        "accuracy": _accuracy(gold_labels, pred_labels),
        "macro_f1": _macro_f1(gold_labels, pred_labels),
        "valence_mae": _mae(gold_valence, pred_valence),
        "energy_mae": _mae(gold_energy, pred_energy),
        "stress_mae": _mae(gold_stress, pred_stress),
        "provider_breakdown": {
            "vi_model": sum(1 for item in predictions if _provider_route(item["pred"]) == "vi_model"),
            "zh_model": sum(1 for item in predictions if _provider_route(item["pred"]) == "zh_model"),
            "fallback_model": sum(1 for item in predictions if _provider_route(item["pred"]) == "fallback_model"),
            "heuristic_fallback": sum(1 for item in predictions if _provider_route(item["pred"]) == "heuristic_fallback"),
        },
    }
    print(f"{run_name}: {metrics}")
    return metrics, predictions


def _format_example_rows(predictions: list[dict[str, object]], limit: int = 6) -> str:
    rows = ["| id | language | gold | pred | route | provider | text |", "| --- | --- | --- | --- | --- | --- | --- |"]
    mismatches = [item for item in predictions if item["gold"]["primary_emotion"] != item["pred"]["primary_emotion"]]
    for item in mismatches[:limit]:
        rows.append(
            f"| {item['id']} | {item['gold']['language']} | {item['gold']['primary_emotion']} | "
            f"{item['pred']['primary_emotion']} | {_provider_route(item['pred'])} | "
            f"{item['pred'].get('provider_name')} | {str(item['gold']['text'])} |"
        )
    return "\n".join(rows)


def _format_all_rows(predictions: list[dict[str, object]]) -> str:
    rows = [
        "| id | language | gold | pred | route | provider | confidence | text |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for item in predictions:
        rows.append(
            f"| {item['id']} | {item['gold']['language']} | {item['gold']['primary_emotion']} | "
            f"{item['pred']['primary_emotion']} | {_provider_route(item['pred'])} | {item['pred'].get('provider_name')} | "
            f"{item['pred'].get('confidence', '')} | {str(item['gold']['text'])} |"
        )
    return "\n".join(rows)


def main() -> None:
    dataset = _load_dataset()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    legacy_metrics, legacy_predictions = _evaluate("legacy", infer_legacy_emotion, dataset)
    ai_metrics, ai_predictions = _evaluate(
        "ai_core",
        lambda text: infer_emotion_signals(text).model_dump(),
        dataset,
    )

    grouped: dict[str, int] = defaultdict(int)
    for item in dataset:
        grouped[str(item["language"])] += 1

    report = f"""# AI Core Evaluation Report

Dataset size: {len(dataset)} examples

Language split:
- vi: {grouped['vi']}
- zh: {grouped['zh']}

## Metrics

| system | accuracy | macro_f1 | valence_mae | energy_mae | stress_mae |
| --- | ---: | ---: | ---: | ---: | ---: |
| legacy | {legacy_metrics['accuracy']} | {legacy_metrics['macro_f1']} | {legacy_metrics['valence_mae']} | {legacy_metrics['energy_mae']} | {legacy_metrics['stress_mae']} |
| ai_core | {ai_metrics['accuracy']} | {ai_metrics['macro_f1']} | {ai_metrics['valence_mae']} | {ai_metrics['energy_mae']} | {ai_metrics['stress_mae']} |

## AI Core Provider Breakdown

- vi_model: {ai_metrics['provider_breakdown']['vi_model']}
- zh_model: {ai_metrics['provider_breakdown']['zh_model']}
- fallback_model: {ai_metrics['provider_breakdown']['fallback_model']}
- heuristic_fallback: {ai_metrics['provider_breakdown']['heuristic_fallback']}

## Representative Legacy Errors
{_format_example_rows(legacy_predictions)}

## Representative AI Core Errors
{_format_example_rows(ai_predictions)}

## AI Core Per-Row Routes
{_format_all_rows(ai_predictions)}
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
