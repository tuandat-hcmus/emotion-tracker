from collections.abc import Callable
from dataclasses import dataclass

from app.services.companion_core.contextual_inference import align_emotion_analysis_with_context
from app.services.companion_core.emotion_understanding import build_normalized_emotional_state
from app.services.companion_core.feature_extraction import extract_insight_features
from app.services.companion_core.memory_summary import build_memory_summary
from app.services.companion_core.recent_context_service import refine_with_recent_context
from app.services.companion_core.render_context import detect_render_context
from app.services.companion_core.schemas import (
    EmotionalMemoryRecord,
    InsightFeatures,
    MemorySummary,
    NormalizedEmotionalState,
    RenderContext,
    SupportStrategy,
)
from app.services.companion_core.strategy_engine import select_support_strategy
from app.services.response_planning_service import build_response_plan


EmotionPostprocessor = Callable[[dict[str, object], RenderContext], dict[str, object]]


@dataclass(frozen=True)
class CompanionPipelineResult:
    emotion_analysis: dict[str, object]
    render_context: RenderContext
    normalized_state: NormalizedEmotionalState
    memory_summary: MemorySummary
    insight_features: InsightFeatures
    support_strategy: SupportStrategy
    response_plan: dict[str, object]


def build_companion_pipeline(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    topic_tags: list[str],
    risk_level: str,
    context_tag: str | None = None,
    memory_records: list[EmotionalMemoryRecord] | None = None,
    recent_trend: dict[str, object] | None = None,
    emotion_postprocessor: EmotionPostprocessor | None = None,
) -> CompanionPipelineResult:
    render_context = detect_render_context(transcript, topic_tags, context_tag=context_tag)
    effective_emotion_analysis = align_emotion_analysis_with_context(dict(emotion_analysis), render_context)
    if emotion_postprocessor is not None:
        effective_emotion_analysis = emotion_postprocessor(effective_emotion_analysis, render_context)

    normalized_state = build_normalized_emotional_state(
        emotion_analysis=effective_emotion_analysis,
        render_context=render_context.model_dump(),
        topic_tags=topic_tags,
        risk_level=risk_level,
    )
    recent_memory = list(memory_records or [])
    memory_summary = build_memory_summary(recent_memory)
    insight_features = extract_insight_features(normalized_state)
    effective_emotion_analysis, normalized_state, insight_features = refine_with_recent_context(
        emotion_analysis=effective_emotion_analysis,
        normalized_state=normalized_state,
        memory_summary=memory_summary,
        insight_features=insight_features,
        memory_records=recent_memory,
        risk_level=risk_level,
    )
    support_strategy = select_support_strategy(normalized_state, memory_summary=memory_summary)
    response_plan = build_response_plan(
        transcript=transcript,
        emotion_analysis=effective_emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        recent_trend=recent_trend,
    )
    response_plan["render_context"] = render_context.model_dump()
    response_plan["normalized_state"] = normalized_state.model_dump()
    response_plan["support_strategy"] = support_strategy.model_dump()
    response_plan["memory_context"] = {
        **memory_summary.model_dump(),
        "recent_primary_emotions": [record.normalized_state.primary_emotion for record in recent_memory[-3:]],
    }
    response_plan["insight_features"] = insight_features.model_dump()

    return CompanionPipelineResult(
        emotion_analysis=effective_emotion_analysis,
        render_context=render_context,
        normalized_state=normalized_state,
        memory_summary=memory_summary,
        insight_features=insight_features,
        support_strategy=support_strategy,
        response_plan=response_plan,
    )


def build_emotional_memory_record(
    *,
    user_id: str,
    transcript: str,
    topic_tags: list[str],
    risk_level: str,
    normalized_state: NormalizedEmotionalState,
    support_strategy: SupportStrategy,
    insight_features: InsightFeatures,
    response_provider: str,
    response_mode: str,
    suggestion_given: bool,
    support_metadata: dict[str, object] | None = None,
) -> EmotionalMemoryRecord:
    return EmotionalMemoryRecord(
        user_id=user_id,
        transcript=transcript,
        language=normalized_state.language,
        normalized_state=normalized_state,
        support_strategy=support_strategy,
        topic_tags=topic_tags,
        risk_level=risk_level,
        suggestion_given=suggestion_given,
        response_provider=response_provider,
        response_mode=response_mode,
        support_metadata=support_metadata or {"response_goal": support_strategy.response_goal},
        insight_features=insight_features,
    )
