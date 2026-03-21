from collections import Counter

from app.services.companion_core.schemas import EmotionalMemoryRecord, InsightFeatures, MemorySummary, NormalizedEmotionalState


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def refine_with_recent_context(
    *,
    emotion_analysis: dict[str, object],
    normalized_state: NormalizedEmotionalState,
    memory_summary: MemorySummary,
    insight_features: InsightFeatures,
    memory_records: list[EmotionalMemoryRecord],
    risk_level: str,
) -> tuple[dict[str, object], NormalizedEmotionalState, InsightFeatures]:
    if not memory_records:
        return emotion_analysis, normalized_state, insight_features

    refined_emotion = dict(emotion_analysis)
    refined_state = normalized_state.model_copy(deep=True)
    refined_insights = insight_features.model_copy(deep=True)

    event_counts = Counter(record.normalized_state.event_type for record in memory_records)
    context_counts = Counter(record.normalized_state.social_context for record in memory_records)
    repeated_current_event = event_counts.get(refined_state.event_type, 0) >= 1
    repeated_current_context = context_counts.get(refined_state.social_context, 0) >= 1
    recent_positive_patterns = bool(memory_summary.dominant_positive_patterns)

    if repeated_current_event:
        stress_bump = 0.08 if refined_state.event_type == "deadline_pressure" else 0.04
        refined_state.stress = round(_clamp(refined_state.stress + stress_bump), 2)
        refined_state.confidence = round(_clamp(refined_state.confidence + 0.04), 2)
        refined_state.uncertainty = round(_clamp(1.0 - refined_state.confidence), 2)
        dominant_signals = [str(item) for item in refined_emotion.get("dominant_signals", [])]
        context_tags = [str(item) for item in refined_emotion.get("context_tags", [])]
        refined_emotion["dominant_signals"] = list(dict.fromkeys([*dominant_signals, "recent_pattern_detected"]))
        refined_emotion["context_tags"] = list(dict.fromkeys([*context_tags, "recurring_trigger_hint"]))
        refined_emotion["stress_score"] = max(float(refined_emotion.get("stress_score", 0.0)), refined_state.stress)

    if repeated_current_context and refined_state.response_mode == "supportive_reflective" and refined_state.stress >= 0.55:
        refined_state.response_mode = "grounding_soft"

    if refined_state.event_type == "deadline_pressure" and repeated_current_event:
        refined_state.response_mode = "stress_supportive"

    if recent_positive_patterns and risk_level == "low" and not refined_insights.is_positive_checkin and refined_state.valence <= 0.1:
        refined_insights.positive_anchor_candidate = True

    if memory_summary.recurring_triggers and refined_state.event_type in set(memory_summary.recurring_triggers):
        refined_insights.high_stress_flag = refined_insights.high_stress_flag or refined_state.stress >= 0.7

    refined_emotion["response_mode"] = refined_state.response_mode
    return refined_emotion, refined_state, refined_insights
