from collections import Counter

from app.services.companion_core.schemas import EmotionalMemoryRecord, WeeklyInsight


def build_weekly_insight(user_id: str, records: list[EmotionalMemoryRecord]) -> WeeklyInsight:
    if not records:
        return WeeklyInsight(
            user_id=user_id,
            total_checkins=0,
            emotional_trend="insufficient_data",
            suggested_reflection_focus="A few more honest check-ins will make the pattern clearer.",
            records_considered_for_insight=0,
            summary="No check-ins yet this week. A few honest moments are enough to start seeing patterns.",
            insight_summary_text="No check-ins yet this week. A few honest moments are enough to start seeing patterns.",
        )

    ordered_records = sorted(records, key=lambda record: record.timestamp)
    period_start = ordered_records[0].timestamp
    period_end = ordered_records[-1].timestamp
    negative_events = [
        record.normalized_state.event_type
        for record in ordered_records
        if record.insight_features.is_negative_checkin
    ]
    positive_events = [
        record.normalized_state.event_type
        for record in ordered_records
        if record.insight_features.is_positive_checkin
    ]
    stress_contexts = [
        record.normalized_state.social_context
        for record in ordered_records
        if record.insight_features.high_stress_flag
    ]
    relational_patterns = [
        record.normalized_state.event_type
        for record in ordered_records
        if record.insight_features.social_support_signal
    ]
    dominant_emotions = [
        emotion
        for emotion, _count in Counter(record.normalized_state.primary_emotion for record in ordered_records).most_common(3)
    ]
    common_negative_triggers = [item for item, _count in Counter(negative_events).most_common(3)]
    common_positive_anchors = [item for item, _count in Counter(positive_events).most_common(3)]
    recurring_contexts = [item for item, _count in Counter(record.normalized_state.social_context for record in ordered_records).most_common(3)]
    stress_heavy_contexts = [item for item, _count in Counter(stress_contexts).most_common(3)]
    recurring_relational_patterns = [item for item, _count in Counter(relational_patterns).most_common(3)]
    avg_valence = sum(record.normalized_state.valence for record in ordered_records) / len(ordered_records)
    if len(ordered_records) < 3:
        emotional_trend = "insufficient_data"
    elif avg_valence >= 0.2:
        emotional_trend = "leaning_positive"
    elif avg_valence <= -0.2:
        emotional_trend = "leaning_heavy"
    else:
        emotional_trend = "mixed"

    if len(ordered_records) < 3:
        summary = (
            "There is not much data yet, but these check-ins already give a starting point. "
            "A few more moments like this will make the weekly picture more useful."
        )
        reflection_focus = "Keep noticing what situations tend to shift your mood most clearly."
    elif common_negative_triggers and common_positive_anchors:
        summary = (
            f"This week shows a mix of strain and support. The heavier pattern has often been {common_negative_triggers[0]}, "
            f"while a steadier point has often come from {common_positive_anchors[0]}."
        )
        reflection_focus = f"Notice what helps the week feel more like {common_positive_anchors[0]} when {common_negative_triggers[0]} shows up."
    elif common_negative_triggers:
        summary = (
            f"This week has leaned heavier. A recurring strain point has been {common_negative_triggers[0]}, "
            "which may be worth noticing gently rather than judging."
        )
        reflection_focus = f"Pay attention to what usually surrounds {common_negative_triggers[0]} and what helps it soften, even a little."
    elif common_positive_anchors:
        summary = (
            f"This week has included some bright points. A recurring positive anchor has been {common_positive_anchors[0]}, "
            "which seems worth keeping in view."
        )
        reflection_focus = f"Keep track of what makes {common_positive_anchors[0]} easier to return to."
    else:
        summary = "This week looks mixed but usable. A few more check-ins would make the pattern clearer."
        reflection_focus = "A simple note about what was happening around each check-in may help the pattern come into view."

    return WeeklyInsight(
        user_id=user_id,
        period_start=period_start,
        period_end=period_end,
        total_checkins=len(ordered_records),
        emotional_trend=emotional_trend,
        common_negative_triggers=common_negative_triggers,
        common_positive_anchors=common_positive_anchors,
        recurring_contexts=recurring_contexts,
        stress_heavy_contexts=stress_heavy_contexts,
        recurring_relational_patterns=recurring_relational_patterns,
        dominant_emotions=dominant_emotions,
        suggested_reflection_focus=reflection_focus,
        records_considered_for_insight=len(ordered_records),
        summary=summary,
        insight_summary_text=summary,
    )
