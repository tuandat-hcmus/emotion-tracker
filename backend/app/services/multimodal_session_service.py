import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

logger = logging.getLogger(__name__)

_SESSION_TTL_SECONDS = 30 * 60  # 30 minutes


@dataclass
class MultimodalSessionState:
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    face_results: list[dict] = field(default_factory=list)
    latest_audio_result: dict | None = None


_sessions: dict[str, MultimodalSessionState] = {}


def _cleanup_expired() -> None:
    now = datetime.now(tz=timezone.utc)
    expired = [
        sid
        for sid, state in _sessions.items()
        if (now - state.created_at).total_seconds() > _SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del _sessions[sid]
        logger.info("multimodal_session.expired session_id=%s", sid)


def create_session(user_id: str) -> MultimodalSessionState:
    _cleanup_expired()
    session_id = str(uuid4())
    state = MultimodalSessionState(session_id=session_id, user_id=user_id)
    _sessions[session_id] = state
    logger.info("multimodal_session.created session_id=%s user_id=%s", session_id, user_id)
    return state


def get_session(session_id: str) -> MultimodalSessionState | None:
    return _sessions.get(session_id)


def close_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
    logger.info("multimodal_session.closed session_id=%s", session_id)


def append_face_result(session_id: str, result: dict) -> None:
    state = _sessions.get(session_id)
    if state is not None:
        state.face_results.append(result)


def set_audio_result(session_id: str, result: dict) -> None:
    state = _sessions.get(session_id)
    if state is not None:
        state.latest_audio_result = result
