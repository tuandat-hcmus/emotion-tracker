import argparse
import json
from math import log
import os
from pathlib import Path
import random

from app.core.config import get_settings
from app.services.ai_core.canonical_schema import CANONICAL_EMOTIONS
from app.services.ai_core.model_registry import get_model_spec
from app.services.ai_core.public_text_emotion_service import augment_text_with_public_features, infer_specific_public_text_emotion
from training.dataset_utils import GROUPED_SPLIT_POLICY, label_distribution, load_dataset, split_dataset


MODEL_ROOT = Path(__file__).resolve().parents[1] / "models"
LABEL_SCHEMA_VERSION = "canonical_v1"
SEED = 42


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


def _log_loss(gold_labels: list[str], probabilities: list[list[float]], labels: list[str]) -> float:
    index = {label: idx for idx, label in enumerate(labels)}
    losses: list[float] = []
    for gold, probs in zip(gold_labels, probabilities, strict=False):
        probability = max(probs[index[gold]], 1e-8)
        losses.append(-log(probability))
    return sum(losses) / len(losses)


def _temperature_scale(probabilities: list[list[float]], temperature: float) -> list[list[float]]:
    if temperature <= 0:
        return probabilities
    scaled: list[list[float]] = []
    for row in probabilities:
        adjusted = [pow(max(probability, 1e-8), 1.0 / temperature) for probability in row]
        total = sum(adjusted) or 1.0
        scaled.append([value / total for value in adjusted])
    return scaled


def _choose_temperature(probabilities: list[list[float]], labels: list[str], gold: list[str]) -> float:
    candidates = [0.7, 0.85, 1.0, 1.15, 1.3, 1.6]
    best_temperature = 1.0
    best_loss = float("inf")
    for temperature in candidates:
        scaled = _temperature_scale(probabilities, temperature)
        loss = _log_loss(gold, scaled, labels)
        if loss < best_loss:
            best_loss = loss
            best_temperature = temperature
    return best_temperature


def _choose_threshold(probabilities: list[list[float]], labels: list[str], gold: list[str]) -> float:
    candidates = [0.45, 0.5, 0.55, 0.58, 0.6, 0.65, 0.7]
    best_threshold = get_settings().ai_confidence_threshold
    best_score = -1.0
    for threshold in candidates:
        covered = [idx for idx, row in enumerate(probabilities) if max(row) >= threshold]
        if not covered:
            continue
        accuracy = sum(
            1
            for idx in covered
            if labels[max(range(len(labels)), key=lambda label_idx: probabilities[idx][label_idx])] == gold[idx]
        ) / len(covered)
        coverage = len(covered) / len(probabilities)
        score = accuracy * 0.7 + coverage * 0.3
        if score > best_score:
            best_score = score
            best_threshold = threshold
    return max(best_threshold, get_settings().ai_confidence_threshold)


def _language_backbone(language: str) -> tuple[str, bool]:
    settings = get_settings()
    backbone_name = {
        "en": settings.en_canonical_backbone,
        "vi": settings.vi_canonical_backbone,
        "zh": settings.zh_canonical_backbone,
    }.get(language, settings.en_canonical_backbone)
    spec = get_model_spec(backbone_name)
    return backbone_name, bool(spec is not None and spec.direct_inference)


def _build_augmented_texts(records: list[dict[str, object]], language: str) -> tuple[list[str], list[str], dict[str, list[float]], dict[str, object]]:
    texts: list[str] = []
    labels: list[str] = []
    regressions = {"valence": [], "energy": [], "stress": []}
    backbone_name, backbone_applied = _language_backbone(language)
    for item in records:
        if backbone_applied:
            weak_result = infer_specific_public_text_emotion(
                str(item["text"]),
                language=language,
                model_name=backbone_name,
                allow_heuristic_fallback=True,
            )
            augmented, _ = augment_text_with_public_features(str(item["text"]), result=weak_result, forced_language=language)
        else:
            augmented, _ = augment_text_with_public_features(str(item["text"]), forced_language=language)
        texts.append(augmented)
        labels.append(str(item["primary_emotion"]))
        regressions["valence"].append(float(item["valence_score"]))
        regressions["energy"].append(float(item["energy_score"]))
        regressions["stress"].append(float(item["stress_score"]))
    return texts, labels, regressions, {"backbone_name": backbone_name, "backbone_applied_in_training": backbone_applied}


def _prepare_transformer_dataset(records: list[dict[str, object]], label_to_id: dict[str, int]) -> tuple[list[str], list[int]]:
    texts = [str(item["text"]) for item in records]
    labels = [label_to_id[str(item["primary_emotion"])] for item in records]
    return texts, labels


