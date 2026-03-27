from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.schemas.me import JournalMonthPeriodResponse, JournalMonthResponse
from app.services.calendar_service import (
    build_calendar_items,
    list_entries_for_local_date_range,
    resolve_user_timezone,
)
from app.services.journal_service import serialize_history_item
from app.services.preferences_service import get_or_create_preferences
from app.services.wrapup_service import get_monthly_wrapup_snapshot


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return start, next_month - timedelta(days=1)


def build_journal_month(
    *,
    db: Session,
    user_id: str,
    year: int,
    month: int,
) -> JournalMonthResponse:
    preferences = get_or_create_preferences(db, user_id)
    tzinfo = resolve_user_timezone(preferences)
    period_start, period_end = _month_bounds(year, month)
    calendar_items = build_calendar_items(
        db=db,
        user_id=user_id,
        start_date=period_start,
        end_date=period_end,
        tzinfo=tzinfo,
    )
    entries = list_entries_for_local_date_range(
        db=db,
        user_id=user_id,
        start_date=period_start,
        end_date=period_end,
        tzinfo=tzinfo,
    )

    history_items = [
        serialize_history_item(entry, local_date=entry.created_at.astimezone(tzinfo).date())
        for entry in entries
    ]
    history_items.sort(key=lambda item: (item.local_date, item.created_at))

    return JournalMonthResponse(
        period=JournalMonthPeriodResponse(
            year=year,
            month=month,
            label=period_start.strftime("%B %Y"),
            date_from=period_start.isoformat(),
            date_to=period_end.isoformat(),
        ),
        calendar_items=calendar_items,
        entries=history_items,
        monthly_wrapup=get_monthly_wrapup_snapshot(db, user_id, year=year, month=month),
    )
