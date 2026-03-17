from collections import Counter
import hashlib
import json
from pathlib import Path


DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets"
GROUPED_SPLIT_POLICY = "grouped_hash_by_source_group_70_20_10"


def dataset_path(language: str, dataset_name: str = "seed") -> Path:
    suffix = "canonical_emotion_seed" if dataset_name == "seed" else "canonical_emotion_realistic"
    return DATASET_DIR / f"{suffix}_{language}.jsonl"


def load_dataset(language: str | None = None, dataset_name: str = "seed") -> list[dict[str, object]]:
    languages = [language] if language else ["en", "vi", "zh"]
    records: list[dict[str, object]] = []
    for item in languages:
        path = dataset_path(item, dataset_name=dataset_name)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def load_seed_dataset(language: str | None = None) -> list[dict[str, object]]:
    return load_dataset(language, dataset_name="seed")


def load_realistic_dataset(language: str | None = None) -> list[dict[str, object]]:
    return load_dataset(language, dataset_name="realistic")


def _split_bucket(value: str) -> int:
    digest = hashlib.md5(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 10


def split_dataset(records: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    train: list[dict[str, object]] = []
    validation: list[dict[str, object]] = []
    test: list[dict[str, object]] = []
    for item in records:
        group_key = str(item.get("source_group") or item.get("text"))
        bucket = _split_bucket(group_key)
        if bucket <= 6:
            train.append(item)
        elif bucket <= 8:
            validation.append(item)
        else:
            test.append(item)
    return train, validation, test


def label_distribution(records: list[dict[str, object]]) -> dict[str, int]:
    return dict(sorted(Counter(str(item["primary_emotion"]) for item in records).items()))


def group_distribution(records: list[dict[str, object]]) -> dict[str, int]:
    return dict(sorted(Counter(str(item.get("source_group", "ungrouped")) for item in records).items()))
