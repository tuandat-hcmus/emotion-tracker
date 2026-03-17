from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user_required
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.checkin import EmotionAnalysisResponse, RespondPreviewRequest, RespondPreviewResponse, ResponsePlanResponse, ResponseQuoteResponse
from app.schemas.me import (
    CalendarResponse,
    CheckinStatusResponse,
    HomeResponse,
    PreferenceResponse,
    UpdateMeRequest,
    UpsertPreferenceRequest,
    UserProfileResponse,
    WrapupRegenerateRequest,
    WrapupSnapshotResponse,
)
from app.services.calendar_service import build_calendar, build_checkin_status, resolve_user_today, resolve_user_timezone
from app.services.home_service import build_home_response
from app.services.ai_support_service import build_support_package
from app.services.preferences_service import get_or_create_preferences, upsert_preferences
from app.services.user_service import update_display_name
from app.services.wrapup_service import generate_wrapup_snapshot, get_latest_wrapup_snapshot

router = APIRouter(prefix="/v1/me", tags=["me"])


@router.get("", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user_required), db: Session = Depends(get_db)) -> UserProfileResponse:
    preferences = get_or_create_preferences(db, current_user.id)
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        preferences=PreferenceResponse.model_validate(preferences),
    )


@router.patch("", response_model=UserProfileResponse)
def patch_me(
    payload: UpdateMeRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    updated_user = update_display_name(db, current_user, payload.display_name)
    preferences = get_or_create_preferences(db, updated_user.id)
    return UserProfileResponse(
        id=updated_user.id,
        email=updated_user.email,
        display_name=updated_user.display_name,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        preferences=PreferenceResponse.model_validate(preferences),
    )


@router.get("/preferences", response_model=PreferenceResponse)
def get_me_preferences(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    preferences = get_or_create_preferences(db, current_user.id)
    return PreferenceResponse.model_validate(preferences)


@router.put("/preferences", response_model=PreferenceResponse)
def put_me_preferences(
    payload: UpsertPreferenceRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> PreferenceResponse:
    preferences = upsert_preferences(db, current_user.id, payload)
    return PreferenceResponse.model_validate(preferences)


@router.get("/home", response_model=HomeResponse)
def get_me_home(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> HomeResponse:
    return build_home_response(db, current_user)


@router.get("/checkin-status", response_model=CheckinStatusResponse)
def get_me_checkin_status(
    date_value: date | None = Query(None, alias="date"),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> CheckinStatusResponse:
    preferences = get_or_create_preferences(db, current_user.id)
    tzinfo = resolve_user_timezone(preferences)
    target_date = date_value or resolve_user_today(preferences)
    return build_checkin_status(db, current_user.id, target_date, tzinfo)


@router.get("/calendar", response_model=CalendarResponse)
def get_me_calendar(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> CalendarResponse:
    preferences = get_or_create_preferences(db, current_user.id)
    return build_calendar(
        db=db,
        user_id=current_user.id,
        days=days,
        end_date=resolve_user_today(preferences),
        tzinfo=resolve_user_timezone(preferences),
    )


@router.get("/wrapups/weekly/latest", response_model=WrapupSnapshotResponse)
def get_latest_weekly_wrapup(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> WrapupSnapshotResponse:
    return get_latest_wrapup_snapshot(db, current_user.id, "week")


@router.get("/wrapups/monthly/latest", response_model=WrapupSnapshotResponse)
def get_latest_monthly_wrapup(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> WrapupSnapshotResponse:
    return get_latest_wrapup_snapshot(db, current_user.id, "month")


@router.post("/wrapups/regenerate", response_model=WrapupSnapshotResponse)
def regenerate_wrapup(
    payload: WrapupRegenerateRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> WrapupSnapshotResponse:
    return generate_wrapup_snapshot(db, current_user.id, payload.period_type, payload.anchor_date)


@router.post("/respond-preview", response_model=RespondPreviewResponse)
def post_respond_preview(
    payload: RespondPreviewRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> RespondPreviewResponse:
    preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).one_or_none()
    support_package = build_support_package(
        transcript=payload.transcript,
        user_id=current_user.id,
        audio_path=None,
        quote_opt_in=preferences.quote_opt_in if preferences is not None else True,
        override_risk_level=payload.override_risk_level,
        override_topic_tags=payload.override_topic_tags,
    )
    quote = support_package["quote"]
    return RespondPreviewResponse(
        emotion_analysis=EmotionAnalysisResponse(
            emotion_label=str(support_package["emotion_analysis"]["emotion_label"]),
            valence_score=float(support_package["emotion_analysis"]["valence_score"]),
            energy_score=float(support_package["emotion_analysis"]["energy_score"]),
            stress_score=float(support_package["emotion_analysis"]["stress_score"]),
            social_need_score=float(support_package["emotion_analysis"]["social_need_score"]),
            confidence=float(support_package["emotion_analysis"]["confidence"]),
            dominant_signals=list(support_package["emotion_analysis"]["dominant_signals"]),
            response_mode=str(support_package["emotion_analysis"]["response_mode"]),
            language=str(support_package["emotion_analysis"]["language"]),
            primary_emotion=str(support_package["emotion_analysis"]["primary_emotion"]),
            secondary_emotions=list(support_package["emotion_analysis"]["secondary_emotions"]),
            source=str(support_package["emotion_analysis"]["source"]),
            raw_model_labels=list(support_package["emotion_analysis"]["raw_model_labels"]),
            provider_name=str(support_package["emotion_analysis"]["provider_name"]),
        ),
        topic_tags=list(support_package["topic_tags"]),
        risk_level=str(support_package["risk_level"]),
        risk_flags=list(support_package["risk_flags"]),
        response_plan=ResponsePlanResponse(**support_package["response_plan"]),
        empathetic_response=str(support_package["empathetic_response"]),
        gentle_suggestion=(
            str(support_package["gentle_suggestion"]) if support_package["gentle_suggestion"] is not None else None
        ),
        quote=ResponseQuoteResponse(**quote.model_dump()) if quote is not None else None,
        ai_response=str(support_package["ai_response"]),
    )
