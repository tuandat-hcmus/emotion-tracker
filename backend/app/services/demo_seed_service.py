import json
from datetime import datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.journal_entry import JournalEntry
from app.models.processing_attempt import ProcessingAttempt
from app.models.tree_state import TreeState
from app.models.tree_state_event import TreeStateEvent
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.wrapup_snapshot import WrapupSnapshot
from app.schemas.dev import SeedDemoDataResponse
from app.schemas.me import UpsertPreferenceRequest
from app.services.auth_service import get_user_by_email, register_user
from app.services.preferences_service import upsert_preferences
from app.services.tree_service import recompute_tree_for_user
from app.services.wrapup_service import generate_wrapup_snapshot

DEFAULT_DEMO_EMAIL = "demo@example.com"
DEFAULT_DEMO_PASSWORD = "demo123456"
DEFAULT_DEMO_DISPLAY_NAME = "Demo User"


def _entry_blueprints_for_days_ago(days_ago: int) -> list[dict[str, object]]:
    schedule: dict[int, list[dict[str, object]]] = {
        0: [
            {
                "session_type": "morning",
                "entry_time": time(8, 15),
                "transcript_text": "Sáng nay mình thấy khá ổn, muốn bắt đầu ngày nhẹ nhàng và tập trung.",
                "emotion_label": "calm",
                "valence_score": 0.48,
                "energy_score": 0.56,
                "stress_score": 0.24,
                "topic_tags": ["công việc/học tập", "bản thân"],
                "risk_level": "low",
                "risk_flags": [],
                "ai_response": "Hôm nay có vẻ đủ ổn định để đi từng bước nhỏ.",
            },
            {
                "session_type": "free",
                "entry_time": time(13, 5),
                "transcript_text": "Giữa ngày mình vẫn giữ được nhịp, hơi mệt nhưng chưa quá tải.",
                "emotion_label": "balanced",
                "valence_score": 0.22,
                "energy_score": 0.41,
                "stress_score": 0.38,
                "topic_tags": ["công việc/học tập"],
                "risk_level": "low",
                "risk_flags": [],
                "ai_response": "Bạn đang duy trì khá tốt nhịp độ trong ngày.",
            },
        ],
        1: [
            {
                "session_type": "evening",
                "entry_time": time(20, 10),
                "transcript_text": "Tối nay mình khá căng vì deadline nhưng vẫn thấy kiểm soát được.",
                "emotion_label": "stressed",
                "valence_score": -0.16,
                "energy_score": 0.52,
                "stress_score": 0.73,
                "topic_tags": ["công việc/học tập"],
                "risk_level": "medium",
                "risk_flags": ["stress_spike"],
                "ai_response": "Có vẻ hôm nay áp lực cao hơn bình thường, nghỉ ngắn cũng có ích.",
            }
        ],
        2: [],
        3: [
            {
                "session_type": "morning",
                "entry_time": time(7, 55),
                "transcript_text": "Mình ngủ tốt hơn và thấy có động lực bắt đầu ngày mới.",
                "emotion_label": "hopeful",
                "valence_score": 0.58,
                "energy_score": 0.62,
                "stress_score": 0.21,
                "topic_tags": ["giấc ngủ", "bản thân"],
                "risk_level": "low",
                "risk_flags": [],
                "ai_response": "Một khởi đầu có năng lượng như vậy là tín hiệu tốt.",
            },
            {
                "session_type": "evening",
                "entry_time": time(20, 35),
                "transcript_text": "Buổi tối mình vẫn hơi mệt nhưng nhìn chung ngày hôm nay khá ổn.",
                "emotion_label": "tired",
                "valence_score": 0.1,
                "energy_score": 0.22,
                "stress_score": 0.34,
                "topic_tags": ["bản thân"],
                "risk_level": "low",
                "risk_flags": [],
                "ai_response": "Ngày hôm nay có vẻ không hoàn hảo nhưng vẫn đi đúng hướng.",
            },
        ],
        4: [
            {
                "session_type": "free",
                "entry_time": time(14, 20),
                "transcript_text": "Mình hơi buồn và nhớ gia đình, nhưng nói ra được thì thấy nhẹ hơn.",
                "emotion_label": "sad",
                "valence_score": -0.34,
                "energy_score": 0.19,
                "stress_score": 0.42,
                "topic_tags": ["gia đình", "bản thân"],
                "risk_level": "low",
                "risk_flags": [],
                "ai_response": "Việc nhận ra nỗi buồn và gọi tên nó đã là một bước quan trọng.",
            }
        ],
        5: [
            {
                "session_type": "evening",
                "entry_time": time(21, 5),
                "transcript_text": "Mình thấy rất quá tải, đầu óc nặng nề và mọi thứ chồng chất.",
                "emotion_label": "overwhelmed",
                "valence_score": -0.62,
                "energy_score": 0.28,
                "stress_score": 0.88,
                "topic_tags": ["công việc/học tập", "sức khỏe"],
                "risk_level": "medium",
                "risk_flags": ["overwhelm"],
                "ai_response": "Đây có vẻ là một ngày nặng. Tạm hạ kỳ vọng xuống mức an toàn hơn cũng ổn.",
            }
        ],
        6: [
            {
                "session_type": "morning",
                "entry_time": time(8, 0),
                "transcript_text": "Sáng nay mình thấy rõ ràng hơn và muốn quay lại các thói quen tốt.",
                "emotion_label": "motivated",
                "valence_score": 0.46,
                "energy_score": 0.67,
                "stress_score": 0.27,
                "topic_tags": ["thói quen", "bản thân"],
                "risk_level": "low",
                "risk_flags": [],
                "ai_response": "Động lực quay lại với nhịp quen là tín hiệu tích cực.",
            }
        ],
        7: [],
        8: [
            {
                "session_type": "morning",
                "entry_time": time(7, 45),
                "transcript_text": "Mình thấy biết ơn vì hôm nay đầu óc khá sáng và cơ thể nhẹ hơn.",
                "emotion_label": "grateful",
                "valence_score": 0.72,
                "energy_score": 0.61,
                "stress_score": 0.12,
                "topic_tags": ["biết ơn", "sức khỏe"],
                "risk_level": "low",
                "risk_flags": [],
                "ai_response": "Cảm giác biết ơn và nhẹ hơn là điểm tựa tốt cho ngày mới.",
            },
            {
                "session_type": "evening",
                "entry_time": time(20, 0),
                "transcript_text": "Tối nay mình khá yên, không quá vui nhưng cũng không căng.",
                "emotion_label": "calm",
                "valence_score": 0.32,
                "energy_score": 0.3,
                "stress_score": 0.2,
                "topic_tags": ["bản thân"],
                "risk_level": "low",
                "risk_flags": [],
                "ai_response": "Một buổi tối yên như vậy vẫn là tiến triển thực sự.",
            },
        ],
        9: [
            {
                "session_type": "free",
                "entry_time": time(16, 10),
                "transcript_text": "Mình thấy rất nặng nề và có lúc chỉ muốn biến mất khỏi mọi thứ.",
                "emotion_label": "hopeless",
                "valence_score": -0.78,
                "energy_score": 0.13,
                "stress_score": 0.94,
                "topic_tags": ["bản thân", "công việc/học tập"],
                "risk_level": "high",
                "risk_flags": ["hopelessness", "withdrawal"],
                "ai_response": "Lúc như vậy, ưu tiên an toàn và một điểm tựa gần nhất là quan trọng nhất.",
            }
        ],
    }
    return schedule[days_ago % 10]


