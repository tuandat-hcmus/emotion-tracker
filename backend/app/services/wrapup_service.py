import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.models.wrapup_snapshot import WrapupSnapshot
from app.schemas.me import (
    MonthlyWrapupDetailResponse,
    MonthlyWrapupDistributionsResponse,
    MonthlyWrapupDistributionItemResponse,
    MonthlyWrapupHeadlineCardResponse,
    MonthlyWrapupOverviewResponse,
    MonthlyWrapupPatternItemResponse,
    MonthlyWrapupPatternListsResponse,
    MonthlyWrapupPeriodResponse,
    MonthlyWrapupStatsResponse,
    MonthlyWrapupVisualHintsResponse,
    MonthlyWrapupWeeklyMetricResponse,
    WrapupConsistencyResponse,
    WrapupDayHighlightResponse,
    WrapupInsightCardResponse,
    WrapupPayloadResponse,
    WrapupSnapshotResponse,
    WrapupStreakHighlightResponse,
    WrapupTrendBlockResponse,
)
from app.services.calendar_service import (
    _average,
    _top_topics,
    list_entries_for_local_date_range,
    resolve_user_timezone,
    resolve_user_today,
    to_local_date,
)
from app.services.preferences_service import get_or_create_preferences
from app.services.journal_service import (
    get_entry_context_tags,
    get_entry_dominant_signals,
    get_entry_memory_summary,
    get_entry_normalized_state,
    get_entry_support_strategy,
)

_POSITIVE_EMOTIONS = {"joy", "gratitude", "love", "relief", "calm", "hopeful", "content"}
_LOW_ENERGY_EMOTIONS = {"sadness", "loneliness", "grief", "tired", "fatigue", "numb"}
_HIGH_STRESS_EMOTIONS = {"stress", "anxiety", "fear", "anger", "overwhelmed", "frustration", "panic"}


def _period_bounds(period_type: str, anchor_date: date) -> tuple[date, date]:
    if period_type == "week":
        start = anchor_date - timedelta(days=anchor_date.weekday())
        return start, start + timedelta(days=6)
    start = anchor_date.replace(day=1)
    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)
    return start, next_month - timedelta(days=1)


def _daily_group(entries: list[JournalEntry], tzinfo) -> dict[date, list[JournalEntry]]:
    grouped: dict[date, list[JournalEntry]] = {}
    for entry in entries:
        grouped.setdefault(to_local_date(entry.created_at, tzinfo), []).append(entry)
    return grouped


def _build_day_highlight(entries: list[JournalEntry], day: date, *, positive: bool) -> WrapupDayHighlightResponse:
    average_valence = _average([entry.valence_score for entry in entries])
    average_stress = _average([entry.stress_score for entry in entries])
    emotion_counts = Counter(entry.emotion_label for entry in entries if entry.emotion_label)
    dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else None
    risk_level = max(
        (entry.risk_level for entry in entries if entry.risk_level),
        default=None,
        key=lambda level: {"low": 1, "medium": 2, "high": 3}.get(level, 0),
    )
    if positive:
        return WrapupDayHighlightResponse(
            date=day.isoformat(),
            average_valence_score=average_valence,
            dominant_emotion_label=dominant_emotion,
            risk_level=risk_level,
        )
    return WrapupDayHighlightResponse(
        date=day.isoformat(),
        average_stress_score=average_stress,
        dominant_emotion_label=dominant_emotion,
        risk_level=risk_level,
    )


def _streak_lengths(checkin_days: list[date], period_end: date) -> WrapupStreakHighlightResponse:
    unique_days = sorted(set(checkin_days))
    if not unique_days:
        return WrapupStreakHighlightResponse(longest_streak_days=0, current_streak_days=0)

    longest = 1
    current_run = 1
    for index in range(1, len(unique_days)):
        if unique_days[index] - unique_days[index - 1] == timedelta(days=1):
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 1

    current_streak = 0
    pointer = period_end
    checkin_day_set = set(unique_days)
    while pointer in checkin_day_set:
        current_streak += 1
        pointer -= timedelta(days=1)

    return WrapupStreakHighlightResponse(longest_streak_days=longest, current_streak_days=current_streak)


def _notable_shift(entries: list[JournalEntry]) -> str:
    scored_entries = [entry for entry in entries if entry.valence_score is not None or entry.stress_score is not None]
    if len(scored_entries) < 2:
        return "stable"

    midpoint = len(scored_entries) // 2
    first_half = scored_entries[:midpoint]
    second_half = scored_entries[midpoint:]
    first_valence = _average([entry.valence_score for entry in first_half])
    second_valence = _average([entry.valence_score for entry in second_half])
    first_stress = _average([entry.stress_score for entry in first_half])
    second_stress = _average([entry.stress_score for entry in second_half])

    if (second_stress or 0.0) - (first_stress or 0.0) >= 0.2:
        return "under_strain"
    if (second_valence or 0.0) - (first_valence or 0.0) >= 0.2:
        return "improving"
    if abs((second_valence or 0.0) - (first_valence or 0.0)) >= 0.15 or abs((second_stress or 0.0) - (first_stress or 0.0)) >= 0.15:
        return "fluctuating"
    return "stable"


