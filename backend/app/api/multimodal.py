import asyncio
import base64
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal, get_db
from app.dependencies.auth import get_current_user_required
from app.models.multimodal_session import MultimodalSession
from app.models.user import User
from app.schemas.multimodal import (
    CreateMultimodalSessionResponse,
    EndMultimodalSessionRequest,
    MultimodalSessionDetailResponse,
)
from app.services.ai_core.audio_emotion_service import infer_audio_emotion
from app.services.ai_core.face_emotion_service import infer_face_emotion_from_bytes
from app.services.ai_core.multimodal_fusion_service import fuse_emotion_signals
from app.services.ai_core.schemas import AudioEmotionResult, TextEmotionResult
from app.services.auth_service import get_user_by_id
from app.services.multimodal_session_service import (
    append_face_result,
    close_session,
    create_session,
    get_session,
    set_audio_result,
)
from app.services.stt_service import persist_stream_audio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/multimodal", tags=["multimodal"])


def _get_websocket_user(websocket: WebSocket, db: Session) -> User:
    settings = get_settings()
    token = websocket.query_params.get("token")
    if not token:
        if settings.auth_optional_for_dev:
            user_id = websocket.query_params.get("user_id")
            if not user_id:
                raise ValueError("Missing token or user_id")
            user = get_user_by_id(db, user_id)
            if user is None:
                raise ValueError("User not available")
            return user
        raise ValueError("Missing token")
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise ValueError("Invalid token subject")
    user = get_user_by_id(db, subject)
    if user is None or not user.is_active:
        raise ValueError("User not available")
    return user


def _session_to_detail(db_session: MultimodalSession) -> MultimodalSessionDetailResponse:
    fused = None
    if db_session.fused_result_text:
        try:
            fused = json.loads(db_session.fused_result_text)
        except Exception:
            fused = None
    return MultimodalSessionDetailResponse(
        session_id=db_session.id,
        user_id=db_session.user_id,
        journal_entry_id=db_session.journal_entry_id,
        status=db_session.status,
        emotion_label=db_session.emotion_label,
        valence_score=db_session.valence_score,
        energy_score=db_session.energy_score,
        stress_score=db_session.stress_score,
        emotion_confidence=db_session.emotion_confidence,
        fusion_source=db_session.fusion_source,
        fused_result=fused,
        started_at=db_session.started_at.isoformat(),
        ended_at=db_session.ended_at.isoformat() if db_session.ended_at else None,
    )


def _aggregate_face_results(face_results: list[dict]) -> AudioEmotionResult | None:
    """Average emotion scores across all accumulated face frames."""
    if not face_results:
        return None
    combined: dict[str, float] = {}
    for fr in face_results:
        for label, score in fr.get("ranked_emotions", []):
            combined[label] = combined.get(label, 0.0) + float(score)
    n = len(face_results)
    averaged = sorted(
        [(label, round(score / n, 4)) for label, score in combined.items()],
        key=lambda x: x[1],
        reverse=True,
    )
    return AudioEmotionResult(
        provider_name=face_results[0].get("provider_name", "face"),
        raw_model_labels=[label for label, _ in averaged],
        ranked_emotions=averaged,
        confidence=averaged[0][1] if averaged else 0.0,
    )


@router.post(
    "/sessions",
    response_model=CreateMultimodalSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_multimodal_session(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> CreateMultimodalSessionResponse:
    mem_state = create_session(current_user.id)
    db_record = MultimodalSession(
        id=mem_state.session_id,
        user_id=current_user.id,
        status="active",
    )
    db.add(db_record)
    db.commit()
    return CreateMultimodalSessionResponse(
        session_id=mem_state.session_id,
        user_id=current_user.id,
        status="active",
        started_at=mem_state.created_at.isoformat(),
    )


@router.post("/sessions/{session_id}/end", response_model=MultimodalSessionDetailResponse)
def end_multimodal_session(
    session_id: str,
    request: EndMultimodalSessionRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> MultimodalSessionDetailResponse:
    db_record = (
        db.query(MultimodalSession)
        .filter(
            MultimodalSession.id == session_id,
            MultimodalSession.user_id == current_user.id,
        )
        .first()
    )
    if db_record is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Multimodal session not found")

    mem_state = get_session(session_id)

    if mem_state is not None:
        # Aggregate face results across all captured frames
        face_result = _aggregate_face_results(mem_state.face_results)

        # Reconstruct audio result from stored dict
        audio_result: AudioEmotionResult | None = None
        if mem_state.latest_audio_result:
            try:
                audio_result = AudioEmotionResult.model_validate(mem_state.latest_audio_result)
            except Exception:
                logger.exception("multimodal.end_audio_result_parse_error session_id=%s", session_id)

        # Attempt fusion when we have at least one non-text modality
        if face_result is not None or audio_result is not None:
            try:
                # Use the audio result (or face result) as a proxy for text to enable fusion
                proxy_source = audio_result or face_result
                text_proxy = TextEmotionResult(
                    language="en",
                    provider_name="multimodal_proxy",
                    raw_model_labels=[label for label, _ in (proxy_source.ranked_emotions or [])],
                    ranked_emotions=proxy_source.ranked_emotions or [],
                    confidence=proxy_source.confidence,
                    source_metadata={"mode": "proxy_for_fusion"},
                )
                fused = fuse_emotion_signals(text_proxy, audio_result, face_result)
                db_record.emotion_label = fused.primary_emotion
                db_record.valence_score = fused.valence
                db_record.energy_score = fused.energy
                db_record.stress_score = fused.stress
                db_record.emotion_confidence = fused.confidence
                db_record.fusion_source = fused.source
                db_record.fused_result_text = json.dumps(fused.model_dump())
            except Exception:
                logger.exception("multimodal.end_fusion_error session_id=%s", session_id)

        if mem_state.face_results:
            db_record.face_results_text = json.dumps(mem_state.face_results[:50])
        if mem_state.latest_audio_result:
            db_record.audio_result_text = json.dumps(mem_state.latest_audio_result)

    db_record.status = "ended"
    db_record.ended_at = datetime.now(tz=timezone.utc)
    if request.journal_entry_id:
        db_record.journal_entry_id = request.journal_entry_id

    db.commit()
    close_session(session_id)
    return _session_to_detail(db_record)


@router.get("/sessions/{session_id}", response_model=MultimodalSessionDetailResponse)
def get_multimodal_session(
    session_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> MultimodalSessionDetailResponse:
    db_record = (
        db.query(MultimodalSession)
        .filter(
            MultimodalSession.id == session_id,
            MultimodalSession.user_id == current_user.id,
        )
        .first()
    )
    if db_record is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Multimodal session not found")
    return _session_to_detail(db_record)


@router.websocket("/ws/{session_id}")
async def multimodal_websocket(websocket: WebSocket, session_id: str) -> None:
    db = SessionLocal()
    accepted = False
    try:
        current_user = _get_websocket_user(websocket, db)
        mem_state = get_session(session_id)
        if mem_state is None or mem_state.user_id != current_user.id:
            await websocket.close(code=4403)
            return

        await websocket.accept()
        accepted = True
        audio_chunks: list[bytes] = []
        audio_extension = ".webm"

        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break

            raw_text = message.get("text")
            if raw_text is None:
                continue

            payload = json.loads(raw_text)
            event_type = str(payload.get("type", "")).strip().lower()

            if event_type == "frame":
                image_b64 = payload.get("data", "")
                if not image_b64:
                    continue
                try:
                    image_bytes = base64.b64decode(image_b64)
                    face_result = await asyncio.to_thread(infer_face_emotion_from_bytes, image_bytes)
                    if face_result is not None:
                        result_dict = face_result.model_dump()
                        append_face_result(session_id, result_dict)
                        await websocket.send_json(
                            {
                                "type": "face_emotion",
                                "face_detected": True,
                                "label": face_result.ranked_emotions[0][0]
                                if face_result.ranked_emotions
                                else "neutral",
                                "confidence": face_result.confidence,
                                "scores": dict(face_result.ranked_emotions),
                            }
                        )
                    else:
                        await websocket.send_json({"type": "face_emotion", "face_detected": False})
                except Exception:
                    logger.exception("multimodal_ws.frame_error session_id=%s", session_id)
                    await websocket.send_json({"type": "face_emotion", "face_detected": False})

            elif event_type == "audio_chunk":
                chunk_b64 = payload.get("chunk")
                if isinstance(chunk_b64, str):
                    audio_chunks.append(base64.b64decode(chunk_b64))
                    audio_extension = str(payload.get("extension", audio_extension))

            elif event_type == "audio_final":
                if audio_chunks:
                    try:
                        ext = str(payload.get("extension", audio_extension))
                        audio_path = await asyncio.to_thread(
                            persist_stream_audio,
                            audio_chunks,
                            get_settings().uploads_dir,
                            ext,
                        )
                        audio_result = await asyncio.to_thread(infer_audio_emotion, audio_path)
                        set_audio_result(session_id, audio_result.model_dump())
                        await websocket.send_json(
                            {
                                "type": "voice_emotion",
                                "label": audio_result.ranked_emotions[0][0]
                                if audio_result.ranked_emotions
                                else "neutral",
                                "confidence": audio_result.confidence,
                                "scores": dict(audio_result.ranked_emotions),
                            }
                        )
                    except Exception:
                        logger.exception("multimodal_ws.audio_error session_id=%s", session_id)
                        await websocket.send_json(
                            {"type": "error", "message": "Audio emotion processing failed"}
                        )
                    audio_chunks = []
                    audio_extension = ".webm"

    except WebSocketDisconnect:
        return
    except Exception:
        if accepted:
            await websocket.send_json({"type": "error", "message": "Multimodal stream failed"})
            await websocket.close(code=1011)
        else:
            await websocket.close(code=4401)
    finally:
        db.close()