def _build_demo_entries(user_id: str, days: int) -> list[JournalEntry]:
    today = datetime.now(timezone.utc).date()
    entries: list[JournalEntry] = []

    for days_ago in range(days - 1, -1, -1):
        target_day = today - timedelta(days=days_ago)
        for blueprint in _entry_blueprints_for_days_ago(days_ago):
            entry_dt = datetime.combine(target_day, blueprint["entry_time"], tzinfo=timezone.utc)
            entries.append(
                JournalEntry(
                    user_id=user_id,
                    session_type=str(blueprint["session_type"]),
                    audio_path=f"uploads/demo/{user_id}/{target_day.isoformat()}-{blueprint['session_type']}.wav",
                    processing_status="processed",
                    transcript_text=str(blueprint["transcript_text"]),
                    transcript_confidence=1.0,
                    ai_response=str(blueprint["ai_response"]),
                    emotion_label=str(blueprint["emotion_label"]),
                    valence_score=float(blueprint["valence_score"]),
                    energy_score=float(blueprint["energy_score"]),
                    stress_score=float(blueprint["stress_score"]),
                    topic_tags_text=json.dumps(blueprint["topic_tags"], ensure_ascii=False),
                    risk_level=str(blueprint["risk_level"]),
                    risk_flags_text=json.dumps(blueprint["risk_flags"], ensure_ascii=False),
                    created_at=entry_dt,
                    updated_at=entry_dt,
                )
            )

    return entries


