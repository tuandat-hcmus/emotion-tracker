import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.journal_entry import JournalEntry
from app.models.processing_attempt import ProcessingAttempt
from app.services.ai_support_service import build_support_package
from app.services.preferences_service import get_or_create_preferences
from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError
from app.services.response_service import get_response_provider_name
from app.services.stt_service import get_stt_provider_name, transcribe_audio
from app.services.tree_service import recompute_tree_for_user


def get_entry_or_404(db: Session, entry_id: str) -> JournalEntry:
    entry = db.get(JournalEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    return entry


def serialize_entry(entry: JournalEntry) -> dict[str, object]:
    response_metadata = json.loads(entry.response_metadata_text) if entry.response_metadata_text else None
    emotion_metadata = response_metadata.get("emotion_analysis", {}) if isinstance(response_metadata, dict) else {}
    return {
        "entry_id": entry.id,
        "status": entry.processing_status,
        "user_id": entry.user_id,
        "session_type": entry.session_type,
        "audio_path": entry.audio_path,
        "transcript_text": entry.transcript_text,
        "transcript_confidence": entry.transcript_confidence,
        "ai_response": entry.ai_response,
        "emotion_label": entry.emotion_label,
        "valence_score": entry.valence_score,
        "energy_score": entry.energy_score,
        "stress_score": entry.stress_score,
        "social_need_score": entry.social_need_score,
        "confidence": entry.emotion_confidence,
        "dominant_signals": json.loads(entry.dominant_signals_text) if entry.dominant_signals_text else [],
        "response_mode": entry.response_mode,
        "language": emotion_metadata.get("language"),
        "primary_emotion": emotion_metadata.get("primary_emotion"),
        "secondary_emotions": list(emotion_metadata.get("secondary_emotions", [])),
        "source": emotion_metadata.get("source"),
        "raw_model_labels": list(emotion_metadata.get("raw_model_labels", [])),
        "provider_name": emotion_metadata.get("provider_name"),
        "empathetic_response": entry.empathetic_response,
        "gentle_suggestion": entry.gentle_suggestion,
        "quote_text": entry.quote_text,
        "response_metadata": response_metadata,
        "topic_tags": json.loads(entry.topic_tags_text) if entry.topic_tags_text else [],
        "risk_level": entry.risk_level,
        "risk_flags": json.loads(entry.risk_flags_text) if entry.risk_flags_text else [],
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


def _create_attempt(
    db: Session,
    entry: JournalEntry,
    trigger_type: str,
    override_transcript: str | None,
) -> ProcessingAttempt:
    attempt = ProcessingAttempt(
        entry_id=entry.id,
        user_id=entry.user_id,
        trigger_type=trigger_type,
        provider_stt=get_stt_provider_name(override_transcript),
        provider_response=get_response_provider_name(),
        status="started",
        used_override_transcript=bool(override_transcript),
        started_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.flush()
    return attempt


def _mark_attempt_finished(
    attempt: ProcessingAttempt,
    attempt_status: str,
    error_message: str | None = None,
) -> None:
    attempt.status = attempt_status
    attempt.error_message = error_message
    attempt.finished_at = datetime.now(timezone.utc)


def _apply_processing_results(
    db: Session,
    entry: JournalEntry,
    transcript_text: str,
    transcript_confidence: float,
) -> None:
    preferences = get_or_create_preferences(db, entry.user_id)
    support_package = build_support_package(
        transcript=transcript_text,
        user_id=entry.user_id,
        audio_path=entry.audio_path,
        quote_opt_in=preferences.quote_opt_in,
    )
    emotion_result = support_package["emotion_analysis"]
    topic_tags = support_package["topic_tags"]
    risk_level = str(support_package["risk_level"])
    risk_flags = list(support_package["risk_flags"])

    entry.transcript_text = transcript_text
    entry.transcript_confidence = transcript_confidence
    entry.ai_response = str(support_package["ai_response"])
    entry.emotion_label = str(emotion_result["label"])
    entry.valence_score = float(emotion_result["valence_score"])
    entry.energy_score = float(emotion_result["energy_score"])
    entry.stress_score = float(emotion_result["stress_score"])
    entry.social_need_score = float(emotion_result["social_need_score"])
    entry.emotion_confidence = float(emotion_result["confidence"])
    entry.dominant_signals_text = json.dumps(emotion_result["dominant_signals"], ensure_ascii=False)
    entry.topic_tags_text = json.dumps(topic_tags, ensure_ascii=False)
    entry.risk_level = risk_level
    entry.risk_flags_text = json.dumps(risk_flags, ensure_ascii=False)
    entry.response_mode = str(emotion_result["response_mode"])
    entry.empathetic_response = str(support_package["empathetic_response"])
    entry.gentle_suggestion = (
        str(support_package["gentle_suggestion"]) if support_package["gentle_suggestion"] is not None else None
    )
    quote = support_package["quote"]
    entry.quote_text = quote.short_text if quote is not None else None
    entry.response_metadata_text = json.dumps(
        {
            "emotion_analysis": {
                "language": emotion_result["language"],
                "primary_emotion": emotion_result["primary_emotion"],
                "secondary_emotions": emotion_result["secondary_emotions"],
                "social_need_score": emotion_result["social_need_score"],
                "confidence": emotion_result["confidence"],
                "dominant_signals": emotion_result["dominant_signals"],
                "response_mode": emotion_result["response_mode"],
                "source": emotion_result["source"],
                "raw_model_labels": emotion_result["raw_model_labels"],
                "provider_name": emotion_result["provider_name"],
                "source_metadata": emotion_result["source_metadata"],
            },
            "response_plan": support_package["response_plan"],
            "quote": quote.model_dump() if quote is not None else None,
        },
        ensure_ascii=False,
    )


def process_entry(
    db: Session,
    entry: JournalEntry,
    trigger_type: str,
    override_transcript: str | None = None,
) -> JournalEntry:
    attempt = _create_attempt(db=db, entry=entry, trigger_type=trigger_type, override_transcript=override_transcript)
    entry.processing_status = "processing"
    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)

    try:
        if override_transcript:
            transcript_text = override_transcript
            transcript_confidence = 1.0
        else:
            transcript_text, transcript_confidence = transcribe_audio(entry.audio_path)

        _apply_processing_results(
            db=db,
            entry=entry,
            transcript_text=transcript_text,
            transcript_confidence=transcript_confidence,
        )
        entry.processing_status = "processed"
        entry.updated_at = datetime.now(timezone.utc)
        recompute_tree_for_user(db, entry.user_id)
        _mark_attempt_finished(attempt, "succeeded")
        db.commit()
        db.refresh(entry)
        return entry
    except (ProviderConfigurationError, ProviderExecutionError) as exc:
        entry.processing_status = "failed"
        entry.updated_at = datetime.now(timezone.utc)
        _mark_attempt_finished(attempt, "failed", str(exc))
        db.commit()
        raise
    except Exception as exc:
        entry.processing_status = "failed"
        entry.updated_at = datetime.now(timezone.utc)
        _mark_attempt_finished(attempt, "failed", str(exc))
        db.commit()
        raise


def process_entry_in_background(
    entry_id: str,
    trigger_type: str,
    override_transcript: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        entry = get_entry_or_404(db, entry_id)
        process_entry(db=db, entry=entry, trigger_type=trigger_type, override_transcript=override_transcript)
    except Exception:
        db.rollback()
    finally:
        db.close()


def remove_entry_audio(audio_path: str) -> bool:
    path = Path(audio_path)
    if path.exists():
        path.unlink()
        return True
    return False
