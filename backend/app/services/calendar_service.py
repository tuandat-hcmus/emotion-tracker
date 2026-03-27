import json
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.models.user_preference import UserPreference
from app.schemas.me import CalendarDayItemResponse, CalendarResponse, CheckinStatusResponse

_RISK_ORDER = {"low": 1, "medium": 2, "high": 3}


def resolve_user_timezone(preferences: UserPreference | None) -> ZoneInfo | timezone:
    timezone_name = preferences.timezone if preferences else None
    if not timezone_name:
        return timezone.utc
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return timezone.utc


def resolve_user_today(preferences: UserPreference | None) -> date:
    return datetime.now(resolve_user_timezone(preferences)).date()


def ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_local_date(value: datetime, tzinfo: ZoneInfo | timezone) -> date:
    return ensure_aware_utc(value).astimezone(tzinfo).date()


def build_local_date_bounds(
    start_date: date,
    end_date: date,
    tzinfo: ZoneInfo | timezone,
) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(start_date, time.min, tzinfo=tzinfo).astimezone(timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=tzinfo).astimezone(timezone.utc)
    return start_dt, end_dt


def list_entries_for_local_date_range(
    db: Session,
    user_id: str,
    start_date: date,
    end_date: date,
    tzinfo: ZoneInfo | timezone,
) -> list[JournalEntry]:
    start_dt, end_dt = build_local_date_bounds(start_date, end_date, tzinfo)
    return (
        db.query(JournalEntry)
        .filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= start_dt,
            JournalEntry.created_at <= end_dt,
        )
        .order_by(JournalEntry.created_at.asc(), JournalEntry.id.asc())
        .all()
    )


def _average(values: list[float | None]) -> float | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return round(sum(filtered) / len(filtered), 2)


def _max_risk_level(entries: list[JournalEntry]) -> str | None:
    levels = [entry.risk_level for entry in entries if entry.risk_level]
    if not levels:
        return None
    return max(levels, key=lambda level: _RISK_ORDER.get(level, 0))


def _top_topics(entries: list[JournalEntry]) -> list[str]:
    topics: list[str] = []
    for entry in entries:
        if entry.topic_tags_text:
            topics.extend(json.loads(entry.topic_tags_text))
    return [topic for topic, _count in Counter(topics).most_common(3)]


def _primary_emotion(entries: list[JournalEntry]) -> str | None:
    counts = Counter(entry.emotion_label for entry in entries if entry.emotion_label)
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def _mood_color_token(
    entries: list[JournalEntry],
    average_valence_score: float | None,
    average_stress_score: float | None,
    max_risk_level: str | None,
) -> str:
    if not entries:
        return "neutral"
    if max_risk_level == "high":
        return "heavy"
    if average_stress_score is not None and average_stress_score >= 0.7:
        return "heavy"
    if average_valence_score is not None and average_valence_score >= 0.55:
        return "bright"
    if average_valence_score is not None and average_valence_score >= 0.2 and (average_stress_score or 0.0) <= 0.45:
        return "calm"
    if average_valence_score is not None and average_valence_score <= -0.25:
        return "low"
    return "neutral"


def build_checkin_status(
    db: Session,
    user_id: str,
    target_date: date,
    tzinfo: ZoneInfo | timezone,
) -> CheckinStatusResponse:
    entries = list_entries_for_local_date_range(db, user_id, target_date, target_date, tzinfo)
    latest_entry = entries[-1] if entries else None
    session_types_present = sorted({entry.session_type for entry in entries})
    return CheckinStatusResponse(
        date=target_date.isoformat(),
        has_morning_checkin=any(entry.session_type == "morning" for entry in entries),
        has_evening_checkin=any(entry.session_type == "evening" for entry in entries),
        total_entries=len(entries),
        session_types_present=session_types_present,
        latest_entry_id=latest_entry.id if latest_entry else None,
        latest_emotion_label=latest_entry.emotion_label if latest_entry else None,
        latest_risk_level=latest_entry.risk_level if latest_entry else None,
    )


def build_calendar(
    db: Session,
    user_id: str,
    days: int,
    end_date: date,
    tzinfo: ZoneInfo | timezone,
) -> CalendarResponse:
    start_date = end_date - timedelta(days=days - 1)
    items = build_calendar_items(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        tzinfo=tzinfo,
    )

    return CalendarResponse(user_id=user_id, days=days, items=items)


def build_calendar_items(
    *,
    db: Session,
    user_id: str,
    start_date: date,
    end_date: date,
    tzinfo: ZoneInfo | timezone,
) -> list[CalendarDayItemResponse]:
    entries = list_entries_for_local_date_range(db, user_id, start_date, end_date, tzinfo)

    grouped_entries: dict[date, list[JournalEntry]] = defaultdict(list)
    for entry in entries:
        grouped_entries[to_local_date(entry.created_at, tzinfo)].append(entry)

    items: list[CalendarDayItemResponse] = []
    current_date = start_date
    while current_date <= end_date:
        day_entries = grouped_entries.get(current_date, [])
        average_valence_score = _average([entry.valence_score for entry in day_entries])
        average_stress_score = _average([entry.stress_score for entry in day_entries])
        max_risk_level = _max_risk_level(day_entries)
        items.append(
            CalendarDayItemResponse(
                date=current_date.isoformat(),
                entry_count=len(day_entries),
                has_morning_checkin=any(entry.session_type == "morning" for entry in day_entries),
                has_evening_checkin=any(entry.session_type == "evening" for entry in day_entries),
                primary_emotion_label=_primary_emotion(day_entries),
                average_valence_score=average_valence_score,
                average_stress_score=average_stress_score,
                max_risk_level=max_risk_level,
                topic_tags_top=_top_topics(day_entries),
                mood_color_token=_mood_color_token(
                    day_entries,
                    average_valence_score,
                    average_stress_score,
                    max_risk_level,
                ),
            )
        )
        current_date += timedelta(days=1)

    return items
