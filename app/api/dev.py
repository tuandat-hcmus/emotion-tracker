from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import app.core.config as config_module
from app.db.session import get_db
from app.schemas.dev import (
    ResetDemoDataRequest,
    ResetDemoDataResponse,
    SeedDemoDataRequest,
    SeedDemoDataResponse,
)
from app.services.demo_seed_service import reset_demo_data, seed_demo_data

router = APIRouter(prefix="/v1/dev", tags=["dev"])


def _ensure_dev_seed_enabled() -> None:
    if not config_module.get_settings().enable_dev_seed_endpoints:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.post("/seed-demo-data", response_model=SeedDemoDataResponse)
def seed_demo_data_endpoint(
    payload: SeedDemoDataRequest,
    db: Session = Depends(get_db),
) -> SeedDemoDataResponse:
    _ensure_dev_seed_enabled()
    return seed_demo_data(
        db,
        days=payload.days,
        email=payload.email,
        password=payload.password,
        reset=payload.reset,
    )


@router.post("/reset-demo-data", response_model=ResetDemoDataResponse)
def reset_demo_data_endpoint(
    payload: ResetDemoDataRequest,
    db: Session = Depends(get_db),
) -> ResetDemoDataResponse:
    _ensure_dev_seed_enabled()
    removed_user = reset_demo_data(db, payload.email)
    return ResetDemoDataResponse(email=payload.email.lower(), removed_user=removed_user)
