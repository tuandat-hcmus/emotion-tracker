from datetime import date

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user_required
from app.models.user import User
from app.schemas.checkin import RespondPreviewRequest, RespondPreviewResponse
from app.schemas.me import (
    CalendarResponse,
    CheckinStatusResponse,
    HomeResponse,
    MonthlyWrapupDetailResponse,
    PreferenceResponse,
    UpdateMeRequest,
    UpsertPreferenceRequest,
    UserProfileResponse,
    WrapupRegenerateRequest,
    WrapupSnapshotResponse,
)
from app.services.calendar_service import build_calendar, build_checkin_status, resolve_user_today, resolve_user_timezone
from app.services.home_service import build_home_response
from app.services.preferences_service import get_or_create_preferences, upsert_preferences
from app.services.respond_preview_service import build_respond_preview_response
from app.services.user_service import update_display_name
from app.services.wrapup_service import (
    build_monthly_wrapup_detail,
    generate_wrapup_snapshot,
    get_latest_monthly_wrapup_detail,
    get_latest_wrapup_snapshot,
)

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


@router.get("/wrapups/monthly/latest/detail", response_model=MonthlyWrapupDetailResponse)
def get_latest_monthly_wrapup_detail_route(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> MonthlyWrapupDetailResponse:
    return get_latest_monthly_wrapup_detail(db, current_user.id)


@router.get("/wrapups/monthly/{year}/{month}", response_model=MonthlyWrapupDetailResponse)
def get_monthly_wrapup_detail(
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> MonthlyWrapupDetailResponse:
    return build_monthly_wrapup_detail(db, current_user.id, year, month)


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
    return build_respond_preview_response(
        db=db,
        current_user=current_user,
        payload=payload,
    )
