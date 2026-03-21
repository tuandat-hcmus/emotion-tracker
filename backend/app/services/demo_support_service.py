from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services.companion_core import get_demo_memory_store
from app.services.safety_service import detect_safety_risk
from app.services.topic_service import tag_topics


def ensure_demo_enabled(*, get_settings_fn=get_settings) -> None:
    settings = get_settings_fn()
    if not settings.enable_ai_core_demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI core demo is disabled")


def build_demo_topics(
    text: str,
    context_tag: str | None,
    *,
    tag_topics_fn=tag_topics,
) -> list[str]:
    topic_tags = tag_topics_fn(text)
    if context_tag and context_tag.strip() and context_tag.strip() not in topic_tags:
        topic_tags = [context_tag.strip(), *topic_tags][:3]
    return topic_tags


def build_demo_safety_context(
    text: str,
    context_tag: str | None,
    *,
    detect_safety_risk_fn=detect_safety_risk,
    tag_topics_fn=tag_topics,
) -> tuple[dict[str, object], str, list[str]]:
    safety_result = detect_safety_risk_fn(text)
    risk_level = str(safety_result["risk_level"])
    topic_tags = build_demo_topics(text, context_tag, tag_topics_fn=tag_topics_fn)
    return safety_result, risk_level, topic_tags


def list_recent_demo_memory(memory_key: str, *, days: int = 7, get_demo_memory_store_fn=get_demo_memory_store):
    memory_store = get_demo_memory_store_fn()
    return memory_store.list_recent(memory_key, days=days)
