from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import enforce_user_owner_access, get_current_user_optional
from app.models.tree_state import TreeState
from app.models.user import User
from app.schemas.user import (
    JournalHistoryItemResponse,
    JournalHistoryResponse,
    TreeStateResponse,
    TreeTimelineResponse,
    UserSummaryResponse,
)
from app.services.journal_service import build_excerpt, get_entry_secondary_labels, get_entry_source_type, list_user_entries
from app.services.summary_service import build_user_summary
from app.services.tree_service import build_tree_timeline

router = APIRouter(prefix="/v1/users", tags=["users"])


@router.get("/{user_id}/tree", response_model=TreeStateResponse)
def get_user_tree(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> TreeStateResponse:
    enforce_user_owner_access(user_id, current_user)
    tree_state = db.query(TreeState).filter(TreeState.user_id == user_id).one_or_none()
    if tree_state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tree state not found")
    return TreeStateResponse.model_validate(tree_state)


@router.get("/{user_id}/summary", response_model=UserSummaryResponse)
def get_user_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> UserSummaryResponse:
    enforce_user_owner_access(user_id, current_user)
    return build_user_summary(db=db, user_id=user_id, days=days)


@router.get("/{user_id}/entries", response_model=JournalHistoryResponse)
def get_user_entries(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> JournalHistoryResponse:
    enforce_user_owner_access(user_id, current_user)
    total, items = list_user_entries(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        session_type=session_type,
        status=status_filter,
        from_date=from_date,
        to_date=to_date,
    )

    return JournalHistoryResponse(
        user_id=user_id,
        total=total,
        limit=limit,
        offset=offset,
        items=[
            JournalHistoryItemResponse(
                id=item.id,
                entry_id=item.id,
                status=item.processing_status,
                session_type=item.session_type,
                source_type=get_entry_source_type(item),
                transcript_excerpt=build_excerpt(item.transcript_text),
                ai_response_excerpt=build_excerpt(item.ai_response),
                primary_label=item.emotion_label,
                secondary_labels=get_entry_secondary_labels(item),
                stress_score=item.stress_score,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in items
        ],
    )


@router.get("/{user_id}/tree/timeline", response_model=TreeTimelineResponse)
def get_user_tree_timeline(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> TreeTimelineResponse:
    enforce_user_owner_access(user_id, current_user)
    return build_tree_timeline(db=db, user_id=user_id, days=days)
