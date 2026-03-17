from collections.abc import Sequence

from app.services.ai_core.canonical_schema import canonical_dimensions, canonicalize_emotion


def sorted_unique_emotions(items: Sequence[tuple[str, float]]) -> list[tuple[str, float]]:
    aggregated: dict[str, float] = {}
    for emotion, score in items:
        aggregated[emotion] = aggregated.get(emotion, 0.0) + score
    return sorted(aggregated.items(), key=lambda item: item[1], reverse=True)


def provider_label_alias(model_name: str, label: str) -> str:
    normalized = label.strip().casefold().replace("_", " ").replace("-", " ")
    aliases: dict[str, dict[str, str]] = {
        "Johnson8187/Chinese-Emotion-Small": {
            "label 0": "neutral",
            "label 1": "concerned",
            "label 2": "happy",
            "label 3": "anger",
            "label 4": "sadness",
            "label 5": "questioning",
            "label 6": "surprise",
            "label 7": "disgust",
        },
        "visolex/phobert-emotion": {
            "enjoyment": "joy",
            "sadness": "sadness",
            "fear": "anxiety",
            "anger": "anger",
            "disgust": "anger",
            "surprise": "neutral",
            "other": "neutral",
        },
        "MilaNLProc/xlm-emo-t": {
            "joy": "joy",
            "sadness": "sadness",
            "anger": "anger",
            "fear": "anxiety",
            "trust": "gratitude",
            "surprise": "neutral",
            "anticipation": "anxiety",
            "neutral": "neutral",
            "disgust": "anger",
        },
        "SamLowe/roberta-base-go_emotions": {
            "admiration": "joy",
            "amusement": "joy",
            "anger": "anger",
            "annoyance": "anger",
            "approval": "joy",
            "caring": "gratitude",
            "confusion": "neutral",
            "curiosity": "neutral",
            "desire": "joy",
            "disappointment": "sadness",
            "disapproval": "anger",
            "disgust": "anger",
            "embarrassment": "sadness",
            "excitement": "joy",
            "fear": "anxiety",
            "gratitude": "gratitude",
            "grief": "sadness",
            "joy": "joy",
            "love": "joy",
            "nervousness": "anxiety",
            "optimism": "joy",
            "pride": "joy",
            "realization": "neutral",
            "relief": "gratitude",
            "remorse": "sadness",
            "sadness": "sadness",
            "surprise": "neutral",
            "neutral": "neutral",
        },
        "j-hartmann/emotion-english-distilroberta-base": {
            "anger": "anger",
            "disgust": "anger",
            "fear": "anxiety",
            "joy": "joy",
            "neutral": "neutral",
            "sadness": "sadness",
            "surprise": "neutral",
        },
        "j-hartmann/emotion-english-roberta-large": {
            "anger": "anger",
            "disgust": "anger",
            "fear": "anxiety",
            "joy": "joy",
            "neutral": "neutral",
            "sadness": "sadness",
            "surprise": "neutral",
        },
    }
    provider_map = aliases.get(model_name)
    if provider_map and normalized in provider_map:
        return provider_map[normalized]
    return label


def adapt_ranked_labels(model_name: str, raw_predictions: Sequence[dict[str, float | str]]) -> tuple[list[str], list[tuple[str, float]], tuple[float, float, float]]:
    raw_labels = [str(item["label"]) for item in raw_predictions]
    ranked = sorted_unique_emotions(
        [
            (
                canonicalize_emotion(provider_label_alias(model_name, str(item["label"]))),
                float(item.get("score", 0.0)),
            )
            for item in raw_predictions
        ]
    )
    dimensions = canonical_dimensions(ranked)
    return raw_labels, ranked, dimensions
