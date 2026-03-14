from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.models.tree_state import TreeState
from app.models.user import User
from app.schemas.me import (
    HomeLatestWrapupMetaResponse,
    HomePreferencesSummaryResponse,
    HomeRecentTrendResponse,
    HomeResponse,
    HomeTodayResponse,
    HomeTreeResponse,
    HomeUserSummaryResponse,
)
from app.services.calendar_service import (
    _average,
    build_checkin_status,
    list_entries_for_local_date_range,
    resolve_user_today,
    resolve_user_timezone,
)
from app.services.preferences_service import get_or_create_preferences
from app.services.quote_service import select_quote
from app.services.wrapup_service import get_latest_wrapup_meta


def build_home_response(db: Session, user: User) -> HomeResponse:
    preferences = get_or_create_preferences(db, user.id)
    tzinfo = resolve_user_timezone(preferences)
    today = resolve_user_today(preferences)
    checkin_status = build_checkin_status(db, user.id, today, tzinfo)

    tree_state = db.query(TreeState).filter(TreeState.user_id == user.id).one_or_none()
    recent_entries = list_entries_for_local_date_range(db, user.id, today - timedelta(days=6), today, tzinfo)
    weekly_generated_at, monthly_generated_at = get_latest_wrapup_meta(db, user.id)

    return HomeResponse(
        user=HomeUserSummaryResponse(id=user.id, email=user.email, display_name=user.display_name),
        preferences_summary=HomePreferencesSummaryResponse(
            quote_opt_in=preferences.quote_opt_in,
            reminder_enabled=preferences.reminder_enabled,
            reminder_time=preferences.reminder_time,
            preferred_tree_type=preferences.preferred_tree_type,
            checkin_goal_per_day=preferences.checkin_goal_per_day,
        ),
        today=HomeTodayResponse(
            **checkin_status.model_dump(),
            total_entries_today=checkin_status.total_entries,
        ),
        tree=HomeTreeResponse(
            vitality_score=tree_state.vitality_score if tree_state else 0,
            streak_days=tree_state.streak_days if tree_state else 0,
            current_stage=tree_state.current_stage if tree_state else None,
            leaf_state=tree_state.leaf_state if tree_state else None,
            weather_state=tree_state.weather_state if tree_state else None,
            last_checkin_date=tree_state.last_checkin_date if tree_state else None,
        ),
        recent_trend=HomeRecentTrendResponse(
            last_7_days_average_valence=_average([entry.valence_score for entry in recent_entries]),
            last_7_days_average_stress=_average([entry.stress_score for entry in recent_entries]),
            entries_last_7_days=len(recent_entries),
        ),
        quote=select_quote(
            quote_opt_in=preferences.quote_opt_in,
            latest_emotion_label=checkin_status.latest_emotion_label,
            latest_risk_level=checkin_status.latest_risk_level,
            user_id=user.id,
        ),
        latest_wrapup_meta=HomeLatestWrapupMetaResponse(
            latest_weekly_wrapup_at=weekly_generated_at,
            latest_monthly_wrapup_at=monthly_generated_at,
        ),
    )
