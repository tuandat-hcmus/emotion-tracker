from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def health_live() -> dict[str, str]:
    return {"status": "ok", "service": "live"}


@router.get("/ready", response_model=None)
def health_ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        dialect = db.bind.dialect.name if db.bind else "unknown"
        return {"status": "ok", "service": "ready", "database": {"status": "ok", "dialect": dialect}}
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "service": "ready",
                "database": {"status": "unavailable"},
                "detail": str(exc),
            },
        )
