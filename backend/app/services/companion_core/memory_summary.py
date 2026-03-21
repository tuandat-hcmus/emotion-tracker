from collections import Counter

from app.services.companion_core.schemas import EmotionalMemoryRecord, MemorySummary


def build_memory_summary(records: list[EmotionalMemoryRecord]) -> MemorySummary:
    if not records:
        return MemorySummary()

    negative_patterns = [
        record.normalized_state.event_type
        for record in records
        if record.insight_features.is_negative_checkin
    ]
    positive_patterns = [
        record.normalized_state.event_type
        for record in records
        if record.insight_features.is_positive_checkin
    ]
    recurring_triggers = [item for item, count in Counter(negative_patterns + positive_patterns).most_common(3) if count >= 2]
    recurring_social_contexts = [
        item
        for item, count in Counter(record.normalized_state.social_context for record in records).most_common(3)
        if count >= 2
    ]
    last_state = records[-1].normalized_state
    if last_state.valence >= 0.2:
        last_direction = "positive"
    elif last_state.valence <= -0.15:
        last_direction = "negative"
    else:
        last_direction = "mixed"

    return MemorySummary(
        recent_checkin_count=len(records),
        dominant_negative_patterns=[item for item, _count in Counter(negative_patterns).most_common(3)],
        dominant_positive_patterns=[item for item, _count in Counter(positive_patterns).most_common(3)],
        recurring_triggers=recurring_triggers,
        recurring_social_contexts=recurring_social_contexts,
        last_seen_emotional_direction=last_direction,
        pattern_detected=bool(recurring_triggers or recurring_social_contexts),
    )
