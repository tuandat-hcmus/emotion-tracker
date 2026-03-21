import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.journal_entry import JournalEntry
from app.models.processing_attempt import ProcessingAttempt
from app.services.checkin_entry_service import get_entry_or_404, serialize_entry
from app.services.ai_support_service import build_support_package
from app.services.checkin_text_service import load_recent_memory_records, normalize_checkin_text
from app.services.preferences_service import get_or_create_preferences
from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError
from app.services.response_service import get_response_provider_name
from app.services.stt_service import get_stt_provider_name, transcribe_audio
from app.services.tree_service import recompute_tree_for_user

logger = logging.getLogger(__name__)

PROCESSABLE_STATUSES = {"uploaded", "failed"}
REPROCESSABLE_STATUSES = {"processed", "failed"}


def _create_attempt(
    db: Session,
    entry: JournalEntry,
    trigger_type: str,
    override_transcript: str | None,
    provider_stt: str | None = None,
) -> ProcessingAttempt:
    attempt = ProcessingAttempt(
        entry_id=entry.id,
        user_id=entry.user_id,
        trigger_type=trigger_type,
        provider_stt=provider_stt or get_stt_provider_name(override_transcript),
        provider_response=get_response_provider_name(),
        status="started",
        used_override_transcript=bool(override_transcript),
        started_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.flush()
    return attempt


def _set_entry_status(entry: JournalEntry, status_value: str) -> None:
    entry.processing_status = status_value
    entry.updated_at = datetime.now(timezone.utc)


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
    raw_text: str | None,
    transcript_text: str,
    transcript_confidence: float,
    source_type: str,
    transcript_source: str,
    transcript_provider: str,
) -> None:
    logger.info(
        "checkin_processing.support_pipeline_start entry_id=%s user_id=%s source_type=%s transcript_source=%s response_provider=%s",
        entry.id,
        entry.user_id,
        source_type,
        transcript_source,
        get_response_provider_name(),
    )
    preferences = get_or_create_preferences(db, entry.user_id)
    recent_memory = load_recent_memory_records(db, user_id=entry.user_id, exclude_entry_id=entry.id, limit=2)
    support_package = build_support_package(
        transcript=transcript_text,
        user_id=entry.user_id,
        audio_path=entry.audio_path,
        quote_opt_in=preferences.quote_opt_in,
        memory_records=recent_memory,
    )
    emotion_result = support_package["emotion_analysis"]
    topic_tags = support_package["topic_tags"]
    risk_level = str(support_package["risk_level"])
    risk_flags = list(support_package["risk_flags"])

    entry.raw_text = raw_text
    entry.transcript_text = transcript_text
    entry.transcript_confidence = transcript_confidence
    entry.ai_response = str(support_package["ai_response"])
    entry.emotion_label = str(emotion_result["primary_label"])
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
                "primary_label": emotion_result["primary_label"],
                "secondary_labels": emotion_result["secondary_labels"],
                "all_labels": emotion_result["all_labels"],
                "scores": emotion_result["scores"],
                "threshold": emotion_result["threshold"],
                "social_need_score": emotion_result["social_need_score"],
                "confidence": emotion_result["confidence"],
                "dominant_signals": emotion_result["dominant_signals"],
                "context_tags": emotion_result["context_tags"],
                "enrichment_notes": emotion_result["enrichment_notes"],
                "response_mode": emotion_result["response_mode"],
                "source": emotion_result["source"],
                "provider_name": emotion_result["provider_name"],
                "source_metadata": emotion_result["source_metadata"],
            },
            "render_context": support_package["render_context"],
            "normalized_state": support_package["normalized_state"],
            "memory_summary": support_package["memory_summary"],
            "insight_features": support_package["insight_features"],
            "support_strategy": support_package["support_strategy"],
            "response_plan": support_package["response_plan"],
            "follow_up_question": support_package["follow_up_question"],
            "quote": quote.model_dump() if quote is not None else None,
            "raw_text": raw_text,
            "normalized_text": transcript_text,
            "source_type": source_type,
            "transcript_source": transcript_source,
            "transcript_provider": transcript_provider,
            "topic_tags": topic_tags,
            "response_provider": get_response_provider_name(),
        },
        ensure_ascii=False,
    )
    logger.info(
        "checkin_processing.support_pipeline_complete entry_id=%s primary_label=%s risk_level=%s response_mode=%s recent_memory=%s",
        entry.id,
        emotion_result["primary_label"],
        risk_level,
        emotion_result["response_mode"],
        len(recent_memory),
    )