def _artifact_dir(language: str, variant: str) -> Path:
    if variant == "active":
        return MODEL_ROOT / f"{language}_canonical_emotion"
    return MODEL_ROOT / f"{language}_canonical_emotion_lightweight"


def _build_metadata(
    *,
    language: str,
    dataset_name: str,
    train_records: list[dict[str, object]],
    validation_records: list[dict[str, object]],
    test_records: list[dict[str, object]],
    backbone_name: str,
    backbone_applied_in_training: bool,
    training_mode: str,
    temperature: float,
    threshold: float,
    validation_accuracy: float,
    validation_macro_f1: float,
    validation_coverage: float,
    training_command: str,
) -> dict[str, object]:
    spec = get_model_spec(backbone_name)
    return {
        "language": language,
        "backbone_name": backbone_name,
        "backbone_applied_in_training": backbone_applied_in_training,
        "backbone_runtime_status": spec.runtime_status if spec is not None else "unknown",
        "training_mode": training_mode,
        "dataset_name": dataset_name,
        "split_policy": GROUPED_SPLIT_POLICY,
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "train_size": len(train_records),
        "validation_size": len(validation_records),
        "test_size": len(test_records),
        "label_distribution": label_distribution(train_records + validation_records + test_records),
        "temperature": temperature,
        "confidence_threshold": threshold,
        "training_command": training_command,
        "validation_metrics": {
            "accuracy": validation_accuracy,
            "macro_f1": validation_macro_f1,
            "coverage_at_threshold": validation_coverage,
        },
    }


