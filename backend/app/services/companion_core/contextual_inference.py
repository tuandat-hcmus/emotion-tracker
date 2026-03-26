from app.services.companion_core.schemas import RenderContext


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _to_frontend_label(label: str) -> str:
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


def _apply_frontend_emotion_override(
    adjusted: dict[str, object],
    *,
    primary: str,
    secondary: list[str],
    confidence: float,
) -> None:
    primary_label = _to_frontend_label(primary)
    secondary_labels = [
        mapped
        for item in secondary
        if (mapped := _to_frontend_label(item)) != primary_label
    ]
    scores = {
        "anger": 0.02,
        "disgust": 0.01,
        "fear": 0.04,
        "joy": 0.06,
        "sadness": 0.03,
        "surprise": 0.02,
        "neutral": 0.72,
    }
    adjusted["primary_label"] = primary_label
    adjusted["secondary_labels"] = list(dict.fromkeys(secondary_labels))
    adjusted["all_labels"] = [primary_label]
    adjusted["scores"] = scores
    adjusted["confidence"] = round(max(confidence, scores[primary_label]), 2)


def align_emotion_analysis_with_context(
    emotion_analysis: dict[str, object],
    render_context: RenderContext,
) -> dict[str, object]:
    adjusted = dict(emotion_analysis)
    language = str(adjusted.get("language", "unknown"))
    if language != "en":
        return adjusted

    primary_emotion = str(adjusted.get("primary_emotion", "neutral"))
    secondary_emotions = [str(item) for item in adjusted.get("secondary_emotions", [])]
    dominant_signals = [str(item) for item in adjusted.get("dominant_signals", [])]
    confidence = float(adjusted.get("confidence", 0.0))
    valence = float(adjusted.get("valence_score", 0.0))
    energy = float(adjusted.get("energy_score", 0.0))
    stress = float(adjusted.get("stress_score", 0.0))
    social_need = float(adjusted.get("social_need_score", 0.0))
    source_metadata = dict(adjusted.get("source_metadata", {}))
    provider_name = str(adjusted.get("provider_name", "unknown"))

    def _apply(
        *,
        primary: str,
        secondary: list[str],
        next_valence: float,
        next_energy: float,
        next_stress: float,
        next_social_need: float | None,
        response_mode: str,
        next_confidence: float,
        extra_signals: list[str],
        adjustment_name: str,
    ) -> None:
        adjusted["primary_emotion"] = primary
        adjusted["secondary_emotions"] = _dedupe(secondary)
        adjusted["valence_score"] = round(next_valence, 2)
        adjusted["energy_score"] = round(next_energy, 2)
        adjusted["stress_score"] = round(next_stress, 2)
        if next_social_need is not None:
            adjusted["social_need_score"] = round(next_social_need, 2)
        adjusted["response_mode"] = response_mode
        adjusted["confidence"] = round(next_confidence, 2)
        adjusted["dominant_signals"] = _dedupe([*extra_signals, *dominant_signals])
        adjusted["context_tags"] = _dedupe([*adjusted.get("context_tags", []), adjustment_name])
        source_metadata["contextual_alignment"] = adjustment_name
        adjusted["source_metadata"] = source_metadata
        adjusted["provider_name"] = f"{provider_name}+contextual_alignment"

    if render_context.event_type == "recognition_or_praise":
        _apply(
            primary="gratitude",
            secondary=["joy", *secondary_emotions],
            next_valence=max(valence, 0.42),
            next_energy=max(energy, 0.46),
            next_stress=min(stress, 0.24),
            next_social_need=social_need,
            response_mode="celebratory_warm" if confidence >= 0.6 else "supportive_reflective",
            next_confidence=max(confidence, 0.62),
            extra_signals=["gratitude_warmth", "positive_affect"],
            adjustment_name="recognition_or_praise",
        )
        return adjusted

    if render_context.event_type == "relief_or_gratitude":
        _apply(
            primary="gratitude",
            secondary=["joy", *secondary_emotions],
            next_valence=max(valence, 0.34),
            next_energy=max(energy, 0.34),
            next_stress=min(stress, 0.22),
            next_social_need=social_need,
            response_mode="celebratory_warm",
            next_confidence=max(confidence, 0.58),
            extra_signals=["positive_affect", "relief_release"],
            adjustment_name="relief_or_gratitude",
        )
        return adjusted

    if render_context.event_type == "deadline_pressure":
        _apply(
            primary="overwhelm" if stress >= 0.56 else "anxiety",
            secondary=["anxiety", *secondary_emotions],
            next_valence=min(valence, -0.34),
            next_energy=max(energy, 0.46),
            next_stress=max(stress, 0.62),
            next_social_need=social_need,
            response_mode="stress_supportive",
            next_confidence=max(confidence, 0.6),
            extra_signals=["overwhelm_load", "deadline_pressure"],
            adjustment_name="deadline_pressure",
        )
        return adjusted

    if render_context.event_type == "other_person_distress":
        _apply(
            primary="anxiety",
            secondary=["sadness", *secondary_emotions],
            next_valence=min(valence, -0.24),
            next_energy=max(energy, 0.34),
            next_stress=max(stress, 0.42),
            next_social_need=max(social_need, 0.24),
            response_mode="supportive_reflective",
            next_confidence=max(confidence, 0.52),
            extra_signals=["anxiety_activation", "connection_need", "care_for_other"],
            adjustment_name="other_person_distress",
        )
        return adjusted

    if render_context.event_type == "loved_one_unwell":
        _apply(
            primary="anxiety",
            secondary=["sadness", *secondary_emotions],
            next_valence=min(valence, -0.28),
            next_energy=max(energy, 0.34),
            next_stress=max(stress, 0.46),
            next_social_need=max(social_need, 0.3),
            response_mode="supportive_reflective",
            next_confidence=max(confidence, 0.58),
            extra_signals=["anxiety_activation", "connection_need", "care_for_other"],
            adjustment_name="loved_one_unwell",
        )
        return adjusted

    if render_context.event_type == "responsibility_tension":
        aligned_primary = "overwhelm" if stress >= 0.72 else "anxiety"
        secondary_seed = ["sadness", "anxiety" if aligned_primary != "anxiety" else "overwhelm"]
        _apply(
            primary=aligned_primary,
            secondary=[*secondary_seed, *secondary_emotions],
            next_valence=min(valence, -0.42),
            next_energy=max(energy, 0.52),
            next_stress=max(stress, 0.64),
            next_social_need=max(social_need, 0.18),
            response_mode="validating_gentle",
            next_confidence=max(confidence, 0.64),
            extra_signals=["responsibility_tension", "guilt_tension"],
            adjustment_name="responsibility_tension",
        )
        return adjusted

    if render_context.event_type == "uncertain_romantic_rejection":
        _apply(
            primary="sadness",
            secondary=["anxiety", *secondary_emotions],
            next_valence=min(valence, -0.48),
            next_energy=max(energy, 0.3),
            next_stress=max(stress, 0.38),
            next_social_need=max(social_need, 0.26),
            response_mode="low_energy_comfort" if energy <= 0.45 else "validating_gentle",
            next_confidence=max(confidence, 0.68),
            extra_signals=["connection_need"],
            adjustment_name="uncertain_romantic_rejection",
        )
        return adjusted

    if render_context.user_stance == "worried_about_other" and primary_emotion in {"anger", "sadness", "neutral"}:
        _apply(
            primary="anxiety",
            secondary=["sadness", *secondary_emotions],
            next_valence=min(valence, -0.2),
            next_energy=max(energy, 0.3),
            next_stress=max(stress, 0.38),
            next_social_need=max(social_need, 0.2),
            response_mode="supportive_reflective",
            next_confidence=max(confidence, 0.5),
            extra_signals=["anxiety_activation", "care_for_other"],
            adjustment_name="worried_about_other",
        )
        return adjusted

    if render_context.event_type == "greeting_or_opening":
        _apply(
            primary="neutral",
            secondary=secondary_emotions,
            next_valence=max(valence, 0.0),
            next_energy=max(energy, 0.24),
            next_stress=min(stress, 0.18),
            next_social_need=max(social_need, 0.12),
            response_mode="supportive_reflective",
            next_confidence=max(confidence, 0.48),
            extra_signals=["gentle_opening"],
            adjustment_name="greeting_or_opening",
        )
        _apply_frontend_emotion_override(
            adjusted,
            primary="neutral",
            secondary=[],
            confidence=max(confidence, 0.48),
        )
    return adjusted
