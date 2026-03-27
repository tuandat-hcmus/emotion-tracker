import json
from datetime import date, datetime, time, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.schemas.user import JournalHistoryItemResponse


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


def deserialize_response_metadata(entry: JournalEntry) -> dict[str, object]:
    if not entry.response_metadata_text:
        return {}
    try:
        metadata = json.loads(entry.response_metadata_text)
    except json.JSONDecodeError:
        return {}
    return metadata if isinstance(metadata, dict) else {}


def get_entry_source_type(entry: JournalEntry) -> str:
    metadata = deserialize_response_metadata(entry)
    source_type = metadata.get("source_type")
    if isinstance(source_type, str) and source_type:
        return source_type
    return "voice" if entry.audio_path else "text"


def get_entry_secondary_labels(entry: JournalEntry) -> list[str]:
    metadata = deserialize_response_metadata(entry)
    emotion_analysis = metadata.get("emotion_analysis")
    if isinstance(emotion_analysis, dict):
        secondary_labels = emotion_analysis.get("secondary_labels")
        if isinstance(secondary_labels, list):
            return [str(label) for label in secondary_labels]
    return []


def build_excerpt(text: str | None, max_length: int = 120) -> str | None:
    if text is None:
        return None
    normalized = " ".join(text.split()).strip()
    if not normalized:
        return None
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 1].rstrip() + "…"


def get_entry_emotion_analysis(entry: JournalEntry) -> dict[str, object]:
    metadata = deserialize_response_metadata(entry)
    emotion_analysis = metadata.get("emotion_analysis")
    if isinstance(emotion_analysis, dict):
        return emotion_analysis
    return {}


def get_entry_normalized_state(entry: JournalEntry) -> dict[str, object]:
    metadata = deserialize_response_metadata(entry)
    normalized_state = metadata.get("normalized_state")
    if isinstance(normalized_state, dict):
        return normalized_state
    return {}


def get_entry_support_strategy(entry: JournalEntry) -> dict[str, object]:
    metadata = deserialize_response_metadata(entry)
    strategy = metadata.get("support_strategy")
    if isinstance(strategy, dict):
        return strategy
    return {}


def get_entry_memory_summary(entry: JournalEntry) -> dict[str, object]:
    metadata = deserialize_response_metadata(entry)
    memory_summary = metadata.get("memory_summary")
    if isinstance(memory_summary, dict):
        return memory_summary
    return {}


def get_entry_dominant_signals(entry: JournalEntry) -> list[str]:
    emotion_analysis = get_entry_emotion_analysis(entry)
    dominant_signals = emotion_analysis.get("dominant_signals")
    if isinstance(dominant_signals, list):
        return [str(item) for item in dominant_signals]
    return json.loads(entry.dominant_signals_text) if entry.dominant_signals_text else []


def get_entry_context_tags(entry: JournalEntry) -> list[str]:
    emotion_analysis = get_entry_emotion_analysis(entry)
    context_tags = emotion_analysis.get("context_tags")
    if isinstance(context_tags, list):
        return [str(item) for item in context_tags]
    return []


def serialize_history_item(entry: JournalEntry, *, local_date: date) -> JournalHistoryItemResponse:
    return JournalHistoryItemResponse(
        id=entry.id,
        entry_id=entry.id,
        status=entry.processing_status,
        session_type=entry.session_type,
        source_type=get_entry_source_type(entry),
        local_date=local_date.isoformat(),
        transcript_excerpt=build_excerpt(entry.transcript_text),
        ai_response_excerpt=build_excerpt(entry.ai_response),
        primary_label=entry.emotion_label,
        secondary_labels=get_entry_secondary_labels(entry),
        stress_score=entry.stress_score,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )
