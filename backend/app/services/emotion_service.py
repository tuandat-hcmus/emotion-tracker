from typing import Any

from app.services.ai_core import infer_emotion_signals
from app.services.ai_core.language_service import normalize_language_code


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
    "sadness": -1,
    "fear": -1,
    "anger": -1,
    "disgust": -1,
    "neutral": 0,
    "surprise": 0,
}
_FRONTEND_LABELS = ("anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral")
_STRESS_WORDS = (
    "stress",
    "stressed",
    "overwhelmed",
    "deadline",
    "deadlines",
    "pressure",
    "piling up",
    "too much",
    "can't keep up",
    "cannot keep up",
    "workload",
    "behind on work",
    "under pressure",
    "áp lực",
    "quá tải",
    "không theo kịp",
    "khong theo kip",
    "dồn dập",
    "don dap",
)


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
    if any(token in normalized for token in ("tự hào", "tu hao", "proud", "vượt qua", "vuot qua", "overcame")):
        signals.append("pride_growth")
    if any(token in normalized for token in ("biết ơn", "biet on", "grateful", "gratitude", "thankful")):
        signals.append("gratitude_warmth")
    if any(token in normalized for token in ("nhẹ nhõm", "nhe nhom", "relieved", "relief")):
        signals.append("relief_release")
    if any(token in normalized for token in ("stress", "stressed", "pressure", "áp lực", "ap luc", "under pressure")):
        signals.append("stress_pressure")
    if any(
        token in normalized
        for token in ("overwhelmed", "too much", "can't keep up", "cannot keep up", "quá tải", "qua tai", "không theo kịp", "khong theo kip")
    ):
        signals.append("overwhelm_load")
    if any(
        token in normalized
        for token in ("deadline", "deadlines", "piling up", "workload", "dồn dập", "don dap", "công việc", "cong viec", "project", "exam")
    ):
        signals.append("deadline_pressure")
    contrast_markers = any(token in normalized for token in ("nhưng", "nhung", "但是", "可是", "dù", "du"))
    if contrast_markers:
        signals.append("mixed_emotions")
    return signals


def _derive_stress_score(
    *,
    normalized: str,
    base_stress: float,
    fear_score: float,
    dominant_signals: list[str],
    risk_level: str,
) -> float:
    adjusted = float(base_stress)
    signal_set = set(dominant_signals)
    if fear_score >= 0.45:
        adjusted += 0.12
    if "deadline_pressure" in signal_set:
        adjusted += 0.12
    if "overwhelm_load" in signal_set:
        adjusted += 0.1
    if any(token in normalized for token in _STRESS_WORDS):
        adjusted += 0.08
    if risk_level == "medium":
        adjusted += 0.12
    elif risk_level == "high":
        adjusted += 0.24
    if "deadline_pressure" in signal_set and fear_score >= 0.4:
        adjusted = max(adjusted, 0.68)
    return round(_clamp(adjusted, 0.0, 1.0), 2)


def _derive_social_need_score(primary_label: str, normalized: str) -> float:
    score = 0.12
    if primary_label == "sadness" and any(
        token in normalized for token in ("một mình", "mot minh", "thu mình", "thu minh", "孤独", "alone", "lonely")
    ):
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


def _internalize_label(primary_label: str, dominant_signals: list[str], stress_score: float) -> str:
    signal_set = set(dominant_signals)
    if primary_label == "joy" and "gratitude_warmth" in signal_set:
        return "gratitude"
    if primary_label == "sadness" and "connection_need" in signal_set:
        return "loneliness"
    if primary_label == "fear":
        return "overwhelm" if stress_score >= 0.72 or "overwhelm_load" in signal_set else "anxiety"
    if primary_label == "disgust":
        return "anger"
    if primary_label == "surprise":
        return "neutral"
    return primary_label


def to_frontend_label(label: str) -> str:
    normalized = label.strip().casefold()
    mapping = {
        "anger": "anger",
        "disgust": "disgust",
        "fear": "fear",
        "anxiety": "fear",
        "overwhelm": "fear",
        "joy": "joy",
        "gratitude": "joy",
        "pride": "joy",
        "relief": "joy",
        "hope": "joy",
        "sadness": "sadness",
        "loneliness": "sadness",
        "emptiness": "sadness",
        "exhaustion": "sadness",
        "surprise": "surprise",
        "neutral": "neutral",
        "calm": "neutral",
    }
    return mapping.get(normalized, "neutral")


