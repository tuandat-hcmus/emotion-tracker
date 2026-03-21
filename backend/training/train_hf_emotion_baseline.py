from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from training.hf_emotion_baseline import (
    DEFAULT_SEED,
    DEFAULT_THRESHOLD,
    TrainingConfig,
    cache_dir,
    dataset_summary,
    export_artifact_config,
    load_goemotions_bundle,
    prepare_runtime_environment,
    resolve_device,
    save_json,
    save_per_label_report,
    select_backbone,
    set_global_seed,
    sweep_thresholds,
    tokenize_bundle,
    validate_label_mapping_consistency,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a Hugging Face GoEmotions multi-label baseline.")
    parser.add_argument("--model-name", default=None, help="Override backbone model. Defaults to automatic selection.")
    parser.add_argument("--dataset-name", default="go_emotions")
    parser.add_argument("--dataset-config", default="raw")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--train-batch-size", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--train-limit", type=int, default=None)
    parser.add_argument("--validation-limit", type=int, default=None)
    parser.add_argument("--test-limit", type=int, default=None)
    parser.add_argument("--cpu-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prepare_runtime_environment(cpu_only=args.cpu_only)
    set_global_seed(args.seed)

    import torch
    from torch.optim import AdamW
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding

    model_name = select_backbone(args.model_name, smoke=args.smoke, cpu_only=args.cpu_only)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(
        "training_start "
        f"model={model_name} epochs={args.epochs} train_batch_size={args.train_batch_size} "
        f"eval_batch_size={args.eval_batch_size} max_length={args.max_length} "
        f"train_limit={args.train_limit if args.train_limit is not None else ('128' if args.smoke else 'full')} "
        f"validation_limit={args.validation_limit if args.validation_limit is not None else ('64' if args.smoke else 'full')} "
        f"test_limit={args.test_limit if args.test_limit is not None else ('64' if args.smoke else 'full')}",
        flush=True,
    )

    bundle = load_goemotions_bundle(
        dataset_name=args.dataset_name,
        dataset_config=args.dataset_config,
        cache_path=args.cache_dir,
        smoke=args.smoke,
        train_limit=args.train_limit,
        validation_limit=args.validation_limit,
        test_limit=args.test_limit,
    )
    save_json(output_dir / "dataset_summary.json", dataset_summary(bundle))
    print(
        "dataset_ready "
        f"train={len(bundle.dataset['train'])} validation={len(bundle.dataset['validation'])} test={len(bundle.dataset['test'])} "
        f"labels={len(bundle.label_names)}",
        flush=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=str(cache_dir(args.cache_dir)))
    tokenized = tokenize_bundle(bundle, tokenizer, args.max_length)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(bundle.label_names),
        label2id=bundle.label2id,
        id2label=bundle.id2label,
        problem_type="multi_label_classification",
        cache_dir=str(cache_dir(args.cache_dir)),
    )
    device_name, using_cuda = resolve_device(cpu_only=args.cpu_only)
    device = torch.device(device_name)
    model.to(device)
    print(f"model_ready device={device_name}", flush=True)

    train_loader = DataLoader(
        tokenized["train"],
        batch_size=args.train_batch_size,
        shuffle=True,
        collate_fn=data_collator,
    )
    validation_loader = DataLoader(
        tokenized["validation"],
        batch_size=args.eval_batch_size,
        shuffle=False,
        collate_fn=data_collator,
    )
    test_loader = DataLoader(
        tokenized["test"],
        batch_size=args.eval_batch_size,
        shuffle=False,
        collate_fn=data_collator,
    )

    optimizer = AdamW(model.parameters(), lr=args.learning_rate)

    history: list[dict[str, object]] = []
    best_validation_result: dict[str, object] | None = None
    for epoch in range(args.epochs):
        print(f"epoch_start epoch={epoch + 1}", flush=True)
        model.train()
        train_loss = 0.0
        train_steps = 0
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            train_loss += float(loss.item())
            train_steps += 1
            if train_steps % 50 == 0:
                print(
                    f"train_progress epoch={epoch + 1} step={train_steps} avg_loss={round(train_loss / train_steps, 4)}",
                    flush=True,
                )

        model.eval()
        validation_logits: list[np.ndarray] = []
        validation_labels: list[np.ndarray] = []
        with torch.no_grad():
            for batch in validation_loader:
                labels = batch["labels"]
                batch = {key: value.to(device) for key, value in batch.items()}
                outputs = model(**batch)
                validation_logits.append(outputs.logits.cpu().numpy())
                validation_labels.append(labels.cpu().numpy())
        threshold_search = sweep_thresholds(
            np.concatenate(validation_logits, axis=0),
            np.concatenate(validation_labels, axis=0),
            bundle.label_names,
        )
        epoch_metrics = dict(threshold_search["best"])
        epoch_metrics["epoch"] = epoch + 1
        epoch_metrics["train_loss"] = round(train_loss / max(train_steps, 1), 4)
        epoch_metrics["threshold_sweep"] = threshold_search["candidates"]
        history.append(epoch_metrics)
        if best_validation_result is None:
            best_validation_result = epoch_metrics
        elif (
            epoch_metrics["micro_f1"] > best_validation_result["micro_f1"]
            or (
                epoch_metrics["micro_f1"] == best_validation_result["micro_f1"]
                and epoch_metrics["macro_f1"] > best_validation_result["macro_f1"]
            )
        ):
            best_validation_result = epoch_metrics
        print(
            f"epoch={epoch + 1} train_loss={epoch_metrics['train_loss']} "
            f"val_macro_f1={epoch_metrics['macro_f1']} val_micro_f1={epoch_metrics['micro_f1']} "
            f"best_threshold={epoch_metrics['threshold']} avg_pred_labels={epoch_metrics['avg_predicted_labels_per_sample']} "
            f"zero_pred_pct={epoch_metrics['percent_zero_predicted_samples']}",
            flush=True,
        )

    selected_threshold = float(best_validation_result["threshold"] if best_validation_result is not None else args.threshold)
    test_logits: list[np.ndarray] = []
    test_labels: list[np.ndarray] = []
    with torch.no_grad():
        for batch in test_loader:
            labels = batch["labels"]
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            test_logits.append(outputs.logits.cpu().numpy())
            test_labels.append(labels.cpu().numpy())
    test_search = sweep_thresholds(
        np.concatenate(test_logits, axis=0),
        np.concatenate(test_labels, axis=0),
        bundle.label_names,
        candidates=(selected_threshold,),
    )
    test_metrics = dict(test_search["best"])
    print(
        "test_metrics",
        " ".join(
            [
                f"macro_f1={test_metrics['macro_f1']}",
                f"micro_f1={test_metrics['micro_f1']}",
                f"macro_precision={test_metrics['macro_precision']}",
                f"micro_precision={test_metrics['micro_precision']}",
                f"macro_recall={test_metrics['macro_recall']}",
                f"micro_recall={test_metrics['micro_recall']}",
                f"threshold={test_metrics['threshold']}",
                f"avg_pred_labels={test_metrics['avg_predicted_labels_per_sample']}",
                f"zero_pred_pct={test_metrics['percent_zero_predicted_samples']}",
            ]
        ),
        flush=True,
    )

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    config = TrainingConfig(
        model_name=model_name,
        dataset_name=args.dataset_name,
        dataset_config=args.dataset_config,
        output_dir=str(output_dir),
        cache_dir=str(cache_dir(args.cache_dir)),
        max_length=args.max_length,
        epochs=args.epochs,
        train_batch_size=args.train_batch_size,
        eval_batch_size=args.eval_batch_size,
        learning_rate=args.learning_rate,
        threshold=selected_threshold,
        seed=args.seed,
        smoke=args.smoke,
        train_limit=args.train_limit if args.train_limit is not None else (128 if args.smoke else None),
        validation_limit=args.validation_limit if args.validation_limit is not None else (64 if args.smoke else None),
        test_limit=args.test_limit if args.test_limit is not None else (64 if args.smoke else None),
        cpu_only=not using_cuda,
    )
    export_artifact_config(
        output_dir,
        config,
        bundle.label_names,
        extra={
            "label_mapping_validation": validate_label_mapping_consistency(bundle.label_names, bundle.label2id, bundle.id2label),
            "validation_history": history,
            "best_validation_result": best_validation_result,
            "test_metrics": test_metrics,
        },
    )
    report_payload = {
        "label_mapping_validation": validate_label_mapping_consistency(bundle.label_names, bundle.label2id, bundle.id2label),
        "validation_history": history,
        "best_validation_result": best_validation_result,
        "chosen_threshold": selected_threshold,
        "test_metrics": test_metrics,
    }
    save_json(output_dir / "metrics.json", report_payload)
    save_json(output_dir / "quality_report.json", report_payload)
    if best_validation_result is not None:
        save_per_label_report(output_dir / "validation_per_label_report.json", best_validation_result)
    save_per_label_report(output_dir / "test_per_label_report.json", test_metrics)
    print(f"artifacts_ready output_dir={output_dir}", flush=True)


if __name__ == "__main__":
    main()
