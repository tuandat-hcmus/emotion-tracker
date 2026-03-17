from typing import Any

from app.services.ai_core import infer_emotion_signals


_PRIMARY_SIGNAL_MAP: dict[str, list[str]] = {
    "joy": ["positive_affect"],
    "gratitude": ["positive_affect", "gratitude_warmth"],
    "sadness": ["sadness_weight"],
    "loneliness": ["loneliness_pull", "connection_need"],
    "anxiety": ["stress_pressure", "anxiety_activation"],
    "overwhelm": ["stress_pressure", "overwhelm_load"],
    "anger": ["anger_friction"],
    "neutral": ["subtle_signal"],
}

_EMOTION_POLARITY = {
    "joy": 1,
    "gratitude": 1,
    "sadness": -1,
    "loneliness": -1,
    "anxiety": -1,
    "overwhelm": -1,
    "anger": -1,
    "neutral": 0,
}


def _clamp(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _normalize_text(text: str) -> str:
    return text.casefold()


def _secondary_signals_from_text(normalized: str) -> list[str]:
    signals: list[str] = []
    if any(token in normalized for token in ("một mình", "mot minh", "thu mình", "thu minh", "不想见人", "孤独")):
        signals.append("connection_need")
    if any(token in normalized for token in ("alone", "lonely", "isolated", "left out")):
        signals.append("connection_need")
    if any(token in normalized for token in ("không biết", "khong biet", "có lẽ", "co le", "也许", "不知道")):
        signals.append("uncertainty_hedging")
    if any(token in normalized for token in ("maybe", "i guess", "not sure", "perhaps")):
        signals.append("uncertainty_hedging")
    contrast_markers = any(token in normalized for token in ("nhưng", "nhung", "但是", "可是", "dù", "du"))
    if contrast_markers:
        signals.append("mixed_emotions")
    return signals


def _derive_social_need_score(primary_emotion: str, normalized: str) -> float:
    score = 0.12
    if primary_emotion == "loneliness":
        score += 0.42
    if any(token in normalized for token in ("muốn nói chuyện", "muon noi chuyen", "cần ai đó", "can ai do", "想找人聊", "陪我")):
        score += 0.28
    if any(token in normalized for token in ("need someone", "want to talk", "wish someone", "someone to talk to")):
        score += 0.28
    if any(token in normalized for token in ("không muốn gặp ai", "khong muon gap ai", "im lặng", "im lang", "不想见人")):
        score += 0.12
    if any(token in normalized for token in ("don't want to see anyone", "do not want to see anyone", "stay quiet")):
        score += 0.12
    return round(_clamp(score, 0.0, 1.0), 2)


def _derive_emotion_label(primary_emotion: str, risk_level: str, language: str) -> str:
    if risk_level == "high":
        return "high risk" if language == "en" else "nguy cơ cao"
    if language == "en":
        labels = {
            "joy": "joy",
            "gratitude": "gratitude",
            "sadness": "sadness",
            "loneliness": "loneliness",
            "anxiety": "anxiety",
            "overwhelm": "overwhelm",
            "anger": "anger",
            "neutral": "neutral",
        }
        return labels.get(primary_emotion, "neutral")
    labels = {
        "joy": "tươi sáng",
        "gratitude": "biết ơn",
        "sadness": "nặng nề",
        "loneliness": "cô đơn",
        "anxiety": "lo lắng",
        "overwhelm": "căng",
        "anger": "bực bội",
        "neutral": "bình thường",
    }
    return labels.get(primary_emotion, "bình thường")


def _infer_response_mode(
    *,
    valence_score: float,
    energy_score: float,
    stress_score: float,
    risk_level: str,
    dominant_signals: list[str],
) -> str:
    dominant_signal_set = set(dominant_signals)
    if risk_level == "high":
        return "high_risk_safe"
    if risk_level == "medium" or stress_score >= 0.66 or "overwhelm_load" in dominant_signal_set:
        return "grounding_soft"
    if "mixed_emotions" in dominant_signal_set and "positive_affect" in dominant_signal_set:
        return "supportive_reflective"
    if "positive_affect" in dominant_signal_set and valence_score >= 0.34 and stress_score <= 0.34:
        return "celebratory_warm"
    if energy_score <= 0.28 and (
        valence_score <= -0.12
        or "loneliness_pull" in dominant_signal_set
    ):
        return "low_energy_comfort"
    if "anger_friction" in dominant_signal_set or valence_score <= -0.2:
        return "validating_gentle"
    return "supportive_reflective"


def normalize_emotion_analysis(raw: dict[str, Any], risk_level: str) -> dict[str, object]:
    dominant_signals = [str(signal) for signal in raw.get("dominant_signals", [])]
    valence_score = round(float(raw.get("valence_score", 0.0)), 2)
    energy_score = round(float(raw.get("energy_score", 0.0)), 2)
    stress_score = round(float(raw.get("stress_score", 0.0)), 2)
    social_need_score = round(float(raw.get("social_need_score", 0.0)), 2)
    confidence = round(float(raw.get("confidence", 0.35)), 2)
    response_mode = str(
        raw.get(
            "response_mode",
            _infer_response_mode(
                valence_score=valence_score,
                energy_score=energy_score,
                stress_score=stress_score,
                risk_level=risk_level,
                dominant_signals=dominant_signals,
            ),
        )
    )
    label = str(raw.get("emotion_label", raw.get("label", "bình thường")))
    return {
        "label": label,
        "emotion_label": label,
        "valence_score": valence_score,
        "energy_score": energy_score,
        "stress_score": stress_score,
        "social_need_score": social_need_score,
        "confidence": confidence,
        "dominant_signals": dominant_signals,
        "response_mode": response_mode,
        "language": str(raw.get("language", "unknown")),
        "primary_emotion": str(raw.get("primary_emotion", "neutral")),
        "secondary_emotions": [str(item) for item in raw.get("secondary_emotions", [])],
        "source": str(raw.get("source", "text")),
        "raw_model_labels": [str(item) for item in raw.get("raw_model_labels", [])],
        "provider_name": str(raw.get("provider_name", "unknown")),
        "source_metadata": dict(raw.get("source_metadata", {})),
    }


def analyze_emotion(transcript: str, risk_level: str = "low", audio_path: str | None = None) -> dict[str, object]:
    normalized = _normalize_text(transcript)
    canonical = infer_emotion_signals(transcript, audio_path=audio_path)

    dominant_signals = list(dict.fromkeys(
        _PRIMARY_SIGNAL_MAP.get(canonical.primary_emotion, ["subtle_signal"]) + _secondary_signals_from_text(normalized)
    ))
    if canonical.secondary_emotions and "mixed_emotions" not in dominant_signals:
        primary_polarity = _EMOTION_POLARITY.get(canonical.primary_emotion, 0)
        secondary_polarity = _EMOTION_POLARITY.get(canonical.secondary_emotions[0], 0)
        if primary_polarity != 0 and secondary_polarity != 0 and primary_polarity != secondary_polarity:
            dominant_signals.append("mixed_emotions")

    return normalize_emotion_analysis(
        {
            "emotion_label": _derive_emotion_label(canonical.primary_emotion, risk_level, canonical.language),
            "valence_score": canonical.valence,
            "energy_score": canonical.energy,
            "stress_score": _clamp(
                canonical.stress + (0.12 if risk_level == "medium" else 0.24 if risk_level == "high" else 0.0),
                0.0,
                1.0,
            ),
            "social_need_score": _derive_social_need_score(canonical.primary_emotion, normalized),
            "confidence": canonical.confidence,
            "dominant_signals": dominant_signals,
            "language": canonical.language,
            "primary_emotion": canonical.primary_emotion,
            "secondary_emotions": canonical.secondary_emotions,
            "source": canonical.source,
            "raw_model_labels": canonical.raw_model_labels,
            "provider_name": canonical.provider_name,
            "source_metadata": canonical.source_metadata,
        },
        risk_level=risk_level,
    )