def _frontend_scores(raw: dict[str, Any]) -> dict[str, float]:
    source_metadata = dict(raw.get("source_metadata", {}))
    scores = source_metadata.get("scores")
    if isinstance(scores, dict):
        return {label: round(float(scores.get(label, 0.0)), 4) for label in _FRONTEND_LABELS}
    ranked = {str(label): float(score) for label, score in raw.get("ranked_emotions", [])}
    return {label: round(float(ranked.get(label, 0.0)), 4) for label in _FRONTEND_LABELS}


def _context_tags(dominant_signals: list[str]) -> list[str]:
    tag_map = {
        "gratitude_warmth": "gratitude",
        "pride_growth": "pride",
        "relief_release": "relief",
        "connection_need": "connection_need",
        "mixed_emotions": "mixed_state",
        "positive_affect": "positive_moment",
    }
    return list(dict.fromkeys(tag_map[signal] for signal in dominant_signals if signal in tag_map))


def _response_provider_name(raw_provider_name: str) -> str:
    normalized = raw_provider_name.strip().casefold()
    if "local_xlmr" in normalized:
        return "local_xlmr+contextual_enrichment"
    return raw_provider_name


def _secondary_labels_from_scores(
    primary_label: str,
    scores: dict[str, float],
    threshold: float,
) -> list[str]:
    secondary_threshold = max(0.2, threshold * 0.6)
    neutral_secondary_threshold = max(0.45, threshold * 0.9)
    labels: list[str] = []
    for label, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
        if label == primary_label:
            continue
        if label == "neutral":
            if score < neutral_secondary_threshold:
                continue
        elif score < secondary_threshold:
            continue
        labels.append(label)
        if len(labels) >= 2:
            break
    return labels


def _boost_scores_with_signals(scores: dict[str, float], dominant_signals: list[str]) -> dict[str, float]:
    boosted = dict(scores)
    signal_set = set(dominant_signals)
    if "gratitude_warmth" in signal_set:
        boosted["joy"] = max(boosted.get("joy", 0.0), 0.62)
    if "pride_growth" in signal_set:
        boosted["joy"] = max(boosted.get("joy", 0.0), 0.68)
    if "relief_release" in signal_set:
        boosted["joy"] = max(boosted.get("joy", 0.0), 0.58)
    if "connection_need" in signal_set:
        boosted["sadness"] = max(boosted.get("sadness", 0.0), 0.52)
    if "anxiety_activation" in signal_set or "overwhelm_load" in signal_set:
        boosted["fear"] = max(boosted.get("fear", 0.0), 0.58)
    if "deadline_pressure" in signal_set:
        boosted["fear"] = max(boosted.get("fear", 0.0), 0.62)
        boosted["sadness"] = max(boosted.get("sadness", 0.0), 0.22)
    if "anger_friction" in signal_set:
        boosted["anger"] = max(boosted.get("anger", 0.0), 0.58)
    if "mixed_emotions" in signal_set:
        boosted["sadness"] = max(boosted.get("sadness", 0.0), 0.34)
        boosted["joy"] = max(boosted.get("joy", 0.0), 0.34)
    return {label: round(boosted.get(label, 0.0), 4) for label in _FRONTEND_LABELS}


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
    if "deadline_pressure" in dominant_signal_set and (
        stress_score >= 0.52 or "overwhelm_load" in dominant_signal_set or "anxiety_activation" in dominant_signal_set
    ):
        return "stress_supportive"
    if "anger_friction" in dominant_signal_set and "overwhelm_load" not in dominant_signal_set:
        return "validating_gentle"
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
    computed_response_mode = _infer_response_mode(
        valence_score=valence_score,
        energy_score=energy_score,
        stress_score=stress_score,
        risk_level=risk_level,
        dominant_signals=dominant_signals,
    )
    response_mode = str(raw.get("response_mode", computed_response_mode))
    primary_label = str(raw.get("primary_label", raw.get("primary_emotion", "neutral")))
    scores = _boost_scores_with_signals(_frontend_scores(raw), dominant_signals)
    threshold = raw.get("threshold")
    source_metadata = dict(raw.get("source_metadata", {}))
    if threshold is None:
        threshold = source_metadata.get("threshold")
    if threshold is None:
        threshold = 0.5
    scored_labels = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    primary_label = scored_labels[0][0] if scored_labels else primary_label
    secondary_labels = _secondary_labels_from_scores(primary_label, scores, float(threshold))
    all_labels = [label for label, score in scored_labels if score >= float(threshold)]
    if not all_labels and scored_labels and scored_labels[0][1] > 0:
        all_labels = [scored_labels[0][0]]
    confidence = round(max(confidence, scored_labels[0][1] if scored_labels else confidence), 2)
    if (
        response_mode == "supportive_reflective"
        and primary_label == "joy"
        and "positive_affect" in dominant_signals
        and valence_score >= 0.34
        and stress_score <= 0.34
    ):
        response_mode = "celebratory_warm"
    internal_primary = _internalize_label(primary_label, dominant_signals, stress_score)
    internal_secondary = list(
        dict.fromkeys(
            _internalize_label(label, dominant_signals, stress_score)
            for label in secondary_labels
            if _internalize_label(label, dominant_signals, stress_score) != internal_primary
        )
    )
    if response_mode == "stress_supportive":
        internal_secondary = list(
            dict.fromkeys(
                _internalize_label(label, dominant_signals, stress_score)
                for label in secondary_labels
                if _internalize_label(label, dominant_signals, stress_score) != internal_primary
            )
        )
    context_tags = [str(item) for item in raw.get("context_tags", _context_tags(dominant_signals))]
    return {
        "primary_label": primary_label,
        "secondary_labels": secondary_labels,
        "all_labels": all_labels,
        "scores": scores,
        "threshold": float(threshold) if threshold is not None else None,
        "valence_score": valence_score,
        "energy_score": energy_score,
        "stress_score": stress_score,
        "social_need_score": social_need_score,
        "confidence": confidence,
        "dominant_signals": dominant_signals,
        "context_tags": context_tags,
        "enrichment_notes": [str(item) for item in raw.get("enrichment_notes", [])],
        "response_mode": response_mode,
        "language": normalize_language_code(str(raw.get("language", "en"))),
        "primary_emotion": internal_primary,
        "secondary_emotions": internal_secondary,
        "source": str(raw.get("source", "text")),
        "provider_name": _response_provider_name(str(raw.get("provider_name", "unknown"))),
        "source_metadata": source_metadata,
    }


