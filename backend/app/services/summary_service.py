import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.schemas.user import UserSummaryResponse
from app.services.journal_service import (
    get_entry_context_tags,
    get_entry_dominant_signals,
    get_entry_memory_summary,
    get_entry_normalized_state,
    get_entry_support_strategy,
)


def build_user_summary(db: Session, user_id: str, days: int) -> UserSummaryResponse:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user_id, JournalEntry.created_at >= cutoff)
        .order_by(JournalEntry.created_at.desc())
        .all()
    )

    emotion_counts = Counter(
        entry.emotion_label for entry in entries if entry.emotion_label
    )
    risk_counts = Counter(entry.risk_level or "low" for entry in entries)
    stable_risk_counts = {
        "low": risk_counts.get("low", 0),
        "medium": risk_counts.get("medium", 0),
        "high": risk_counts.get("high", 0),
    }

    topics: list[str] = []
    for entry in entries:
        if entry.topic_tags_text:
            topics.extend(json.loads(entry.topic_tags_text))
    top_topics = [topic for topic, _count in Counter(topics).most_common(3)]

    valence_values = [entry.valence_score for entry in entries if entry.valence_score is not None]
    energy_values = [entry.energy_score for entry in entries if entry.energy_score is not None]
    stress_values = [entry.stress_score for entry in entries if entry.stress_score is not None]

    def average(values: list[float]) -> float | None:
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    latest_entry_at = entries[0].created_at.isoformat() if entries else None
    dominant_emotional_patterns = [label for label, _count in emotion_counts.most_common(3)]

    recurring_candidates: list[str] = []
    workload_patterns: Counter[str] = Counter()
    positive_anchor_counter: Counter[str] = Counter()
    high_stress_entry_count = 0

    for entry in entries:
        state = get_entry_normalized_state(entry)
        strategy = get_entry_support_strategy(entry)
        memory_summary = get_entry_memory_summary(entry)
        event_type = state.get("event_type")
        if isinstance(event_type, str) and event_type:
            recurring_candidates.append(event_type)

        context_tags = get_entry_context_tags(entry)
        recurring_candidates.extend(context_tags)
        recurring_from_memory = memory_summary.get("recurring_triggers")
        if isinstance(recurring_from_memory, list):
            recurring_candidates.extend(str(item) for item in recurring_from_memory)

        signals = set(get_entry_dominant_signals(entry))
        if (
            entry.response_mode == "stress_supportive"
            or strategy.get("strategy_type") == "stress_supportive"
            or "deadline_pressure" in signals
            or event_type == "deadline_pressure"
        ):
            workload_patterns["deadline_pressure"] += 1
        if "work/school" in context_tags:
            workload_patterns["workload_pressure"] += 1

        if entry.emotion_label == "joy" or "positive_affect" in signals:
            if context_tags:
                positive_anchor_counter.update(context_tags)
            dominant_positive_patterns = memory_summary.get("dominant_positive_patterns")
            if isinstance(dominant_positive_patterns, list):
                positive_anchor_counter.update(str(item) for item in dominant_positive_patterns)
            else:
                positive_anchor_counter["positive_moment"] += 1

        if (entry.stress_score or 0.0) >= 0.7:
            high_stress_entry_count += 1

    recurring_triggers = [item for item, count in Counter(recurring_candidates).most_common(4) if count >= 2]
    workload_deadline_patterns = [item for item, count in workload_patterns.most_common(3) if count >= 1]
    positive_anchors = [item for item, _count in positive_anchor_counter.most_common(4)]
    high_stress_frequency = round(high_stress_entry_count / len(entries), 2) if entries else 0.0

    if len(valence_values) >= 2:
        midpoint = max(1, len(valence_values) // 2)
        first_avg = average(valence_values[:midpoint]) or 0.0
        second_avg = average(valence_values[midpoint:]) or 0.0
        if second_avg - first_avg >= 0.18:
            emotional_direction_trend = "improving"
        elif second_avg - first_avg <= -0.18:
            emotional_direction_trend = "heavier"
        else:
            emotional_direction_trend = "mixed"
    else:
        emotional_direction_trend = "mixed"

    if not entries:
        summary_text = "No recent check-ins yet. A few honest entries are enough to start a useful pattern."
    else:
        fragments = []
        if dominant_emotional_patterns:
            fragments.append(f"Most common recently: {dominant_emotional_patterns[0]}.")
        if recurring_triggers:
            fragments.append(f"Repeated pressure or context showed up around {recurring_triggers[0]}.")
        if positive_anchors:
            fragments.append(f"A steadier anchor appeared around {positive_anchors[0]}.")
        if high_stress_frequency >= 0.5:
            fragments.append(f"High stress appeared in {int(high_stress_frequency * 100)}% of recent check-ins.")
        elif emotional_direction_trend == "improving":
            fragments.append("The recent emotional direction looks lighter.")
        summary_text = " ".join(fragments) if fragments else "Recent check-ins look mixed but usable."

    return UserSummaryResponse(
        user_id=user_id,
        days=days,
        total_entries=len(entries),
        emotion_counts=dict(emotion_counts),
        average_valence_score=average(valence_values),
        average_energy_score=average(energy_values),
        average_stress_score=average(stress_values),
        top_topics=top_topics,
        risk_counts=stable_risk_counts,
        latest_entry_at=latest_entry_at,
        dominant_emotional_patterns=dominant_emotional_patterns,
        recurring_triggers=recurring_triggers,
        workload_deadline_patterns=workload_deadline_patterns,
        positive_anchors=positive_anchors,
        emotional_direction_trend=emotional_direction_trend,
        high_stress_frequency=high_stress_frequency,
        summary_text=summary_text,
    )
