from sqlalchemy.orm import Session

from app.models.user_preference import UserPreference
from app.schemas.me import UpsertPreferenceRequest


def get_or_create_preferences(db: Session, user_id: str) -> UserPreference:
    preferences = db.query(UserPreference).filter(UserPreference.user_id == user_id).one_or_none()
    if preferences is None:
        preferences = UserPreference(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return preferences


def upsert_preferences(db: Session, user_id: str, payload: UpsertPreferenceRequest) -> UserPreference:
    preferences = db.query(UserPreference).filter(UserPreference.user_id == user_id).one_or_none()
    if preferences is None:
        preferences = UserPreference(user_id=user_id)
        db.add(preferences)

    preferences.locale = payload.locale
    preferences.timezone = payload.timezone
    preferences.quote_opt_in = payload.quote_opt_in
    preferences.reminder_enabled = payload.reminder_enabled
    preferences.reminder_time = payload.reminder_time
    preferences.preferred_tree_type = payload.preferred_tree_type
    preferences.checkin_goal_per_day = payload.checkin_goal_per_day
    db.commit()
    db.refresh(preferences)
    return preferences
