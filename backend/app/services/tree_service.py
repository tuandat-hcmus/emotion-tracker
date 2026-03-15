from collections import Counter
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.models.tree_state import TreeState
from app.models.tree_state_event import TreeStateEvent
from app.schemas.user import TreeTimelineItemResponse, TreeTimelineResponse


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def _derive_tree_visuals(vitality_score: int, risk_level: str) -> tuple[str, str, str]:
    if vitality_score >= 75:
        stage = "blooming"
    elif vitality_score >= 50:
        stage = "growing"
    elif vitality_score >= 25:
        stage = "sapling"
    else:
        stage = "bare"

    if vitality_score >= 70:
        leaf_state = "lush"
    elif vitality_score >= 45:
        leaf_state = "steady"
    elif vitality_score >= 20:
        leaf_state = "thinning"
    else:
        leaf_state = "fallen"

    if risk_level == "high":
        weather_state = "storm"
    elif risk_level == "medium" or vitality_score < 35:
        weather_state = "rainy"
    elif vitality_score >= 70:
        weather_state = "sunny"
    else:
        weather_state = "partly_cloudy"

    return stage, leaf_state, weather_state


def _calculate_vitality_delta(valence_score: float, stress_score: float, risk_level: str) -> int:
    base_delta = round(valence_score * 12 - stress_score * 8)
    if risk_level == "high":
        base_delta -= 14
    elif risk_level == "medium":
        base_delta -= 6
    return max(-18, min(12, base_delta))


def _calculate_streak_days(checkin_dates: list[date]) -> int:
    if not checkin_dates:
        return 0

    unique_dates = sorted(set(checkin_dates))
    streak = 1
    for index in range(len(unique_dates) - 1, 0, -1):
        if unique_dates[index] - unique_dates[index - 1] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def recompute_tree_for_user(db: Session, user_id: str) -> TreeState | None:
    db.flush()
    processed_entries = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.user_id == user_id,
            JournalEntry.processing_status == "processed",
        )
        .order_by(JournalEntry.created_at.asc(), JournalEntry.id.asc())
        .all()
    )

    db.query(TreeStateEvent).filter(TreeStateEvent.user_id == user_id).delete(synchronize_session=False)

    if not processed_entries:
        db.query(TreeState).filter(TreeState.user_id == user_id).delete(synchronize_session=False)
        db.flush()
        return None

    state = db.query(TreeState).filter(TreeState.user_id == user_id).one_or_none()
    if state is None:
        state = TreeState(user_id=user_id)
        db.add(state)

    vitality_score = 50
    checkin_dates: list[date] = []

    for entry in processed_entries:
        checkin_date = (entry.updated_at or entry.created_at).date()
        checkin_dates.append(checkin_date)
        delta = _calculate_vitality_delta(
            valence_score=entry.valence_score or 0.0,
            stress_score=entry.stress_score or 0.0,
            risk_level=entry.risk_level or "low",
        )
        vitality_score = _clamp_score(vitality_score + delta)
        current_stage, leaf_state, weather_state = _derive_tree_visuals(
            vitality_score,
            entry.risk_level or "low",
        )
        db.add(
            TreeStateEvent(
                user_id=user_id,
                entry_id=entry.id,
                event_date=checkin_date,
                vitality_delta=delta,
                vitality_score_after=vitality_score,
                current_stage=current_stage,
                leaf_state=leaf_state,
                weather_state=weather_state,
            )
        )

    db.flush()
    latest_date = checkin_dates[-1]
    latest_event = (
        db.query(TreeStateEvent)
        .filter(TreeStateEvent.user_id == user_id)
        .order_by(TreeStateEvent.event_date.desc(), TreeStateEvent.created_at.desc())
        .first()
    )

    state.vitality_score = vitality_score
    state.streak_days = _calculate_streak_days(checkin_dates)
    state.current_stage = latest_event.current_stage if latest_event else "sapling"
    state.leaf_state = latest_event.leaf_state if latest_event else "steady"
    state.weather_state = latest_event.weather_state if latest_event else "partly_cloudy"
    state.last_checkin_date = latest_date
    db.flush()
    return state


def build_tree_timeline(db: Session, user_id: str, days: int) -> TreeTimelineResponse:
    processed_entries = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.user_id == user_id,
            JournalEntry.processing_status == "processed",
        )
        .order_by(JournalEntry.created_at.asc(), JournalEntry.id.asc())
        .all()
    )
    events = (
        db.query(TreeStateEvent)
        .filter(TreeStateEvent.user_id == user_id)
        .order_by(TreeStateEvent.event_date.asc(), TreeStateEvent.created_at.asc())
        .all()
    )

    if not processed_entries:
        return TreeTimelineResponse(user_id=user_id, days=days, items=[])

    latest_date = max((entry.updated_at or entry.created_at).date() for entry in processed_entries)
    cutoff_date = latest_date - timedelta(days=days - 1)

    daily_entries: dict[date, list[JournalEntry]] = {}
    for entry in processed_entries:
        entry_date = (entry.updated_at or entry.created_at).date()
        if entry_date >= cutoff_date:
            daily_entries.setdefault(entry_date, []).append(entry)

    daily_events: dict[date, list[TreeStateEvent]] = {}
    for event in events:
        if event.event_date >= cutoff_date:
            daily_events.setdefault(event.event_date, []).append(event)

    items: list[TreeTimelineItemResponse] = []
    for day in sorted(daily_entries):
        entries = daily_entries[day]
        day_events = daily_events.get(day, [])
        average_valence = round(
            sum(entry.valence_score or 0.0 for entry in entries) / len(entries),
            2,
        ) if entries else None
        average_stress = round(
            sum(entry.stress_score or 0.0 for entry in entries) / len(entries),
            2,
        ) if entries else None
        emotion_counts = Counter(entry.emotion_label for entry in entries if entry.emotion_label)
        dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else None
        last_event = day_events[-1] if day_events else None
        items.append(
            TreeTimelineItemResponse(
                date=day.isoformat(),
                entry_count=len(entries),
                average_valence_score=average_valence,
                average_stress_score=average_stress,
                dominant_emotion_label=dominant_emotion,
                vitality_score_after_day=last_event.vitality_score_after if last_event else None,
                leaf_state=last_event.leaf_state if last_event else None,
                weather_state=last_event.weather_state if last_event else None,
            )
        )

    return TreeTimelineResponse(user_id=user_id, days=days, items=items)