def _delete_demo_user_rows(db: Session, user: User, *, delete_user: bool) -> None:
    db.query(WrapupSnapshot).filter(WrapupSnapshot.user_id == user.id).delete(synchronize_session=False)
    db.query(TreeStateEvent).filter(TreeStateEvent.user_id == user.id).delete(synchronize_session=False)
    db.query(TreeState).filter(TreeState.user_id == user.id).delete(synchronize_session=False)
    db.query(ProcessingAttempt).filter(ProcessingAttempt.user_id == user.id).delete(synchronize_session=False)
    db.query(JournalEntry).filter(JournalEntry.user_id == user.id).delete(synchronize_session=False)
    db.query(UserPreference).filter(UserPreference.user_id == user.id).delete(synchronize_session=False)
    if delete_user:
        db.delete(user)


def reset_demo_data(db: Session, email: str = DEFAULT_DEMO_EMAIL) -> bool:
    user = get_user_by_email(db, email.lower())
    if user is None:
        return False
    _delete_demo_user_rows(db, user, delete_user=True)
    db.commit()
    return True


def seed_demo_data(
    db: Session,
    *,
    days: int = 30,
    email: str = DEFAULT_DEMO_EMAIL,
    password: str = DEFAULT_DEMO_PASSWORD,
    reset: bool = False,
) -> SeedDemoDataResponse:
    normalized_email = email.lower()
    user = get_user_by_email(db, normalized_email)

    if user is not None:
        _delete_demo_user_rows(db, user, delete_user=False)
        user.password_hash = hash_password(password)
        user.display_name = DEFAULT_DEMO_DISPLAY_NAME
        user.is_active = True
        db.commit()
        db.refresh(user)
    else:
        user = register_user(db, normalized_email, password, DEFAULT_DEMO_DISPLAY_NAME)

    preferences_payload = UpsertPreferenceRequest(
        locale="en",
        timezone="UTC",
        quote_opt_in=True,
        reminder_enabled=True,
        reminder_time="08:30",
        preferred_tree_type="oak",
        checkin_goal_per_day=2,
    )
    upsert_preferences(db, user.id, preferences_payload)

    demo_entries = _build_demo_entries(user.id, days)
    db.add_all(demo_entries)
    db.commit()

    recompute_tree_for_user(db, user.id)
    db.commit()

    weekly_wrapup = generate_wrapup_snapshot(db, user.id, "week")
    monthly_wrapup = generate_wrapup_snapshot(db, user.id, "month")

    return SeedDemoDataResponse(
        user_id=user.id,
        email=user.email,
        days=days,
        entry_count=len(demo_entries),
        weekly_wrapup_id=weekly_wrapup.id,
        monthly_wrapup_id=monthly_wrapup.id,
        reset_applied=reset,
    )
