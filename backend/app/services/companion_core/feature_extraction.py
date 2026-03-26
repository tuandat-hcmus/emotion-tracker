from app.services.companion_core.schemas import InsightFeatures, NormalizedEmotionalState


def extract_insight_features(state: NormalizedEmotionalState) -> InsightFeatures:
    negative = state.valence <= -0.15
    positive = state.valence >= 0.2
    return InsightFeatures(
        is_negative_checkin=negative,
        is_positive_checkin=positive,
        work_trigger=state.social_context == "work_or_school" or "work/school" in state.topic_tags,
        relationship_strain=state.event_type in {"conflict_or_disappointment", "responsibility_tension", "uncertain_romantic_rejection", "other_person_distress"}
        or (state.social_context in {"friendship", "family", "romantic_relationship"} and negative),
        deadline_related=state.event_type == "deadline_pressure",
        loneliness_related=state.event_type == "loneliness_or_disconnection"
        or state.primary_emotion == "loneliness",
        positive_anchor_candidate=positive and state.stress <= 0.35,
        social_support_signal=state.social_context in {"friendship", "family", "romantic_relationship"},
        high_stress_flag=state.stress >= 0.6,
    )
