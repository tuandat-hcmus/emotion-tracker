import logging

from app.services.emotion_service import analyze_emotion
from app.services.companion_core import build_companion_pipeline
from app.services.companion_core.schemas import EmotionalMemoryRecord
from app.services.response_service import generate_supportive_response
from app.services.safety_service import detect_safety_risk
from app.services.topic_service import tag_topics

logger = logging.getLogger(__name__)


def build_support_package(
    *,
    transcript: str,
    user_id: str,
    audio_path: str | None = None,
    quote_opt_in: bool = True,
    override_risk_level: str | None = None,
    override_topic_tags: list[str] | None = None,
    recent_trend: dict[str, object] | None = None,
    memory_records: list[EmotionalMemoryRecord] | None = None,
    emotion_analysis_override: dict[str, object] | None = None,
    session_mode: str | None = None,
) -> dict[str, object]:
    safety_result = detect_safety_risk(transcript)
    risk_level = override_risk_level or str(safety_result["risk_level"])
    topic_tags = override_topic_tags or tag_topics(transcript)
    logger.info(
        "ai_support.start user_id=%s transcript_chars=%s risk_level=%s topic_count=%s recent_memory=%s",
        user_id,
        len(transcript),
        risk_level,
        len(topic_tags),
        len(memory_records or []),
    )
    emotion_analysis = emotion_analysis_override or analyze_emotion(transcript, risk_level=risk_level, audio_path=audio_path)
    logger.info(
        "ai_support.emotion user_id=%s primary_label=%s provider=%s language=%s response_mode=%s",
        user_id,
        emotion_analysis.get("primary_label"),
        emotion_analysis.get("provider_name"),
        emotion_analysis.get("language"),
        emotion_analysis.get("response_mode"),
    )
    companion_pipeline = build_companion_pipeline(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        context_tag=None,
        memory_records=memory_records,
        recent_trend=recent_trend,
        session_mode=session_mode,
    )
    response_payload = generate_supportive_response(
        transcript=transcript,
        emotion_analysis=companion_pipeline.emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        response_plan=companion_pipeline.response_plan,
        memory_summary=companion_pipeline.memory_summary.model_dump(),
        user_id=user_id,
        quote_opt_in=quote_opt_in,
    )
    logger.info(
        "ai_support.complete user_id=%s primary_label=%s risk_level=%s response_variant=%s response_mode=%s",
        user_id,
        companion_pipeline.emotion_analysis.get("primary_label"),
        risk_level,
        companion_pipeline.response_plan.get("response_variant"),
        companion_pipeline.response_plan.get("response_mode"),
    )
    return {
        "emotion_analysis": companion_pipeline.emotion_analysis,
        "topic_tags": topic_tags,
        "risk_level": risk_level,
        "risk_flags": list(safety_result["risk_flags"]),
        "render_context": companion_pipeline.render_context.model_dump(),
        "normalized_state": companion_pipeline.normalized_state.model_dump(),
        "memory_summary": companion_pipeline.memory_summary.model_dump(),
        "insight_features": companion_pipeline.insight_features.model_dump(),
        "support_strategy": companion_pipeline.support_strategy.model_dump(),
        "response_plan": companion_pipeline.response_plan,
        **response_payload,
    }
