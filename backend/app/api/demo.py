from fastapi import APIRouter

from app.schemas.demo import DemoAICoreRequest, DemoAICoreResponse, DemoWeeklyInsightResponse
from app.services.demo_service import build_demo_payload, build_demo_weekly_insight


router = APIRouter(prefix="/v1/demo", tags=["demo"])


@router.post("/ai-core", response_model=DemoAICoreResponse)
def post_demo_ai_core(payload: DemoAICoreRequest) -> DemoAICoreResponse:
    return build_demo_payload(
        text=payload.text,
        user_name=payload.user_name,
        context_tag=payload.context_tag,
    )


@router.get("/ai-core/weekly-insight", response_model=DemoWeeklyInsightResponse)
def get_demo_weekly_insight() -> DemoWeeklyInsightResponse:
    return build_demo_weekly_insight()
