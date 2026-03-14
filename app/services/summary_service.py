import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.schemas.user import UserSummaryResponse


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
    )
