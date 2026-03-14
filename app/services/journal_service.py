import json
from datetime import date, datetime, time, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry


def list_user_entries(
    db: Session,
    user_id: str,
    limit: int,
    offset: int,
    session_type: str | None = None,
    status: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> tuple[int, list[JournalEntry]]:
    query = db.query(JournalEntry).filter(JournalEntry.user_id == user_id)

    if session_type:
        query = query.filter(JournalEntry.session_type == session_type)
    if status:
        query = query.filter(JournalEntry.processing_status == status)
    if from_date:
        query = query.filter(
            JournalEntry.created_at >= datetime.combine(from_date, time.min, tzinfo=timezone.utc)
        )
    if to_date:
        query = query.filter(
            JournalEntry.created_at <= datetime.combine(to_date, time.max, tzinfo=timezone.utc)
        )

    total = query.with_entities(func.count(JournalEntry.id)).scalar() or 0
    items = (
        query.order_by(JournalEntry.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return total, items


def deserialize_topic_tags(entry: JournalEntry) -> list[str]:
    return json.loads(entry.topic_tags_text) if entry.topic_tags_text else []


def deserialize_risk_flags(entry: JournalEntry) -> list[str]:
    return json.loads(entry.risk_flags_text) if entry.risk_flags_text else []
