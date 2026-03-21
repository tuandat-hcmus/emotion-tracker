import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.models.wrapup_snapshot import WrapupSnapshot
from app.schemas.me import (
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
