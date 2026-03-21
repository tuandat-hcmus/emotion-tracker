import json
import re

from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.services.companion_core.schemas import EmotionalMemoryRecord


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_checkin_text(text: str) -> str:
    normalized = _WHITESPACE_RE.sub(" ", text).strip()
    if not normalized:
        raise ValueError("Check-in text cannot be empty")
    return normalized


def load_recent_memory_records(
    db: Session,
    *,
    user_id: str,
    limit: int = 2,
    exclude_entry_id: str | None = None,
) -> list[EmotionalMemoryRecord]:
    query = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user_id)
        .filter(JournalEntry.processing_status == "processed")
        .filter(JournalEntry.response_metadata_text.isnot(None))
        .filter(JournalEntry.transcript_text.isnot(None))
        .order_by(JournalEntry.updated_at.desc(), JournalEntry.created_at.desc(), JournalEntry.id.desc())
    )
    if exclude_entry_id is not None:
        query = query.filter(JournalEntry.id != exclude_entry_id)

    records: list[EmotionalMemoryRecord] = []
    for entry in query.limit(limit).all():
        if not entry.response_metadata_text:
            continue
        try:
            metadata = json.loads(entry.response_metadata_text)
        except json.JSONDecodeError:
            continue
        if not isinstance(metadata, dict):
            continue

        normalized_state = metadata.get("normalized_state")
        support_strategy = metadata.get("support_strategy")
        insight_features = metadata.get("insight_features")
        if not all(isinstance(item, dict) for item in (normalized_state, support_strategy, insight_features)):
            continue

        topic_tags = metadata.get("topic_tags")
        if not isinstance(topic_tags, list):
            topic_tags = json.loads(entry.topic_tags_text) if entry.topic_tags_text else []

        try:
            records.append(
                EmotionalMemoryRecord.model_validate(
                    {
                        "user_id": entry.user_id,
                        "transcript": entry.transcript_text,
                        "timestamp": entry.updated_at,
                        "language": normalized_state.get("language", "en"),
                        "normalized_state": normalized_state,
                        "support_strategy": support_strategy,
                        "topic_tags": topic_tags,
                        "risk_level": entry.risk_level or "low",
                        "suggestion_given": entry.gentle_suggestion is not None,
                        "response_provider": metadata.get("response_provider")
                        or metadata.get("emotion_analysis", {}).get("provider_name")
                        or "unknown",
                        "response_mode": entry.response_mode or normalized_state.get("response_mode", "supportive_reflective"),
                        "support_metadata": {
                            "response_goal": support_strategy.get("response_goal"),
                            "support_focus": support_strategy.get("support_focus"),
                            "entry_id": entry.id,
                        },
                        "insight_features": insight_features,
                    }
                )
            )
        except Exception:
            continue

    return records