def train_language_lightweight(language: str, dataset_name: str, training_command: str) -> dict[str, object]:
    try:
        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression, Ridge
        from sklearn.pipeline import FeatureUnion, Pipeline
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required to train lightweight canonical emotion models") from exc

    records = load_dataset(language, dataset_name=dataset_name)
    train_records, validation_records, test_records = split_dataset(records)
    train_texts, train_labels, train_reg, train_meta = _build_augmented_texts(train_records, language)
    val_texts, val_labels, _, _ = _build_augmented_texts(validation_records, language)

    features = FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, min_df=1)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1)),
        ]
    )
    classifier = Pipeline(
        [
            ("features", features),
            ("classifier", LogisticRegression(max_iter=2500, class_weight="balanced", C=5.0)),
        ]
    )
    classifier.fit(train_texts, train_labels)

    regressors = {}
    for dimension in ("valence", "energy", "stress"):
        regressor = Pipeline(
            [
                ("features", FeatureUnion(
                    [
                        ("word", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, min_df=1)),
                        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1)),
                    ]
                )),
                ("regressor", Ridge(alpha=1.0)),
            ]
        )
        regressor.fit(train_texts, train_reg[dimension])
        regressors[dimension] = regressor

    val_probabilities_raw = classifier.predict_proba(val_texts)
    labels = list(classifier.classes_)
    temperature = _choose_temperature(val_probabilities_raw.tolist(), labels, val_labels)
    val_probabilities = _temperature_scale(val_probabilities_raw.tolist(), temperature)
    val_predictions = [labels[max(range(len(labels)), key=lambda idx: row[idx])] for row in val_probabilities]
    threshold = _choose_threshold(val_probabilities, labels, val_labels)

    artifact_dir = _artifact_dir(language, "lightweight")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"classifier": classifier, "regressors": regressors, "labels": labels},
        artifact_dir / "model.joblib",
    )
    metadata = _build_metadata(
        language=language,
        dataset_name=dataset_name,
        train_records=train_records,
        validation_records=validation_records,
        test_records=test_records,
        backbone_name=str(train_meta["backbone_name"]),
        backbone_applied_in_training=bool(train_meta["backbone_applied_in_training"]),
        training_mode="lightweight_tfidf_head",
        temperature=temperature,
        threshold=threshold,
        validation_accuracy=_accuracy(val_labels, val_predictions),
        validation_macro_f1=_macro_f1(val_labels, val_predictions),
        validation_coverage=round(sum(1 for row in val_probabilities if max(row) >= threshold) / len(val_probabilities), 3),
        training_command=training_command,
    )
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def train_language_transformer(language: str, dataset_name: str, training_command: str) -> dict[str, object]:
    import torch
    from torch.utils.data import DataLoader, Dataset
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    random.seed(SEED)
    torch.manual_seed(SEED)

    records = load_dataset(language, dataset_name=dataset_name)
    train_records, validation_records, test_records = split_dataset(records)
    backbone_name, _ = _language_backbone(language)
    labels = list(CANONICAL_EMOTIONS)
    label_to_id = {label: idx for idx, label in enumerate(labels)}
    id_to_label = {idx: label for label, idx in label_to_id.items()}

    local_files_only = os.getenv("HF_HUB_OFFLINE") == "1"
    tokenizer = AutoTokenizer.from_pretrained(
        backbone_name,
        cache_dir=get_settings().model_cache_dir or get_settings().hf_home or None,
        local_files_only=local_files_only,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        backbone_name,
        num_labels=len(labels),
        id2label=id_to_label,
        label2id=label_to_id,
        cache_dir=get_settings().model_cache_dir or get_settings().hf_home or None,
        local_files_only=local_files_only,
        ignore_mismatched_sizes=True,
    )
    base_model = getattr(model, model.base_model_prefix, None)
    if base_model is not None:
        for param in base_model.parameters():
            param.requires_grad = False

    class EncodedDataset(Dataset):
        def __init__(self, rows: list[dict[str, object]]):
            texts, targets = _prepare_transformer_dataset(rows, label_to_id)
            self.encodings = tokenizer(texts, truncation=True, padding=True, max_length=256)
            self.labels = targets

        def __len__(self) -> int:
            return len(self.labels)

        def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
            item = {key: torch.tensor(value[idx]) for key, value in self.encodings.items()}
            item["labels"] = torch.tensor(self.labels[idx])
            return item

    train_loader = DataLoader(EncodedDataset(train_records), batch_size=get_settings().ai_batch_size, shuffle=True)
    val_loader = DataLoader(EncodedDataset(validation_records), batch_size=get_settings().ai_batch_size, shuffle=False)

    device = torch.device("cpu")
    model.to(device)
    optimizer = torch.optim.AdamW([param for param in model.parameters() if param.requires_grad], lr=2e-4)
    model.train()
    for _ in range(3):
        for batch in train_loader:
            optimizer.zero_grad()
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            outputs.loss.backward()
            optimizer.step()

    def predict_probabilities(loader: DataLoader) -> tuple[list[list[float]], list[str]]:
        model.eval()
        probabilities: list[list[float]] = []
        gold_labels: list[str] = []
        with torch.no_grad():
            for batch in loader:
                labels_tensor = batch["labels"]
                gold_labels.extend(id_to_label[int(value)] for value in labels_tensor.tolist())
                batch = {key: value.to(device) for key, value in batch.items()}
                logits = model(**batch).logits
                probs = torch.softmax(logits, dim=-1).cpu().tolist()
                probabilities.extend(probs)
        model.train()
        return probabilities, gold_labels

    val_probabilities_raw, val_labels = predict_probabilities(val_loader)
    temperature = _choose_temperature(val_probabilities_raw, labels, val_labels)
    val_probabilities = _temperature_scale(val_probabilities_raw, temperature)
    val_predictions = [labels[max(range(len(labels)), key=lambda idx: row[idx])] for row in val_probabilities]
    threshold = _choose_threshold(val_probabilities, labels, val_labels)

    artifact_dir = _artifact_dir(language, "active")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(artifact_dir / "transformer_model")
    tokenizer.save_pretrained(artifact_dir / "transformer_model")
    metadata = _build_metadata(
        language=language,
        dataset_name=dataset_name,
        train_records=train_records,
        validation_records=validation_records,
        test_records=test_records,
        backbone_name=backbone_name,
        backbone_applied_in_training=True,
        training_mode="transformer_frozen_backbone_classifier_head",
        temperature=temperature,
        threshold=threshold,
        validation_accuracy=_accuracy(val_labels, val_predictions),
        validation_macro_f1=_macro_f1(val_labels, val_predictions),
        validation_coverage=round(sum(1 for row in val_probabilities if max(row) >= threshold) / len(val_probabilities), 3),
        training_command=training_command,
    )
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=["en", "vi", "zh", "all"], default="all")
    parser.add_argument("--dataset", choices=["seed", "realistic"], default="realistic")
    parser.add_argument("--mode", choices=["lightweight", "transformer", "all"], default="all")
    args = parser.parse_args()

    languages = ["en", "vi", "zh"] if args.language == "all" else [args.language]
    training_command = f"python -m training.train_canonical_emotion --language {args.language} --dataset {args.dataset} --mode {args.mode}"
    summaries: dict[str, dict[str, object]] = {}
    for language in languages:
        summaries[language] = {}
        if args.mode in {"lightweight", "all"}:
            summaries[language]["lightweight"] = train_language_lightweight(language, args.dataset, training_command)
        if args.mode in {"transformer", "all"}:
            summaries[language]["transformer"] = train_language_transformer(language, args.dataset, training_command)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
