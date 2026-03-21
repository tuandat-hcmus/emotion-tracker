from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from training.hf_emotion_baseline import (
    cache_dir,
    load_goemotions_bundle,
    prepare_runtime_environment,
    resolve_device,
    save_per_label_report,
    sweep_thresholds,
    tokenize_bundle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained Hugging Face GoEmotions baseline.")
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--dataset-name", default="go_emotions")
    parser.add_argument("--dataset-config", default="raw")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--cpu-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prepare_runtime_environment(cpu_only=args.cpu_only)

    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding

    model_dir = Path(args.model_dir)
    artifact_config = json.loads((model_dir / "goemotions_baseline_config.json").read_text(encoding="utf-8"))
    threshold = float(args.threshold if args.threshold is not None else artifact_config["training"]["threshold"])

    bundle = load_goemotions_bundle(
        dataset_name=args.dataset_name,
        dataset_config=args.dataset_config,
        cache_path=args.cache_dir,
        smoke=args.smoke,
        train_limit=artifact_config["training"].get("train_limit"),
        validation_limit=artifact_config["training"].get("validation_limit"),
        test_limit=artifact_config["training"].get("test_limit"),
    )
    tokenizer = AutoTokenizer.from_pretrained(model_dir, cache_dir=str(cache_dir(args.cache_dir)))
    tokenized = tokenize_bundle(bundle, tokenizer, args.max_length)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    loader = DataLoader(tokenized["test"], batch_size=args.eval_batch_size, shuffle=False, collate_fn=data_collator)

    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    device_name, _using_cuda = resolve_device(cpu_only=args.cpu_only)
    device = torch.device(device_name)
    model.to(device)
    model.eval()
    print(f"evaluation_ready device={device_name} threshold={threshold}", flush=True)

    logits: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    with torch.no_grad():
        for batch in loader:
            batch_labels = batch["labels"]
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            logits.append(outputs.logits.cpu().numpy())
            labels.append(batch_labels.cpu().numpy())
    threshold_search = sweep_thresholds(
        np.concatenate(logits, axis=0),
        np.concatenate(labels, axis=0),
        bundle.label_names,
        candidates=(threshold,),
    )
    metrics = dict(threshold_search["best"])
    print(
        "test_metrics",
        " ".join(
            [
                f"macro_f1={metrics['macro_f1']}",
                f"micro_f1={metrics['micro_f1']}",
                f"macro_precision={metrics['macro_precision']}",
                f"micro_precision={metrics['micro_precision']}",
                f"macro_recall={metrics['macro_recall']}",
                f"micro_recall={metrics['micro_recall']}",
                f"threshold={metrics['threshold']}",
                f"avg_pred_labels={metrics['avg_predicted_labels_per_sample']}",
                f"zero_pred_pct={metrics['percent_zero_predicted_samples']}",
            ]
        ),
        flush=True,
    )
    (model_dir / "evaluation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    save_per_label_report(model_dir / "evaluation_per_label_report.json", metrics)


if __name__ == "__main__":
    main()
