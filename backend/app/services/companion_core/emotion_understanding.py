from app.services.companion_core.schemas import NormalizedEmotionalState


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def build_normalized_emotional_state(
    *,
    emotion_analysis: dict[str, object],
    render_context: dict[str, object],
    topic_tags: list[str],
    risk_level: str,
) -> NormalizedEmotionalState:
    user_stance = str(render_context.get("user_stance", "processing_self"))
    relationship_role = str(render_context["relationship_role"]) if render_context.get("relationship_role") else None
    concern_target = (str(render_context["concern_target"]) if render_context.get("concern_target") else None)
    event_type = str(render_context.get("event_type", "uncertain_mixed_state"))
    social_context = str(render_context.get("social_context", "solo"))

    primary_emotion = str(emotion_analysis.get("primary_emotion", "neutral"))
    secondary_emotions = [str(item) for item in emotion_analysis.get("secondary_emotions", [])]
    valence = float(emotion_analysis.get("valence_score", 0.0))
    energy = float(emotion_analysis.get("energy_score", 0.0))
    stress = float(emotion_analysis.get("stress_score", 0.0))
    confidence = float(emotion_analysis.get("confidence", 0.0))
    response_mode = str(emotion_analysis.get("response_mode", "supportive_reflective"))

    if event_type in {"other_person_distress", "loved_one_unwell"}:
        primary_emotion = "anxiety"
        secondary_emotions = _dedupe(["sadness", *secondary_emotions])
        valence = min(valence, -0.24)
        energy = max(energy, 0.34)
        stress = max(stress, 0.42)
        response_mode = "supportive_reflective"
    elif event_type == "responsibility_tension":
        primary_emotion = "overwhelm" if stress >= 0.72 else "anxiety"
        secondary_emotions = _dedupe(["sadness", "anxiety" if primary_emotion != "anxiety" else "overwhelm", *secondary_emotions])
        valence = min(valence, -0.42)
        energy = max(energy, 0.5)
        stress = max(stress, 0.62)
        response_mode = "validating_gentle"
    elif event_type == "recognition_or_praise":
        primary_emotion = "gratitude"
        secondary_emotions = _dedupe(["joy", *secondary_emotions])
        valence = max(valence, 0.42)
        energy = max(energy, 0.46)
        stress = min(stress, 0.24)
        response_mode = "celebratory_warm" if confidence >= 0.6 else "supportive_reflective"
    elif event_type == "deadline_pressure":
        primary_emotion = "overwhelm" if stress >= 0.68 else "anxiety"
        secondary_emotions = _dedupe(
            ["anxiety" if primary_emotion != "anxiety" else "overwhelm", *secondary_emotions]
        )
        valence = min(valence, -0.32)
        energy = max(energy, 0.48)
        stress = max(stress, 0.64)
        response_mode = "stress_supportive"
    elif event_type == "uncertain_romantic_rejection":
        primary_emotion = "sadness"
        secondary_emotions = _dedupe(["anxiety", *secondary_emotions])
        valence = min(valence, -0.48)
        energy = max(energy, 0.3)
        stress = max(stress, 0.38)
        response_mode = "low_energy_comfort" if energy <= 0.45 else "validating_gentle"

    emotion_owner = "user"
    if user_stance == "processing_self":
        if bool(render_context.get("relationship_concern")) and bool(render_context.get("other_person_state_mentioned")):
            emotion_owner = "mixed"
    else:
        emotion_owner = "user"

    owner_confidence = 0.92 if user_stance != "processing_self" else 0.62 if emotion_owner == "user" else 0.7
    target_confidence = 0.94 if concern_target and relationship_role not in {None, "named_person"} else 0.82 if concern_target else 0.0
    event_confidence = 0.9 if event_type not in {"uncertain_mixed_state"} else 0.52
    stance_confidence = 0.9 if user_stance != "processing_self" else 0.58

    return NormalizedEmotionalState(
        language=str(emotion_analysis.get("language", "en")),
        primary_emotion=primary_emotion,
        secondary_emotions=secondary_emotions,
        valence=round(valence, 2),
        energy=round(energy, 2),
        stress=round(stress, 2),
        emotion_owner=emotion_owner,
        user_stance=user_stance,
        social_context=social_context,
        event_type=event_type,
        concern_target=concern_target,
        relationship_role=relationship_role,
        uncertainty=round(1.0 - confidence, 2),
        confidence=confidence,
        owner_confidence=owner_confidence,
        event_confidence=event_confidence,
        target_confidence=target_confidence,
        stance_confidence=stance_confidence,
        response_mode=response_mode,
        risk_level=risk_level,
        topic_tags=topic_tags,
        evidence_spans=[str(item) for item in render_context.get("evidence_spans", [])],
        source_provider=str(emotion_analysis.get("provider_name", "unknown")),
    )