def _process_transcript_for_entry(
    *,
    db: Session,
    entry: JournalEntry,
    raw_text: str | None,
    transcript_text: str,
    transcript_confidence: float,
    source_type: str,
    transcript_source: str,
    transcript_provider: str,
) -> None:
    normalized_transcript = normalize_checkin_text(transcript_text)
    logger.info(
        "checkin_processing.transcript_normalized entry_id=%s source_type=%s transcript_source=%s transcript_provider=%s raw_chars=%s normalized_chars=%s",
        entry.id,
        source_type,
        transcript_source,
        transcript_provider,
        len(transcript_text),
        len(normalized_transcript),
    )
    _apply_processing_results(
        db=db,
        entry=entry,
        raw_text=raw_text,
        transcript_text=normalized_transcript,
        transcript_confidence=transcript_confidence,
        source_type=source_type,
        transcript_source=transcript_source,
        transcript_provider=transcript_provider,
    )


def _mark_processing_failed(
    *,
    db: Session,
    entry_id: str,
    attempt_id: str,
    error_message: str,
) -> None:
    db.rollback()
    failed_entry = get_entry_or_404(db, entry_id)
    failed_attempt = db.get(ProcessingAttempt, attempt_id)
    _set_entry_status(failed_entry, "failed")
    if failed_attempt is not None:
        _mark_attempt_finished(failed_attempt, "failed", error_message)
    db.commit()
    logger.exception(
        "checkin_processing.failed entry_id=%s attempt_id=%s error=%s",
        entry_id,
        attempt_id,
        error_message,
    )


def process_entry(
    db: Session,
    entry: JournalEntry,
    trigger_type: str,
    override_transcript: str | None = None,
) -> JournalEntry:
    allowed_statuses = REPROCESSABLE_STATUSES if trigger_type == "reprocess" else PROCESSABLE_STATUSES | {"processing"}
    if entry.processing_status not in allowed_statuses:
        logger.info(
            "checkin_processing.skip_nonprocessable entry_id=%s trigger=%s status=%s",
            entry.id,
            trigger_type,
            entry.processing_status,
        )
        return entry

    attempt = _create_attempt(db=db, entry=entry, trigger_type=trigger_type, override_transcript=override_transcript)
    _set_entry_status(entry, "processing")
    logger.info(
        "checkin_processing.start entry_id=%s attempt_id=%s trigger=%s source_type=%s override=%s",
        entry.id,
        attempt.id,
        trigger_type,
        "voice" if entry.audio_path else "text",
        bool(override_transcript),
    )
    db.commit()
    db.refresh(entry)

    try:
        if override_transcript:
            raw_text = override_transcript
            transcript_text = override_transcript
            transcript_confidence = 1.0
            source_type = "voice" if entry.audio_path else "text"
            transcript_source = "override"
            transcript_provider = "override"
        else:
            raw_text = None
            logger.info(
                "checkin_processing.stt_start entry_id=%s attempt_id=%s provider=%s",
                entry.id,
                attempt.id,
                get_stt_provider_name(),
            )
            transcript_text, transcript_confidence = transcribe_audio(entry.audio_path)
            source_type = "voice"
            transcript_source = "stt"
            transcript_provider = get_stt_provider_name()
            logger.info(
                "checkin_processing.stt_complete entry_id=%s attempt_id=%s provider=%s confidence=%s",
                entry.id,
                attempt.id,
                transcript_provider,
                transcript_confidence,
            )

        _process_transcript_for_entry(
            db=db,
            entry=entry,
            raw_text=raw_text,
            transcript_text=transcript_text,
            transcript_confidence=transcript_confidence,
            source_type=source_type,
            transcript_source=transcript_source,
            transcript_provider=transcript_provider,
        )
        _set_entry_status(entry, "processed")
        recompute_tree_for_user(db, entry.user_id)
        _mark_attempt_finished(attempt, "succeeded")
        db.commit()
        db.refresh(entry)
        logger.info(
            "checkin_processing.succeeded entry_id=%s attempt_id=%s source_type=%s transcript_source=%s",
            entry.id,
            attempt.id,
            source_type,
            transcript_source,
        )
        return entry
    except (ProviderConfigurationError, ProviderExecutionError) as exc:
        _mark_processing_failed(db=db, entry_id=entry.id, attempt_id=attempt.id, error_message=str(exc))
        raise
    except Exception as exc:
        _mark_processing_failed(db=db, entry_id=entry.id, attempt_id=attempt.id, error_message=str(exc))
        raise


