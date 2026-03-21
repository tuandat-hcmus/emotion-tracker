import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, object_session

from app.models.journal_entry import JournalEntry
from app.models.processing_attempt import ProcessingAttempt
from app.services.ai_contract_service import build_ai_contract


def get_entry_or_404(db: Session, entry_id: str) -> JournalEntry:
    entry = db.get(JournalEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    return entry


def get_latest_attempt(db: Session, entry_id: str) -> ProcessingAttempt | None:
    return (
        db.query(ProcessingAttempt)
        .filter(ProcessingAttempt.entry_id == entry_id)
        .order_by(ProcessingAttempt.started_at.desc(), ProcessingAttempt.id.desc())
        .first()
    )


def serialize_entry(entry: JournalEntry) -> dict[str, object]:
    response_metadata = json.loads(entry.response_metadata_text) if entry.response_metadata_text else None
    emotion_metadata = response_metadata.get("emotion_analysis", {}) if isinstance(response_metadata, dict) else {}
    session = object_session(entry)
    latest_attempt = get_latest_attempt(session, entry.id) if session is not None else None
    source_type = (
        str(response_metadata.get("source_type"))
        if isinstance(response_metadata, dict) and response_metadata.get("source_type")
        else ("voice" if entry.audio_path else "text")
    )
    transcript_source = (
        str(response_metadata.get("transcript_source"))
        if isinstance(response_metadata, dict) and response_metadata.get("transcript_source")
        else None
    )
    transcript_provider = (
        str(response_metadata.get("transcript_provider"))
        if isinstance(response_metadata, dict) and response_metadata.get("transcript_provider")
        else None
    )
    ai_analysis_complete = (
        entry.processing_status == "processed"
        and entry.response_metadata_text is not None
        and entry.emotion_label is not None
        and entry.ai_response is not None
    )
    ai_contract = build_ai_contract(
        emotion_analysis={
            "primary_label": emotion_metadata.get("primary_label", entry.emotion_label),
            "secondary_labels": list(emotion_metadata.get("secondary_labels", [])),
            "all_labels": list(emotion_metadata.get("all_labels", [])),
            "scores": dict(emotion_metadata.get("scores", {})),
            "threshold": emotion_metadata.get("threshold"),
            "valence_score": entry.valence_score,
            "energy_score": entry.energy_score,
            "stress_score": entry.stress_score,
            "social_need_score": entry.social_need_score,
            "confidence": entry.emotion_confidence,
            "dominant_signals": json.loads(entry.dominant_signals_text) if entry.dominant_signals_text else [],
            "context_tags": list(emotion_metadata.get("context_tags", [])),
            "enrichment_notes": list(emotion_metadata.get("enrichment_notes", [])),
            "response_mode": entry.response_mode,
            "language": emotion_metadata.get("language"),
            "source": emotion_metadata.get("source"),
            "provider_name": emotion_metadata.get("provider_name"),
        },
        risk_level=entry.risk_level,
        risk_flags=json.loads(entry.risk_flags_text) if entry.risk_flags_text else [],
        topic_tags=json.loads(entry.topic_tags_text) if entry.topic_tags_text else [],
        response_plan=response_metadata.get("response_plan") if isinstance(response_metadata, dict) else None,
        empathetic_response=entry.empathetic_response,
        follow_up_question=(
            response_metadata.get("follow_up_question") if isinstance(response_metadata, dict) else None
        ),
        gentle_suggestion=entry.gentle_suggestion,
        quote=response_metadata.get("quote") if isinstance(response_metadata, dict) else None,
        ai_response=entry.ai_response,
        normalized_state=response_metadata.get("normalized_state") if isinstance(response_metadata, dict) else None,
        support_strategy=response_metadata.get("support_strategy") if isinstance(response_metadata, dict) else None,
        memory_summary=response_metadata.get("memory_summary") if isinstance(response_metadata, dict) else None,
        insight_features=response_metadata.get("insight_features") if isinstance(response_metadata, dict) else None,
    )
    return {
        "entry_id": entry.id,
        "status": entry.processing_status,
        "user_id": entry.user_id,
        "session_type": entry.session_type,
        "source_type": source_type,
        "audio_path": entry.audio_path,
        "transcript_text": entry.transcript_text,
        "transcript_confidence": entry.transcript_confidence,
        "transcript_source": transcript_source,
        "transcript_provider": transcript_provider,
        "ai_analysis_complete": ai_analysis_complete,
        "latest_attempt_status": latest_attempt.status if latest_attempt is not None else None,
        "processing_started_at": latest_attempt.started_at if latest_attempt is not None else None,
        "processing_finished_at": latest_attempt.finished_at if latest_attempt is not None else None,
        "ai_response": entry.ai_response,
        "primary_label": emotion_metadata.get("primary_label", entry.emotion_label),
        "secondary_labels": list(emotion_metadata.get("secondary_labels", [])),
        "all_labels": list(emotion_metadata.get("all_labels", [])),
        "scores": dict(emotion_metadata.get("scores", {})),
        "threshold": emotion_metadata.get("threshold"),
        "valence_score": entry.valence_score,
        "energy_score": entry.energy_score,
        "stress_score": entry.stress_score,
        "social_need_score": entry.social_need_score,
        "confidence": entry.emotion_confidence,
        "dominant_signals": json.loads(entry.dominant_signals_text) if entry.dominant_signals_text else [],
        "context_tags": list(emotion_metadata.get("context_tags", [])),
        "enrichment_notes": list(emotion_metadata.get("enrichment_notes", [])),
        "response_mode": entry.response_mode,
        "language": emotion_metadata.get("language"),
        "source": emotion_metadata.get("source"),
        "provider_name": emotion_metadata.get("provider_name"),
        "empathetic_response": entry.empathetic_response,
        "follow_up_question": response_metadata.get("follow_up_question") if isinstance(response_metadata, dict) else None,
        "gentle_suggestion": entry.gentle_suggestion,
        "quote_text": entry.quote_text,
        "response_metadata": response_metadata,
        "topic_tags": json.loads(entry.topic_tags_text) if entry.topic_tags_text else [],
        "risk_level": entry.risk_level,
        "risk_flags": json.loads(entry.risk_flags_text) if entry.risk_flags_text else [],
        "ai": ai_contract.model_dump(),
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }
