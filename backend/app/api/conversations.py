import base64
import json

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal, get_db
from app.dependencies.auth import get_current_user_required
from app.models.user import User
from app.schemas.conversation import (
    ConversationSessionListResponse,
    ConversationSessionResponse,
    ConversationTurnListResponse,
    ConversationTurnResponse,
    ConversationTurnResultResponse,
)
from app.services.auth_service import get_user_by_id
from app.services.conversation_service import (
    end_session,
    ensure_session_owner,
    get_session_or_404,
    list_session_turns,
    list_user_sessions,
    process_conversation_turn,
    start_session,
)
from app.services.stt_service import build_partial_transcript, transcribe_stream_audio

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


@router.post("/sessions", response_model=ConversationSessionResponse, status_code=status.HTTP_201_CREATED)
def create_conversation_session(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> ConversationSessionResponse:
    return ConversationSessionResponse.model_validate(start_session(db, current_user.id))


@router.get("/sessions", response_model=ConversationSessionListResponse)
def list_conversation_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> ConversationSessionListResponse:
    total, items = list_user_sessions(db, user_id=current_user.id, limit=limit, offset=offset)
    return ConversationSessionListResponse(
        user_id=current_user.id,
        total=total,
        limit=limit,
        offset=offset,
        items=[ConversationSessionResponse.model_validate(item) for item in items],
    )


@router.get("/sessions/{session_id}", response_model=ConversationSessionResponse)
def get_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> ConversationSessionResponse:
    session = ensure_session_owner(get_session_or_404(db, session_id), current_user.id)
    return ConversationSessionResponse.model_validate(session)


@router.get("/sessions/{session_id}/turns", response_model=ConversationTurnListResponse)
def get_conversation_session_turns(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> ConversationTurnListResponse:
    session = ensure_session_owner(get_session_or_404(db, session_id), current_user.id)
    total, items = list_session_turns(db, session_id=session.id, limit=limit, offset=offset)
    return ConversationTurnListResponse(
        session_id=session.id,
        total=total,
        limit=limit,
        offset=offset,
        items=[ConversationTurnResponse.model_validate(item) for item in items],
    )


@router.post("/sessions/{session_id}/end", response_model=ConversationSessionResponse)
def close_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> ConversationSessionResponse:
    session = ensure_session_owner(get_session_or_404(db, session_id), current_user.id)
    return ConversationSessionResponse.model_validate(end_session(db, session_id))


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


@router.websocket("/ws/{session_id}")
async def conversation_websocket(websocket: WebSocket, session_id: str) -> None:
    db = SessionLocal()
    accepted = False
    try:
        current_user = _get_websocket_user(websocket, db)
        session = get_session_or_404(db, session_id)
        if session.user_id != current_user.id:
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
            if message.get("bytes") is not None:
                audio_chunks.append(message["bytes"])
                partial = build_partial_transcript(audio_chunks)
                if partial:
                    await websocket.send_json({"type": "partial_transcript", "text": partial})
                continue
            raw_text = message.get("text")
            if raw_text is None:
                continue
            payload = json.loads(raw_text)
            event_type = str(payload.get("type", "")).strip().lower()
            if event_type == "audio_chunk":
                chunk_b64 = payload.get("chunk")
                if isinstance(chunk_b64, str):
                    audio_chunks.append(base64.b64decode(chunk_b64))
                    audio_extension = str(payload.get("extension", audio_extension))
                    partial = build_partial_transcript(audio_chunks)
                    if partial:
                        await websocket.send_json({"type": "partial_transcript", "text": partial})
            elif event_type == "audio_final":
                transcript, confidence, audio_path = transcribe_stream_audio(
                    audio_chunks,
                    uploads_dir=get_settings().uploads_dir,
                    extension=str(payload.get("extension", audio_extension)),
                    text_fallback=payload.get("text_fallback"),
                )
                await websocket.send_json(
                    {
                        "type": "final_transcript",
                        "text": transcript,
                        "confidence": confidence,
                        "audio_path": audio_path,
                    }
                )
                result = process_conversation_turn(db, session_id, transcript, audio_path=audio_path)
                await websocket.send_json(
                    {
                        "type": "assistant_response",
                        "payload": ConversationTurnResultResponse.model_validate(result).model_dump(mode="json"),
                    }
                )
                audio_chunks = []
                audio_extension = ".webm"
            elif event_type == "user_text":
                result = process_conversation_turn(db, session_id, str(payload.get("text", "")))
                await websocket.send_json(
                    {
                        "type": "assistant_response",
                        "payload": ConversationTurnResultResponse.model_validate(result).model_dump(mode="json"),
                    }
                )
    except WebSocketDisconnect:
        return
    except Exception:
        if accepted:
            await websocket.send_json({"type": "error", "message": "Conversation processing failed"})
            await websocket.close(code=1011)
        else:
            await websocket.close(code=4401)
    finally:
        db.close()
