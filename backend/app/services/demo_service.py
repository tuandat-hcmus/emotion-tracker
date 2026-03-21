from app.core.config import get_settings
from app.schemas.demo import DemoAICoreResponse, DemoWeeklyInsightResponse
from app.services.ai_core.language_service import detect_language
from app.services.en_demo_service import build_en_demo_payload, build_en_weekly_insight
from app.services.vi_demo_service import build_vi_demo_payload


def build_demo_payload(
    *,
    text: str,
    user_name: str | None = None,
    context_tag: str | None = None,
) -> DemoAICoreResponse:
    settings = get_settings()
    detected_language = detect_language(text)
    if detected_language == "vi":
        return build_vi_demo_payload(text=text, user_name=user_name, context_tag=context_tag)
    if settings.main_language == "en" or detected_language in {"en", "unknown"}:
        return build_en_demo_payload(text=text, user_name=user_name, context_tag=context_tag)
    return build_en_demo_payload(text=text, user_name=user_name, context_tag=context_tag)


def build_demo_weekly_insight() -> DemoWeeklyInsightResponse:
    settings = get_settings()
    if settings.main_language == "en":
        return build_en_weekly_insight()
    return build_en_weekly_insight()