def process_entry_in_background(
    entry_id: str,
    trigger_type: str,
    override_transcript: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        entry = get_entry_or_404(db, entry_id)
        logger.info(
            "checkin_processing.background_start entry_id=%s trigger=%s override=%s",
            entry_id,
            trigger_type,
            bool(override_transcript),
        )
        process_entry(db=db, entry=entry, trigger_type=trigger_type, override_transcript=override_transcript)
    except Exception:
        db.rollback()
        logger.exception("checkin_processing.background_failed entry_id=%s trigger=%s", entry_id, trigger_type)
    finally:
        db.close()


def remove_entry_audio(audio_path: str) -> bool:
    if not audio_path:
        return False
    path = Path(audio_path)
    if path.exists():
        path.unlink()
        return True
    return False


def create_and_process_text_entry(
    *,
    db: Session,
    user_id: str,
    session_type: str,
    raw_text: str,
) -> JournalEntry:
    normalized_text = normalize_checkin_text(raw_text)
    created_at = datetime.now(timezone.utc)
    logger.info(
        "checkin_processing.text_ingest user_id=%s session_type=%s raw_chars=%s normalized_chars=%s",
        user_id,
        session_type,
        len(raw_text),
        len(normalized_text),
    )
    entry = JournalEntry(
        user_id=user_id,
        session_type=session_type,
        audio_path=None,
        processing_status="uploaded",
        raw_text=raw_text,
        created_at=created_at,
        updated_at=created_at,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    attempt = _create_attempt(
        db=db,
        entry=entry,
        trigger_type="text",
        override_transcript=None,
        provider_stt="text_input",
    )
    _set_entry_status(entry, "processing")
    db.commit()
    db.refresh(entry)

    try:
        _process_transcript_for_entry(
            db=db,
            entry=entry,
            raw_text=raw_text,
            transcript_text=normalized_text,
            transcript_confidence=1.0,
            source_type="text",
            transcript_source="user_text",
            transcript_provider="text_input",
        )
        _set_entry_status(entry, "processed")
        recompute_tree_for_user(db, entry.user_id)
        _mark_attempt_finished(attempt, "succeeded")
        db.commit()
        db.refresh(entry)
        logger.info("checkin_processing.text_succeeded entry_id=%s attempt_id=%s", entry.id, attempt.id)
        return entry
    except (ProviderConfigurationError, ProviderExecutionError) as exc:
        _mark_processing_failed(db=db, entry_id=entry.id, attempt_id=attempt.id, error_message=str(exc))
        raise
    except Exception as exc:
        _mark_processing_failed(db=db, entry_id=entry.id, attempt_id=attempt.id, error_message=str(exc))
        raise