def analyze_emotion(transcript: str, risk_level: str = "low", audio_path: str | None = None) -> dict[str, object]:
    normalized = _normalize_text(transcript)
    canonical = infer_emotion_signals(transcript, audio_path=audio_path)

    dominant_signals = list(dict.fromkeys(
        _PRIMARY_SIGNAL_MAP.get(canonical.primary_emotion, ["subtle_signal"]) + _secondary_signals_from_text(normalized)
    ))
    if (
        {"pride_growth", "gratitude_warmth", "relief_release"} & set(dominant_signals)
        or {"joy", "gratitude"} & set(canonical.secondary_emotions)
    ) and "positive_affect" not in dominant_signals:
        dominant_signals.append("positive_affect")
    if canonical.secondary_emotions and "mixed_emotions" not in dominant_signals:
        primary_polarity = _EMOTION_POLARITY.get(canonical.primary_emotion, 0)
        secondary_polarity = _EMOTION_POLARITY.get(canonical.secondary_emotions[0], 0)
        if primary_polarity != 0 and secondary_polarity != 0 and primary_polarity != secondary_polarity:
            dominant_signals.append("mixed_emotions")

    fear_score = float(dict(canonical.source_metadata.get("scores", {})).get("fear", 0.0))
    return normalize_emotion_analysis(
        {
            "primary_label": canonical.primary_emotion,
            "secondary_labels": canonical.secondary_emotions,
            "all_labels": canonical.raw_model_labels,
            "scores": dict(canonical.source_metadata.get("scores", {})),
            "threshold": canonical.source_metadata.get("threshold"),
            "valence_score": canonical.valence,
            "energy_score": canonical.energy,
            "stress_score": _derive_stress_score(
                normalized=normalized,
                base_stress=canonical.stress,
                fear_score=fear_score,
                dominant_signals=dominant_signals,
                risk_level=risk_level,
            ),
            "social_need_score": _derive_social_need_score(canonical.primary_emotion, normalized),
            "confidence": canonical.confidence,
            "dominant_signals": dominant_signals,
            "context_tags": _context_tags(dominant_signals),
            "language": canonical.language,
            "primary_emotion": canonical.primary_emotion,
            "secondary_emotions": canonical.secondary_emotions,
            "source": canonical.source,
            "provider_name": canonical.provider_name,
            "source_metadata": canonical.source_metadata,
        },
        risk_level=risk_level,
    )