def _closing_message(period_type: str, total_entries: int, notable_shift: str) -> str:
    if total_entries == 0:
        return f"No {period_type} data yet. A single check-in is enough to start the pattern."
    if notable_shift == "improving":
        return f"This {period_type} shows signs of recovery. Keep the routines that helped most."
    if notable_shift == "under_strain":
        return f"This {period_type} carried a heavier load. Aim for steadier support before the next cycle."
    if notable_shift == "fluctuating":
        return f"This {period_type} moved around noticeably. Consistent check-ins will make the trend clearer."
    return f"This {period_type} looks relatively steady. Small consistent check-ins will keep the signal useful."


def _rounded_ratio(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total, 2)


def _emotional_direction_trend(entries: list[JournalEntry]) -> str:
    scored_entries = [entry for entry in entries if entry.valence_score is not None]
    if len(scored_entries) < 2:
        return "mixed"
    first_half = scored_entries[: max(1, len(scored_entries) // 2)]
    second_half = scored_entries[max(1, len(scored_entries) // 2) :]
    first_average = _average([entry.valence_score for entry in first_half]) or 0.0
    second_average = _average([entry.valence_score for entry in second_half]) or 0.0
    shift = second_average - first_average
    if shift >= 0.18:
        return "improving"
    if shift <= -0.18:
        return "heavier"
    return "mixed"


def _dominant_emotional_patterns(entries: list[JournalEntry]) -> list[str]:
    labels = [entry.emotion_label for entry in entries if entry.emotion_label]
    return [label for label, _count in Counter(labels).most_common(3)]


def _recurring_triggers(entries: list[JournalEntry]) -> list[str]:
    trigger_candidates: list[str] = []
    for entry in entries:
        state = get_entry_normalized_state(entry)
        event_type = state.get("event_type")
        if isinstance(event_type, str) and event_type:
            trigger_candidates.append(event_type)
        trigger_candidates.extend(get_entry_context_tags(entry))
        memory_summary = get_entry_memory_summary(entry)
        recurring_triggers = memory_summary.get("recurring_triggers")
        if isinstance(recurring_triggers, list):
            trigger_candidates.extend(str(item) for item in recurring_triggers)
    return [item for item, count in Counter(trigger_candidates).most_common(4) if count >= 2]


def _workload_deadline_patterns(entries: list[JournalEntry]) -> list[str]:
    patterns: Counter[str] = Counter()
    for entry in entries:
        signals = set(get_entry_dominant_signals(entry))
        context_tags = set(get_entry_context_tags(entry))
        state = get_entry_normalized_state(entry)
        strategy = get_entry_support_strategy(entry)
        event_type = str(state.get("event_type") or "")
        if (
            entry.response_mode == "stress_supportive"
            or strategy.get("strategy_type") == "stress_supportive"
            or "deadline_pressure" in signals
            or event_type == "deadline_pressure"
        ):
            patterns["deadline_pressure"] += 1
        if "work/school" in context_tags or "work_trigger" in signals:
            patterns["workload_pressure"] += 1
    return [item for item, count in patterns.most_common(3) if count >= 1]


def _positive_anchors(entries: list[JournalEntry]) -> list[str]:
    anchors: Counter[str] = Counter()
    for entry in entries:
        context_tags = get_entry_context_tags(entry)
        signals = set(get_entry_dominant_signals(entry))
        memory_summary = get_entry_memory_summary(entry)
        if entry.emotion_label == "joy" or "positive_affect" in signals:
            if context_tags:
                anchors.update(context_tags)
            dominant_positive_patterns = memory_summary.get("dominant_positive_patterns")
            if isinstance(dominant_positive_patterns, list):
                anchors.update(str(item) for item in dominant_positive_patterns)
            else:
                anchors["positive_moment"] += 1
    return [item for item, _count in anchors.most_common(4)]


def _high_stress_entry_count(entries: list[JournalEntry]) -> int:
    count = 0
    for entry in entries:
        state = get_entry_normalized_state(entry)
        if (entry.stress_score or 0.0) >= 0.7 or bool(state.get("stress", 0.0) >= 0.7):
            count += 1
    return count


def _summary_text(
    *,
    period_type: str,
    total_entries: int,
    direction: str,
    dominant_patterns: list[str],
    recurring_triggers: list[str],
    positive_anchors: list[str],
    high_stress_frequency: float,
) -> str:
    if total_entries == 0:
        return f"No {period_type} check-ins yet. A few honest entries are enough to start a useful pattern."
    if total_entries == 1:
        return (
            f"This {period_type} has only one check-in so far. The strongest visible signal is "
            f"{dominant_patterns[0] if dominant_patterns else 'mixed emotion'}, and more entries will make the pattern clearer."
        )
    parts = []
    if dominant_patterns:
        parts.append(f"The most common emotional pattern this {period_type} was {dominant_patterns[0]}.")
    if recurring_triggers:
        parts.append(f"Repeated pressure showed up around {recurring_triggers[0]}.")
    if positive_anchors:
        parts.append(f"A steadier anchor appeared around {positive_anchors[0]}.")
    if high_stress_frequency >= 0.5:
        parts.append(f"High stress was present in {int(high_stress_frequency * 100)}% of check-ins.")
    elif direction == "improving":
        parts.append(f"The emotional direction looks lighter toward the end of the {period_type}.")
    elif direction == "heavier":
        parts.append(f"The emotional direction looks heavier toward the end of the {period_type}.")
    return " ".join(parts) if parts else f"This {period_type} looks mixed but usable."


def _build_insight_cards(
    *,
    dominant_patterns: list[str],
    recurring_triggers: list[str],
    workload_patterns: list[str],
    positive_anchors: list[str],
    direction: str,
    high_stress_frequency: float,
) -> list[WrapupInsightCardResponse]:
    cards: list[WrapupInsightCardResponse] = []
    cards.append(
        WrapupInsightCardResponse(
            kind="dominant_patterns",
            title="Dominant emotional patterns",
            summary="Most common emotional labels seen in the period.",
            emphasis=dominant_patterns[0] if dominant_patterns else None,
            items=dominant_patterns,
        )
    )
    if recurring_triggers:
        cards.append(
            WrapupInsightCardResponse(
                kind="recurring_triggers",
                title="Recurring triggers",
                summary="Repeated context or event signals detected from stored snapshots.",
                emphasis=recurring_triggers[0],
                items=recurring_triggers,
            )
        )
    if workload_patterns:
        cards.append(
            WrapupInsightCardResponse(
                kind="workload_patterns",
                title="Workload and deadline patterns",
                summary="Pressure-related signals surfaced repeatedly across check-ins.",
                emphasis=workload_patterns[0],
                items=workload_patterns,
            )
        )
    if positive_anchors:
        cards.append(
            WrapupInsightCardResponse(
                kind="positive_anchors",
                title="Positive anchors",
                summary="Steadier or supportive signals that appeared in the same period.",
                emphasis=positive_anchors[0],
                items=positive_anchors,
            )
        )
    cards.append(
        WrapupInsightCardResponse(
            kind="stress_trend",
            title="Stress trend",
            summary="How often high-stress states showed up in the selected period.",
            emphasis=direction,
            items=[f"high_stress_frequency:{high_stress_frequency:.2f}"],
        )
    )
    return cards


def _serialize_snapshot(snapshot: WrapupSnapshot) -> WrapupSnapshotResponse:
    return WrapupSnapshotResponse(
        id=snapshot.id,
        user_id=snapshot.user_id,
        period_type=snapshot.period_type,
        period_start=snapshot.period_start,
        period_end=snapshot.period_end,
        payload=WrapupPayloadResponse(**json.loads(snapshot.payload_text)),
        generated_at=snapshot.generated_at,
        created_at=snapshot.created_at,
        updated_at=snapshot.updated_at,
    )


def _month_label(period_start: date) -> str:
    return period_start.strftime("%B %Y")


def _counter_weight(count: int, total: int) -> float | None:
    if total <= 0:
        return None
    return round(count / total, 2)


def _emotion_counter(entries: list[JournalEntry]) -> Counter[str]:
    return Counter(entry.emotion_label for entry in entries if entry.emotion_label)


def _recurring_trigger_counter(entries: list[JournalEntry]) -> Counter[str]:
    trigger_candidates: Counter[str] = Counter()
    for entry in entries:
        entry_candidates: set[str] = set()
        state = get_entry_normalized_state(entry)
        event_type = state.get("event_type")
        if isinstance(event_type, str) and event_type:
            entry_candidates.add(event_type)
        entry_candidates.update(get_entry_context_tags(entry))
        memory_summary = get_entry_memory_summary(entry)
        recurring_triggers = memory_summary.get("recurring_triggers")
        if isinstance(recurring_triggers, list):
            entry_candidates.update(str(item) for item in recurring_triggers if str(item))
        trigger_candidates.update(entry_candidates)
    return trigger_candidates


def _workload_pattern_counter(entries: list[JournalEntry]) -> Counter[str]:
    patterns: Counter[str] = Counter()
    for entry in entries:
        signals = set(get_entry_dominant_signals(entry))
        context_tags = set(get_entry_context_tags(entry))
        state = get_entry_normalized_state(entry)
        strategy = get_entry_support_strategy(entry)
        event_type = str(state.get("event_type") or "")
        if (
            entry.response_mode == "stress_supportive"
            or strategy.get("strategy_type") == "stress_supportive"
            or "deadline_pressure" in signals
            or event_type == "deadline_pressure"
        ):
            patterns["deadline_pressure"] += 1
        if "work/school" in context_tags or "work_trigger" in signals:
            patterns["workload_pressure"] += 1
    return patterns


def _positive_anchor_counter(entries: list[JournalEntry]) -> Counter[str]:
    anchors: Counter[str] = Counter()
    for entry in entries:
        context_tags = get_entry_context_tags(entry)
        signals = set(get_entry_dominant_signals(entry))
        memory_summary = get_entry_memory_summary(entry)
        if entry.emotion_label == "joy" or "positive_affect" in signals:
            if context_tags:
                anchors.update(context_tags)
            dominant_positive_patterns = memory_summary.get("dominant_positive_patterns")
            if isinstance(dominant_positive_patterns, list):
                anchors.update(str(item) for item in dominant_positive_patterns if str(item))
            elif not context_tags:
                anchors["positive_moment"] += 1
    return anchors


def _pattern_items(counter: Counter[str], total: int, limit: int, kind: str) -> list[MonthlyWrapupPatternItemResponse]:
    items: list[MonthlyWrapupPatternItemResponse] = []
    for label, count in counter.most_common(limit):
        if count <= 0:
            continue
        icon_key, color_token = _semantic_tokens(kind, label)
        items.append(
            MonthlyWrapupPatternItemResponse(
                label=label,
                count=count,
                weight=_counter_weight(count, total),
                icon_key=icon_key,
                color_token=color_token,
            )
        )
    return items


def _emotion_semantics(label: str | None) -> tuple[str, str]:
    normalized = (label or "").strip().lower()
    if normalized in _POSITIVE_EMOTIONS:
        return ("sun", "soft_yellow")
    if normalized in _LOW_ENERGY_EMOTIONS:
        return ("cloud", "lavender")
    if normalized in _HIGH_STRESS_EMOTIONS:
        return ("wave", "sunset_orange")
    if normalized in {"calm", "peace", "steady"}:
        return ("leaf", "calm_blue")
    return ("heart", "warm_pink")


def _semantic_tokens(kind: str, label: str | None = None, value: str | None = None) -> tuple[str, str]:
    normalized_label = (label or "").strip().lower()
    normalized_value = (value or "").strip().lower()
    merged = " ".join(part for part in (normalized_label, normalized_value) if part)

    if kind in {"most_frequent_emotion", "dominant_emotional_patterns"}:
        return _emotion_semantics(label)
    if kind in {"most_common_trigger", "highest_stress_pattern", "workload_deadline_patterns"}:
        return ("wave", "sunset_orange")
    if kind in {"strongest_positive_anchor", "positive_anchors"}:
        return ("sun", "soft_yellow")
    if kind in {"consistency_streak"}:
        return ("seed", "forest_green")
    if kind in {"emotional_shift"}:
        if normalized_value == "improving":
            return ("leaf", "forest_green")
        if normalized_value == "heavier" or normalized_value == "under_strain":
            return ("cloud", "lavender")
        return ("wave", "calm_blue")
    if kind in {"month_theme"}:
        if any(token in merged for token in ("work", "deadline", "school", "pressure")):
            return ("wave", "sunset_orange")
        if any(token in merged for token in ("rest", "family", "friend", "gratitude", "calm")):
            return ("heart", "warm_pink")
        return ("spark", "warm_pink")
    if any(token in merged for token in ("deadline", "work", "school", "pressure", "stress")):
        return ("wave", "sunset_orange")
    if any(token in merged for token in ("joy", "gratitude", "love", "support", "friend", "family")):
        return ("sun", "soft_yellow")
    if any(token in merged for token in ("sad", "lonely", "tired", "low")):
        return ("cloud", "lavender")
    return ("heart", "warm_pink")


def _month_theme(top_topic: str | None, dominant_emotion: str | None) -> str | None:
    if top_topic:
        return top_topic
    return dominant_emotion


def _longest_gap_days(checkin_days: list[date], period_start: date, period_end: date) -> int | None:
    if period_end < period_start:
        return None
    if not checkin_days:
        return (period_end - period_start).days + 1

    unique_days = sorted(set(checkin_days))
    longest = max((unique_days[0] - period_start).days, (period_end - unique_days[-1]).days)
    for index in range(1, len(unique_days)):
        gap_days = (unique_days[index] - unique_days[index - 1]).days - 1
        longest = max(longest, gap_days)
    return longest


def _weekly_metrics(
    entries: list[JournalEntry],
    period_start: date,
    period_end: date,
    tzinfo,
) -> tuple[list[MonthlyWrapupWeeklyMetricResponse], list[MonthlyWrapupWeeklyMetricResponse]]:
    stress_items: list[MonthlyWrapupWeeklyMetricResponse] = []
    count_items: list[MonthlyWrapupWeeklyMetricResponse] = []
    cursor = period_start
    week_index = 1

    while cursor <= period_end:
        week_end = min(cursor + timedelta(days=6), period_end)
        week_entries = [
            entry
            for entry in entries
            if cursor <= to_local_date(entry.created_at, tzinfo) <= week_end
        ]
        count = len(week_entries)
        metric = MonthlyWrapupWeeklyMetricResponse(
            week_label=f"Week {week_index}",
            date_from=cursor.isoformat(),
            date_to=week_end.isoformat(),
            avg_stress_score=_average([entry.stress_score for entry in week_entries]),
            count=count,
        )
        stress_items.append(metric)
        count_items.append(metric.model_copy())
        cursor = week_end + timedelta(days=1)
        week_index += 1

    return stress_items, count_items


def _emotion_distribution(emotion_counts: Counter[str], total_entries: int) -> list[MonthlyWrapupDistributionItemResponse]:
    if total_entries <= 0:
        return []
    return [
        MonthlyWrapupDistributionItemResponse(
            label=label,
            count=count,
            percent=round((count / total_entries) * 100, 1),
        )
        for label, count in emotion_counts.most_common(5)
    ]


def _intensity_level(high_stress_frequency: float, average_stress_score: float | None) -> str:
    if high_stress_frequency >= 0.5 or (average_stress_score or 0.0) >= 0.7:
        return "high"
    if high_stress_frequency >= 0.2 or (average_stress_score or 0.0) >= 0.4:
        return "moderate"
    return "low"


def _month_visual_hints(
    dominant_emotion: str | None,
    high_stress_frequency: float,
    average_stress_score: float | None,
    month_theme: str | None,
) -> MonthlyWrapupVisualHintsResponse:
    theme_icon, theme_color = _semantic_tokens("month_theme", month_theme, dominant_emotion)
    return MonthlyWrapupVisualHintsResponse(
        month_mood_color=theme_color if dominant_emotion or month_theme else "calm_blue",
        month_theme_icon=theme_icon,
        intensity_level=_intensity_level(high_stress_frequency, average_stress_score),
    )


def _headline_cards(
    *,
    total_entries: int,
    emotion_counts: Counter[str],
    trigger_counter: Counter[str],
    positive_anchor_counter: Counter[str],
    workload_counter: Counter[str],
    longest_streak_days: int,
    emotional_direction_trend: str,
    month_theme: str | None,
    high_stress_frequency: float,
) -> list[MonthlyWrapupHeadlineCardResponse]:
    cards: list[MonthlyWrapupHeadlineCardResponse] = []

    top_emotion, top_emotion_count = (emotion_counts.most_common(1)[0] if emotion_counts else (None, 0))
    if top_emotion:
        icon_key, color_token = _semantic_tokens("most_frequent_emotion", top_emotion)
        cards.append(
            MonthlyWrapupHeadlineCardResponse(
                id="most_frequent_emotion",
                title="Most frequent emotion",
                subtitle="Emotion seen most often this month",
                value=top_emotion,
                supporting_text=f"{top_emotion_count} of {total_entries} check-ins",
                icon_key=icon_key,
                color_token=color_token,
                priority=1,
                source_type="emotion_label",
            )
        )

    top_trigger, top_trigger_count = (trigger_counter.most_common(1)[0] if trigger_counter else (None, 0))
    if top_trigger and top_trigger_count >= 2:
        icon_key, color_token = _semantic_tokens("most_common_trigger", top_trigger)
        cards.append(
            MonthlyWrapupHeadlineCardResponse(
                id="most_common_trigger",
                title="Most common trigger",
                subtitle="Repeated trigger across stored check-ins",
                value=top_trigger,
                supporting_text=f"Seen {top_trigger_count} times",
                icon_key=icon_key,
                color_token=color_token,
                priority=2,
                source_type="memory_summary",
            )
        )

    top_anchor, top_anchor_count = (positive_anchor_counter.most_common(1)[0] if positive_anchor_counter else (None, 0))
    if top_anchor:
        icon_key, color_token = _semantic_tokens("strongest_positive_anchor", top_anchor)
        cards.append(
            MonthlyWrapupHeadlineCardResponse(
                id="strongest_positive_anchor",
                title="Strongest positive anchor",
                subtitle="Supportive pattern that appeared in positive moments",
                value=top_anchor,
                supporting_text=f"Referenced {top_anchor_count} times",
                icon_key=icon_key,
                color_token=color_token,
                priority=3,
                source_type="memory_summary",
            )
        )

    top_workload, top_workload_count = (workload_counter.most_common(1)[0] if workload_counter else (None, 0))
    if top_workload:
        icon_key, color_token = _semantic_tokens("highest_stress_pattern", top_workload)
        cards.append(
            MonthlyWrapupHeadlineCardResponse(
                id="highest_stress_pattern",
                title="Highest stress pattern",
                subtitle="Pressure signal repeated in stored metadata",
                value=top_workload,
                supporting_text=f"Matched {top_workload_count} entries",
                icon_key=icon_key,
                color_token=color_token,
                priority=4,
                source_type="normalized_state",
            )
        )
    elif total_entries > 0 and high_stress_frequency > 0:
        icon_key, color_token = _semantic_tokens("highest_stress_pattern", value="stress")
        cards.append(
            MonthlyWrapupHeadlineCardResponse(
                id="highest_stress_pattern",
                title="High stress presence",
                subtitle="Share of check-ins with elevated stress",
                value=f"{int(high_stress_frequency * 100)}%",
                supporting_text="Based on persisted stress scores",
                icon_key=icon_key,
                color_token=color_token,
                priority=4,
                source_type="stress_score",
            )
        )

    if longest_streak_days > 0:
        icon_key, color_token = _semantic_tokens("consistency_streak")
        cards.append(
            MonthlyWrapupHeadlineCardResponse(
                id="consistency_streak",
                title="Consistency streak",
                subtitle="Longest run of active check-in days",
                value=longest_streak_days,
                supporting_text="Measured from persisted entry dates",
                icon_key=icon_key,
                color_token=color_token,
                priority=5,
                source_type="created_at",
            )
        )

    if total_entries >= 2:
        icon_key, color_token = _semantic_tokens("emotional_shift", value=emotional_direction_trend)
        cards.append(
            MonthlyWrapupHeadlineCardResponse(
                id="emotional_shift",
                title="Emotional shift",
                subtitle="Change between the first and second half of the month",
                value=emotional_direction_trend,
                supporting_text="Derived from persisted valence scores",
                icon_key=icon_key,
                color_token=color_token,
                priority=6,
                source_type="valence_score",
            )
        )

    if month_theme:
        icon_key, color_token = _semantic_tokens("month_theme", month_theme)
        cards.append(
            MonthlyWrapupHeadlineCardResponse(
                id="month_theme",
                title="Month theme",
                subtitle="Most visible recurring theme from stored data",
                value=month_theme,
                supporting_text="Based on top topics or dominant emotion",
                icon_key=icon_key,
                color_token=color_token,
                priority=7,
                source_type="topic_tags",
            )
        )

    return sorted(cards, key=lambda card: card.priority)[:6]


def generate_wrapup_snapshot(
    db: Session,
    user_id: str,
    period_type: str,
    anchor_date: date | None = None,
) -> WrapupSnapshotResponse:
    preferences = get_or_create_preferences(db, user_id)
    tzinfo = resolve_user_timezone(preferences)
    resolved_anchor = anchor_date or resolve_user_today(preferences)
    period_start, period_end = _period_bounds(period_type, resolved_anchor)
    entries = [
        entry
        for entry in list_entries_for_local_date_range(db, user_id, period_start, period_end, tzinfo)
        if entry.processing_status == "processed"
    ]
    grouped = _daily_group(entries, tzinfo)
    emotion_counts = Counter(entry.emotion_label for entry in entries if entry.emotion_label)
    checkin_days = sorted(grouped.keys())
    strongest_positive_day = None
    heaviest_day = None
    if grouped:
        strongest_day = max(
            grouped.items(),
            key=lambda item: (_average([entry.valence_score for entry in item[1]]) or -1.0, item[0].toordinal()),
        )[0]
        heaviest = max(
            grouped.items(),
            key=lambda item: (
                max({"low": 1, "medium": 2, "high": 3}.get(entry.risk_level or "low", 1) for entry in item[1]),
                _average([entry.stress_score for entry in item[1]]) or 0.0,
                item[0].toordinal(),
            ),
        )[0]
        strongest_positive_day = _build_day_highlight(grouped[strongest_day], strongest_day, positive=True)
        heaviest_day = _build_day_highlight(grouped[heaviest], heaviest, positive=False)

    notable_shift = _notable_shift(entries)
    dominant_patterns = _dominant_emotional_patterns(entries)
    recurring_triggers = _recurring_triggers(entries)
    workload_patterns = _workload_deadline_patterns(entries)
    positive_anchors = _positive_anchors(entries)
    emotional_direction_trend = _emotional_direction_trend(entries)
    high_stress_entry_count = _high_stress_entry_count(entries)
    high_stress_frequency = _rounded_ratio(high_stress_entry_count, len(entries))
    total_days = (period_end - period_start).days + 1
    payload = WrapupPayloadResponse(
        period_type=period_type,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        total_entries=len(entries),
        total_checkin_days=len(checkin_days),
        emotion_counts=dict(emotion_counts),
        average_valence_score=_average([entry.valence_score for entry in entries]),
        average_stress_score=_average([entry.stress_score for entry in entries]),
        top_topics=_top_topics(entries),
        strongest_positive_day=strongest_positive_day,
        heaviest_day=heaviest_day,
        streak_highlight=_streak_lengths(checkin_days, period_end),
        checkin_consistency=WrapupConsistencyResponse(
            completed_days=len(checkin_days),
            total_days=total_days,
            ratio=round(len(checkin_days) / total_days, 2) if total_days else 0.0,
        ),
        notable_shift=notable_shift,
        dominant_emotional_patterns=dominant_patterns,
        recurring_triggers=recurring_triggers,
        workload_deadline_patterns=workload_patterns,
        positive_anchors=positive_anchors,
        emotional_direction_trend=emotional_direction_trend,
        high_stress_frequency=high_stress_frequency,
        summary_text=_summary_text(
            period_type=period_type,
            total_entries=len(entries),
            direction=emotional_direction_trend,
            dominant_patterns=dominant_patterns,
            recurring_triggers=recurring_triggers,
            positive_anchors=positive_anchors,
            high_stress_frequency=high_stress_frequency,
        ),
        insight_cards=_build_insight_cards(
            dominant_patterns=dominant_patterns,
            recurring_triggers=recurring_triggers,
            workload_patterns=workload_patterns,
            positive_anchors=positive_anchors,
            direction=emotional_direction_trend,
            high_stress_frequency=high_stress_frequency,
        ),
        trend_block=WrapupTrendBlockResponse(
            emotional_direction_trend=emotional_direction_trend,
            high_stress_frequency=high_stress_frequency,
            high_stress_entry_count=high_stress_entry_count,
            workload_pattern_detected=bool(workload_patterns),
            positive_anchor_count=len(positive_anchors),
            recurring_trigger_count=len(recurring_triggers),
        ),
        closing_message=_closing_message(period_type, len(entries), notable_shift),
    )

    snapshot = (
        db.query(WrapupSnapshot)
        .filter(
            WrapupSnapshot.user_id == user_id,
            WrapupSnapshot.period_type == period_type,
            WrapupSnapshot.period_start == period_start,
            WrapupSnapshot.period_end == period_end,
        )
        .one_or_none()
    )
    if snapshot is None:
        snapshot = WrapupSnapshot(
            user_id=user_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            payload_text=payload.model_dump_json(),
            generated_at=datetime.now(timezone.utc),
        )
        db.add(snapshot)
    else:
        snapshot.payload_text = payload.model_dump_json()
        snapshot.generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(snapshot)
    return _serialize_snapshot(snapshot)


def get_latest_wrapup_snapshot(
    db: Session,
    user_id: str,
    period_type: str,
) -> WrapupSnapshotResponse:
    snapshot = (
        db.query(WrapupSnapshot)
        .filter(
            WrapupSnapshot.user_id == user_id,
            WrapupSnapshot.period_type == period_type,
        )
        .order_by(WrapupSnapshot.generated_at.desc(), WrapupSnapshot.created_at.desc())
        .first()
    )
    if snapshot is None:
        return generate_wrapup_snapshot(db, user_id, period_type)
    return _serialize_snapshot(snapshot)


def get_monthly_wrapup_snapshot(
    db: Session,
    user_id: str,
    *,
    year: int,
    month: int,
) -> WrapupSnapshotResponse | None:
    period_start, period_end = _period_bounds("month", date(year, month, 1))
    snapshot = (
        db.query(WrapupSnapshot)
        .filter(
            WrapupSnapshot.user_id == user_id,
            WrapupSnapshot.period_type == "month",
            WrapupSnapshot.period_start == period_start,
            WrapupSnapshot.period_end == period_end,
        )
        .order_by(WrapupSnapshot.generated_at.desc(), WrapupSnapshot.created_at.desc())
        .first()
    )
    if snapshot is None:
        return None
    return _serialize_snapshot(snapshot)


def build_monthly_wrapup_detail(
    db: Session,
    user_id: str,
    year: int,
    month: int,
) -> MonthlyWrapupDetailResponse:
    anchor = date(year, month, 1)
    preferences = get_or_create_preferences(db, user_id)
    tzinfo = resolve_user_timezone(preferences)
    period_start, period_end = _period_bounds("month", anchor)
    entries = [
        entry
        for entry in list_entries_for_local_date_range(db, user_id, period_start, period_end, tzinfo)
        if entry.processing_status == "processed"
    ]
    grouped = _daily_group(entries, tzinfo)
    checkin_days = sorted(grouped.keys())
    emotion_counts = _emotion_counter(entries)
    trigger_counter = _recurring_trigger_counter(entries)
    positive_anchor_counter = _positive_anchor_counter(entries)
    workload_counter = _workload_pattern_counter(entries)
    dominant_patterns = _pattern_items(emotion_counts, len(entries), 4, "dominant_emotional_patterns")
    recurring_triggers = _pattern_items(
        Counter({label: count for label, count in trigger_counter.items() if count >= 2}),
        len(entries),
        4,
        "most_common_trigger",
    )
    positive_anchors = _pattern_items(positive_anchor_counter, len(entries), 4, "positive_anchors")
    workload_patterns = _pattern_items(workload_counter, len(entries), 4, "workload_deadline_patterns")
    emotional_direction_trend = _emotional_direction_trend(entries)
    high_stress_entry_count = _high_stress_entry_count(entries)
    high_stress_frequency = _rounded_ratio(high_stress_entry_count, len(entries))
    streak_highlight = _streak_lengths(checkin_days, period_end)
    average_stress_score = _average([entry.stress_score for entry in entries])
    top_topics = _top_topics(entries)
    dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else None
    month_theme = _month_theme(top_topics[0] if top_topics else None, dominant_emotion)
    weekly_stress_trend, weekly_checkin_counts = _weekly_metrics(entries, period_start, period_end, tzinfo)
    headline_cards = _headline_cards(
        total_entries=len(entries),
        emotion_counts=emotion_counts,
        trigger_counter=Counter({item.label: item.count for item in recurring_triggers}),
        positive_anchor_counter=positive_anchor_counter,
        workload_counter=workload_counter,
        longest_streak_days=streak_highlight.longest_streak_days,
        emotional_direction_trend=emotional_direction_trend,
        month_theme=month_theme,
        high_stress_frequency=high_stress_frequency,
    )

    return MonthlyWrapupDetailResponse(
        period=MonthlyWrapupPeriodResponse(
            year=year,
            month=month,
            label=_month_label(period_start),
            date_from=period_start.isoformat(),
            date_to=period_end.isoformat(),
        ),
        overview=MonthlyWrapupOverviewResponse(
            summary_text=_summary_text(
                period_type="month",
                total_entries=len(entries),
                direction=emotional_direction_trend,
                dominant_patterns=[item.label for item in dominant_patterns],
                recurring_triggers=[item.label for item in recurring_triggers],
                positive_anchors=[item.label for item in positive_anchors],
                high_stress_frequency=high_stress_frequency,
            ),
            dominant_emotion=dominant_emotion,
            emotional_direction_trend=emotional_direction_trend,
            overall_checkin_count=len(entries),
            high_stress_frequency=high_stress_frequency,
        ),
        headline_cards=headline_cards,
        stats=MonthlyWrapupStatsResponse(
            total_checkins=len(entries),
            active_days=len(checkin_days),
            avg_stress_score=average_stress_score,
            top_emotion=dominant_emotion,
            top_trigger=recurring_triggers[0].label if recurring_triggers else None,
            top_positive_anchor=positive_anchors[0].label if positive_anchors else None,
            longest_gap_days=_longest_gap_days(checkin_days, period_start, period_end),
            best_streak_days=streak_highlight.longest_streak_days,
        ),
        distributions=MonthlyWrapupDistributionsResponse(
            emotion_distribution=_emotion_distribution(emotion_counts, len(entries)),
            weekly_stress_trend=weekly_stress_trend,
            weekly_checkin_counts=weekly_checkin_counts,
        ),
        pattern_lists=MonthlyWrapupPatternListsResponse(
            recurring_triggers=recurring_triggers,
            positive_anchors=positive_anchors,
            workload_deadline_patterns=workload_patterns,
            dominant_emotional_patterns=dominant_patterns,
        ),
        visual_hints=_month_visual_hints(
            dominant_emotion=dominant_emotion,
            high_stress_frequency=high_stress_frequency,
            average_stress_score=average_stress_score,
            month_theme=month_theme,
        ),
    )


def get_latest_monthly_wrapup_detail(
    db: Session,
    user_id: str,
) -> MonthlyWrapupDetailResponse:
    snapshot = (
        db.query(WrapupSnapshot)
        .filter(
            WrapupSnapshot.user_id == user_id,
            WrapupSnapshot.period_type == "month",
        )
        .order_by(WrapupSnapshot.generated_at.desc(), WrapupSnapshot.created_at.desc())
        .first()
    )
    if snapshot is not None:
        return build_monthly_wrapup_detail(db, user_id, snapshot.period_start.year, snapshot.period_start.month)

    preferences = get_or_create_preferences(db, user_id)
    today = resolve_user_today(preferences)
    return build_monthly_wrapup_detail(db, user_id, today.year, today.month)


def get_latest_wrapup_meta(db: Session, user_id: str) -> tuple[datetime | None, datetime | None]:
    weekly = (
        db.query(WrapupSnapshot.generated_at)
        .filter(WrapupSnapshot.user_id == user_id, WrapupSnapshot.period_type == "week")
        .order_by(WrapupSnapshot.generated_at.desc(), WrapupSnapshot.created_at.desc())
        .first()
    )
    monthly = (
        db.query(WrapupSnapshot.generated_at)
        .filter(WrapupSnapshot.user_id == user_id, WrapupSnapshot.period_type == "month")
        .order_by(WrapupSnapshot.generated_at.desc(), WrapupSnapshot.created_at.desc())
        .first()
    )
    return (weekly[0] if weekly else None, monthly[0] if monthly else None)
