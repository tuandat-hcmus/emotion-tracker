from app.schemas.me import QuoteResponse

_QUOTE_CATALOG: dict[str, list[dict[str, str]]] = {
    "high_risk": [
        {
            "short_text": "Take this one moment gently. You do not need to carry all of it at once.",
            "tone": "grounding",
            "source_type": "curated",
        },
        {
            "short_text": "Staying with the next safe step is enough for now.",
            "tone": "supportive",
            "source_type": "curated",
        },
    ],
    "stressed": [
        {
            "short_text": "A slower pace is still progress.",
            "tone": "calm",
            "source_type": "curated",
        },
        {
            "short_text": "You can narrow today down to one manageable thing.",
            "tone": "steady",
            "source_type": "curated",
        },
    ],
    "sad": [
        {
            "short_text": "Heavy days still move, even when they move quietly.",
            "tone": "supportive",
            "source_type": "curated",
        },
        {
            "short_text": "You are allowed to be tender with yourself today.",
            "tone": "gentle",
            "source_type": "curated",
        },
    ],
    "positive": [
        {
            "short_text": "Small signs of steadiness are worth keeping.",
            "tone": "warm",
            "source_type": "curated",
        },
        {
            "short_text": "Let this calmer moment count as real progress.",
            "tone": "bright",
            "source_type": "curated",
        },
    ],
    "general": [
        {
            "short_text": "You can meet today one honest check-in at a time.",
            "tone": "neutral",
            "source_type": "curated",
        },
        {
            "short_text": "Notice what is true right now before judging it.",
            "tone": "reflective",
            "source_type": "curated",
        },
    ],
}

_POSITIVE_EMOTIONS = {"happy", "joy", "grateful", "calm", "hopeful", "content", "relieved", "tươi sáng"}
_LOW_MOOD_EMOTIONS = {"sad", "down", "lonely", "tired", "ashamed", "hurt", "chùng xuống", "nặng nề"}
_STRESS_EMOTIONS = {"anxious", "stressed", "overwhelmed", "angry", "frustrated", "afraid", "căng", "phức hợp"}


def _stable_index(seed: str, size: int) -> int:
    return sum(ord(character) for character in seed) % size


def select_quote(
    *,
    quote_opt_in: bool,
    latest_emotion_label: str | None,
    latest_risk_level: str | None,
    user_id: str,
) -> QuoteResponse | None:
    if not quote_opt_in:
        return None

    normalized_emotion = (latest_emotion_label or "").strip().lower()
    normalized_risk = (latest_risk_level or "low").strip().lower()

    if normalized_risk == "high":
        key = "high_risk"
    elif normalized_emotion in _STRESS_EMOTIONS or normalized_risk == "medium":
        key = "stressed"
    elif normalized_emotion in _LOW_MOOD_EMOTIONS:
        key = "sad"
    elif normalized_emotion in _POSITIVE_EMOTIONS:
        key = "positive"
    else:
        key = "general"

    options = _QUOTE_CATALOG[key]
    selected = options[_stable_index(f"{user_id}:{normalized_emotion}:{normalized_risk}", len(options))]
    return QuoteResponse(**selected)
