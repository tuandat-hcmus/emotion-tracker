from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import enforce_entry_owner_access, get_current_user_optional
from app.models.journal_entry import JournalEntry
from app.models.processing_attempt import ProcessingAttempt
from app.models.user import User
from app.schemas.checkin import (
    CheckinDetailResponse,
    CreateTextCheckinRequest,
    DeleteCheckinResponse,
    ProcessAcceptedResponse,
    ProcessCheckinRequest,
    ProcessingAttemptItemResponse,
    ProcessingAttemptListResponse,
    UploadCheckinResponse,
)
from app.services.checkin_entry_service import get_entry_or_404, serialize_entry
from app.services.checkin_processing_service import (
    PROCESSABLE_STATUSES,
    REPROCESSABLE_STATUSES,
    create_and_process_text_entry,
    process_entry,
    process_entry_in_background,
    remove_entry_audio,
)
from app.services.storage_service import save_upload_file, validate_upload_file
from app.services.tree_service import recompute_tree_for_user

router = APIRouter(prefix="/v1/checkins", tags=["checkins"])


def _raise_processing_http_error(exc: Exception) -> None:
    from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError

    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, ProviderConfigurationError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    if isinstance(exc, ProviderExecutionError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    raise exc


@router.post("/upload", response_model=UploadCheckinResponse, status_code=status.HTTP_201_CREATED)
def upload_checkin(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    session_type: str = Form("free"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> UploadCheckinResponse:
    from app.core.config import get_settings

    settings = get_settings()
    created_at = datetime.now(timezone.utc)
    entry_user_id = current_user.id if current_user is not None else user_id

    if current_user is None and not settings.auth_optional_for_dev:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")

    try:
        validate_upload_file(file)
        audio_path = save_upload_file(file, settings.uploads_dir)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save uploaded file") from exc
    finally:
        file.file.close()

    entry = JournalEntry(
        user_id=entry_user_id,
        session_type=session_type,
        audio_path=audio_path,
        processing_status="uploaded",
        created_at=created_at,
        updated_at=created_at,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return UploadCheckinResponse(entry_id=entry.id, status=entry.processing_status, source_type="voice")


@router.post("/text", response_model=CheckinDetailResponse, status_code=status.HTTP_201_CREATED)
def create_text_checkin(
    payload: CreateTextCheckinRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CheckinDetailResponse:
    from app.core.config import get_settings

    settings = get_settings()
    entry_user_id = current_user.id if current_user is not None else payload.user_id

    if current_user is None and not settings.auth_optional_for_dev:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")
    if not entry_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required for text check-ins")

    try:
        entry = create_and_process_text_entry(
            db=db,
            user_id=entry_user_id,
            session_type=payload.session_type,
            raw_text=payload.text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        _raise_processing_http_error(exc)

    return CheckinDetailResponse.model_validate(serialize_entry(entry))


@router.post("/{entry_id}/process", response_model=CheckinDetailResponse)
def process_checkin(
    entry_id: str,
    payload: ProcessCheckinRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CheckinDetailResponse:
    entry = get_entry_or_404(db, entry_id)
    enforce_entry_owner_access(entry, current_user)
    if entry.processing_status == "processing":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Journal entry is already processing")
    if entry.processing_status == "processed":
        normalized_override = payload.override_transcript.strip() if payload.override_transcript else None
        if not normalized_override or normalized_override == (entry.transcript_text or ""):
            return CheckinDetailResponse.model_validate(serialize_entry(entry))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Journal entry is already processed; use reprocess to change the transcript or snapshots",
        )
    if entry.processing_status not in PROCESSABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Journal entry cannot be processed from status '{entry.processing_status}'",
        )
    try:
        processed_entry = process_entry(
            db=db,
            entry=entry,
            trigger_type="manual",
            override_transcript=payload.override_transcript,
        )
    except Exception as exc:
        _raise_processing_http_error(exc)
    return CheckinDetailResponse.model_validate(serialize_entry(processed_entry))


@router.post("/{entry_id}/process-async", response_model=ProcessAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def process_checkin_async(
    entry_id: str,
    payload: ProcessCheckinRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProcessAcceptedResponse:
    entry = get_entry_or_404(db, entry_id)
    enforce_entry_owner_access(entry, current_user)
    if entry.processing_status == "processing":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Journal entry is already processing")
    if entry.processing_status == "processed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Journal entry is already processed; use reprocess instead",
        )
    if entry.processing_status not in PROCESSABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Journal entry cannot be processed from status '{entry.processing_status}'",
        )

    entry.processing_status = "processing"
    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    background_tasks.add_task(
        process_entry_in_background,
        entry_id=entry.id,
        trigger_type="async",
        override_transcript=payload.override_transcript,
    )
    return ProcessAcceptedResponse(
        entry_id=entry.id,
        status="processing",
        message="Journal entry accepted for background processing",
    )


@router.post("/{entry_id}/reprocess", response_model=CheckinDetailResponse)
def reprocess_checkin(
    entry_id: str,
    payload: ProcessCheckinRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CheckinDetailResponse:
    entry = get_entry_or_404(db, entry_id)
    enforce_entry_owner_access(entry, current_user)
    if entry.processing_status == "processing":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Journal entry is already processing")
    if entry.processing_status not in REPROCESSABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only processed or failed entries can be reprocessed",
        )

    try:
        processed_entry = process_entry(
            db=db,
            entry=entry,
            trigger_type="reprocess",
            override_transcript=payload.override_transcript,
        )
    except Exception as exc:
        _raise_processing_http_error(exc)
    return CheckinDetailResponse.model_validate(serialize_entry(processed_entry))


@router.delete("/{entry_id}", response_model=DeleteCheckinResponse)
def delete_checkin(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> DeleteCheckinResponse:
    entry = get_entry_or_404(db, entry_id)
    enforce_entry_owner_access(entry, current_user)
    if entry.processing_status == "processing":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete an entry while processing")

    user_id = entry.user_id
    removed_audio = remove_entry_audio(entry.audio_path)
    db.query(ProcessingAttempt).filter(ProcessingAttempt.entry_id == entry.id).delete(synchronize_session=False)
    db.delete(entry)
    db.flush()
    recompute_tree_for_user(db, user_id)
    db.commit()

    return DeleteCheckinResponse(entry_id=entry_id, deleted=True, removed_audio=removed_audio)


@router.get("/{entry_id}/attempts", response_model=ProcessingAttemptListResponse)
def get_processing_attempts(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProcessingAttemptListResponse:
    entry = get_entry_or_404(db, entry_id)
    enforce_entry_owner_access(entry, current_user)
    attempts = (
        db.query(ProcessingAttempt)
        .filter(ProcessingAttempt.entry_id == entry.id)
        .order_by(ProcessingAttempt.started_at.desc(), ProcessingAttempt.id.desc())
        .all()
    )
    return ProcessingAttemptListResponse(
        entry_id=entry.id,
        total=len(attempts),
        items=[
            ProcessingAttemptItemResponse(
                id=attempt.id,
                trigger_type=attempt.trigger_type,
                provider_stt=attempt.provider_stt,
                provider_response=attempt.provider_response,
                status=attempt.status,
                used_override_transcript=attempt.used_override_transcript,
                error_message=attempt.error_message,
                started_at=attempt.started_at,
                finished_at=attempt.finished_at,
            )
            for attempt in attempts
        ],
    )


@router.get("/{entry_id}", response_model=CheckinDetailResponse)
def get_checkin(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CheckinDetailResponse:
    entry = get_entry_or_404(db, entry_id)
    enforce_entry_owner_access(entry, current_user)
    return CheckinDetailResponse.model_validate(serialize_entry(entry))
