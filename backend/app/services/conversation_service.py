from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.conversation_session import ConversationSession
from app.models.conversation_turn import ConversationTurn
from app.services.ai_contract_service import build_ai_contract
from app.services.ai_support_service import build_support_package
from app.services.companion_core import build_emotional_memory_record
from app.services.companion_core.feature_extraction import extract_insight_features
from app.services.companion_core.schemas import EmotionalMemoryRecord, NormalizedEmotionalState, SupportStrategy
from app.services.companion_core.strategy_engine import select_support_strategy
from app.services.emotion_service import analyze_emotion
from app.services.safety_service import detect_safety_risk

logger = logging.getLogger(__name__)


def _serialize_snapshot(snapshot: dict[str, object] | None) -> str | None:
    if snapshot is None:
        return None
    return json.dumps(snapshot, ensure_ascii=False)


def _deserialize_snapshot(snapshot_text: str | None) -> dict[str, object]:
    if not snapshot_text:
        return {}
    try:
        payload = json.loads(snapshot_text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _serialize_turn(turn: ConversationTurn) -> dict[str, object]:
    return {
        "id": turn.id,
        "session_id": turn.session_id,
        "role": turn.role,
        "text": turn.text,
        "audio_path": turn.audio_path,
        "emotion_snapshot": _deserialize_snapshot(turn.emotion_snapshot),
        "state_snapshot": _deserialize_snapshot(turn.state_snapshot),
        "created_at": turn.created_at,
    }


def get_session_or_404(db: Session, session_id: str) -> ConversationSession:
    session = db.get(ConversationSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation session not found")
    return session


def ensure_session_owner(session: ConversationSession, user_id: str) -> ConversationSession:
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return session


def list_user_sessions(
    db: Session,
    *,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[int, list[ConversationSession]]:
    query = db.query(ConversationSession).filter(ConversationSession.user_id == user_id)
    total = query.count()
    items = (
        query.order_by(ConversationSession.started_at.desc(), ConversationSession.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return total, items


def list_session_turns(
    db: Session,
    *,
    session_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[ConversationTurn]]:
    query = db.query(ConversationTurn).filter(ConversationTurn.session_id == session_id)
    total = query.count()
    items = (
        query.order_by(ConversationTurn.created_at.asc(), ConversationTurn.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return total, items


def start_session(db: Session, user_id: str) -> ConversationSession:
    session = ConversationSession(
        user_id=user_id,
        status="active",
        started_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info("conversation.start_session session_id=%s user_id=%s", session.id, user_id)
    return session


def end_session(db: Session, session_id: str) -> ConversationSession:
    session = get_session_or_404(db, session_id)
    if session.status != "ended":
        session.status = "ended"
        session.ended_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
    logger.info("conversation.end_session session_id=%s user_id=%s", session.id, session.user_id)
    return session


def _add_turn(
    db: Session,
    *,
    session_id: str,
    role: str,
    text: str,
    audio_path: str | None = None,
    emotion_snapshot: dict[str, object] | None = None,
    state_snapshot: dict[str, object] | None = None,
) -> ConversationTurn:
    turn = ConversationTurn(
        session_id=session_id,
        role=role,
        text=text,
        audio_path=audio_path,
        emotion_snapshot=_serialize_snapshot(emotion_snapshot),
        state_snapshot=_serialize_snapshot(state_snapshot),
        created_at=datetime.now(timezone.utc),
    )
    db.add(turn)
    db.flush()
    return turn


def add_user_turn(
    db: Session,
    session_id: str,
    text: str,
    audio_path: str | None = None,
    emotion_snapshot: dict[str, object] | None = None,
    state_snapshot: dict[str, object] | None = None,
) -> ConversationTurn:
    turn = _add_turn(
        db,
        session_id=session_id,
        role="user",
        text=text,
        audio_path=audio_path,
        emotion_snapshot=emotion_snapshot,
        state_snapshot=state_snapshot,
    )
    db.commit()
    db.refresh(turn)
    return turn


def add_assistant_turn(
    db: Session,
    session_id: str,
    text: str,
    audio_path: str | None = None,
    emotion_snapshot: dict[str, object] | None = None,
    state_snapshot: dict[str, object] | None = None,
) -> ConversationTurn:
    turn = _add_turn(
        db,
        session_id=session_id,
        role="assistant",
        text=text,
        audio_path=audio_path,
        emotion_snapshot=emotion_snapshot,
        state_snapshot=state_snapshot,
    )
    db.commit()
    db.refresh(turn)
    return turn


def get_recent_user_turns(db: Session, session_id: str, n: int = 3) -> list[ConversationTurn]:
    turns = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.session_id == session_id, ConversationTurn.role == "user")
        .order_by(ConversationTurn.created_at.desc(), ConversationTurn.id.desc())
        .limit(n)
        .all()
    )
    return list(reversed(turns))


def _turn_to_memory_record(turn: ConversationTurn, session_user_id: str) -> EmotionalMemoryRecord | None:
    emotion_snapshot = _deserialize_snapshot(turn.emotion_snapshot)
    state_snapshot = _deserialize_snapshot(turn.state_snapshot)
    if not state_snapshot:
        return None
    normalized_state_data = state_snapshot.get("normalized_state", state_snapshot)
    if not isinstance(normalized_state_data, dict) or not normalized_state_data:
        return None
    normalized_state = NormalizedEmotionalState.model_validate(normalized_state_data)
    support_strategy_data = state_snapshot.get("support_strategy")
    if isinstance(support_strategy_data, dict) and support_strategy_data:
        support_strategy = SupportStrategy.model_validate(support_strategy_data)
    else:
        support_strategy = select_support_strategy(normalized_state)
    insight_features = extract_insight_features(normalized_state)
    topic_tags = list(normalized_state.topic_tags or emotion_snapshot.get("context_tags", []))
    return build_emotional_memory_record(
        user_id=session_user_id,
        transcript=turn.text,
        topic_tags=[str(item) for item in topic_tags],
        risk_level=str(normalized_state.risk_level),
        normalized_state=normalized_state,
        support_strategy=support_strategy,
        insight_features=insight_features,
        response_provider="conversation_session",
        response_mode=str(normalized_state.response_mode),
        suggestion_given=False,
        support_metadata={
            "session_id": turn.session_id,
            "turn_id": turn.id,
            "memory_summary": state_snapshot.get("memory_summary", {}),
        },
    )


def process_conversation_turn(
    db: Session,
    session_id: str,
    text: str,
    *,
    audio_path: str | None = None,
) -> dict[str, object]:
    session = get_session_or_404(db, session_id)
    if session.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conversation session is not active")

    cleaned_text = " ".join(text.split()).strip()
    if not cleaned_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation text cannot be empty")

    recent_turns = get_recent_user_turns(db, session_id, n=3)
    context_lines = [turn.text for turn in recent_turns[-2:] if turn.text]
    context_lines.append(cleaned_text)
    context_text = "\n".join(context_lines)
    memory_records = [
        record
        for record in (_turn_to_memory_record(turn, session.user_id) for turn in recent_turns)
        if record is not None
    ]
    risk_level = str(detect_safety_risk(cleaned_text)["risk_level"])
    context_emotion = analyze_emotion(context_text, risk_level=risk_level, audio_path=audio_path)
    logger.info(
        "conversation.process_turn session_id=%s user_id=%s recent_turns=%s context_chars=%s",
        session.id,
        session.user_id,
        len(recent_turns),
        len(context_text),
    )
    support_package = build_support_package(
        transcript=cleaned_text,
        user_id=session.user_id,
        audio_path=audio_path,
        quote_opt_in=False,
        memory_records=memory_records,
        emotion_analysis_override=context_emotion,
        session_mode="realtime",
    )
    state_snapshot = {
        "normalized_state": support_package["normalized_state"],
        "support_strategy": support_package["support_strategy"],
        "memory_summary": support_package["memory_summary"],
        "response_plan": support_package["response_plan"],
    }
    user_turn = _add_turn(
        db,
        session_id=session.id,
        role="user",
        text=cleaned_text,
        audio_path=audio_path,
        emotion_snapshot=support_package["emotion_analysis"],
        state_snapshot=state_snapshot,
    )
    assistant_turn = _add_turn(
        db,
        session_id=session.id,
        role="assistant",
        text=str(support_package["ai_response"]),
        audio_path=None,
        emotion_snapshot=support_package["emotion_analysis"],
        state_snapshot=state_snapshot,
    )
    db.commit()
    db.refresh(user_turn)
    db.refresh(assistant_turn)
    ai_contract = build_ai_contract(
        emotion_analysis=support_package["emotion_analysis"],
        risk_level=str(support_package["risk_level"]),
        risk_flags=list(support_package["risk_flags"]),
        topic_tags=list(support_package["topic_tags"]),
        response_plan=support_package["response_plan"],
        empathetic_response=str(support_package["empathetic_response"]),
        follow_up_question=support_package["follow_up_question"],
        gentle_suggestion=support_package["gentle_suggestion"],
        quote=support_package["quote"].model_dump() if support_package["quote"] is not None else None,
        ai_response=str(support_package["ai_response"]),
        normalized_state=support_package["normalized_state"],
        support_strategy=support_package["support_strategy"],
        memory_summary=support_package["memory_summary"],
        insight_features=support_package["insight_features"],
    ).model_dump()
    return {
        "session_id": session.id,
        "user_turn": _serialize_turn(user_turn),
        "assistant_turn": _serialize_turn(assistant_turn),
        "final_transcript": cleaned_text,
        "assistant_response": str(support_package["ai_response"]),
        "emotion_analysis": support_package["emotion_analysis"],
        "response_plan": support_package["response_plan"],
        "ai": ai_contract,
    }
