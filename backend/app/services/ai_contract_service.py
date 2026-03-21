from typing import Any

from app.schemas.checkin import (
    AIContractResponse,
    AIEmotionContractResponse,
    AIInsightFeaturesContractResponse,
    AIMemoryContractResponse,
    AIResponseContractResponse,
    AIRiskContractResponse,
    AIStateContractResponse,
    AIStrategyContractResponse,
    AITopicsContractResponse,
    ResponsePlanResponse,
    ResponseQuoteResponse,
)
from app.services.ai_core.language_service import normalize_language_code
from app.services.emotion_service import to_frontend_label


def _to_dict(value: dict[str, Any] | Any | None) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return dict(model_dump())
    return {}


def _to_response_plan(plan: dict[str, Any] | Any | None) -> ResponsePlanResponse | None:
    plan_dict = _to_dict(plan)
    required_fields = {
        "opening_style",
        "acknowledgment_focus",
        "suggestion_allowed",
        "suggestion_style",
        "quote_allowed",
        "avoid_advice",
        "tone",
        "max_sentences",
        "follow_up_question_allowed",
    }
    if not required_fields.issubset(plan_dict):
        return None
    return ResponsePlanResponse(**plan_dict)


def _to_quote(quote: dict[str, Any] | Any | None) -> ResponseQuoteResponse | None:
    quote_dict = _to_dict(quote)
    required_fields = {"short_text", "tone", "source_type"}
    if not required_fields.issubset(quote_dict):
        return None
    return ResponseQuoteResponse(**{field: quote_dict[field] for field in required_fields})


def build_ai_contract(
    *,
    emotion_analysis: dict[str, Any] | Any | None = None,
    risk_level: str | None = None,
    risk_flags: list[str] | None = None,
    topic_tags: list[str] | None = None,
    response_plan: dict[str, Any] | Any | None = None,
    empathetic_response: str | None = None,
    gentle_suggestion: str | None = None,
    follow_up_question: str | None = None,
    quote: dict[str, Any] | Any | None = None,
    ai_response: str | None = None,
    normalized_state: dict[str, Any] | Any | None = None,
    support_strategy: dict[str, Any] | Any | None = None,
    memory_summary: dict[str, Any] | Any | None = None,
    insight_features: dict[str, Any] | Any | None = None,
) -> AIContractResponse:
    emotion = _to_dict(emotion_analysis)
    state = _to_dict(normalized_state)
    strategy = _to_dict(support_strategy)
    memory = _to_dict(memory_summary)
    insights = _to_dict(insight_features)
    response_quote = _to_quote(quote)
    state_primary_label = _coerce_str(
        emotion.get("primary_label"),
        to_frontend_label(str(state.get("primary_emotion"))) if state.get("primary_emotion") else None,
    )
    explicit_state_secondary = [
        to_frontend_label(str(item))
        for item in state.get("secondary_emotions", [])
        if to_frontend_label(str(item)) != state_primary_label
    ]
    emotion_secondary = [
        str(item) for item in emotion.get("secondary_labels", []) if str(item) != state_primary_label
    ]
    state_secondary_labels = list(dict.fromkeys(emotion_secondary or explicit_state_secondary))

    return AIContractResponse(
        emotion=AIEmotionContractResponse(
            primary_label=_coerce_str(emotion.get("primary_label")),
            secondary_labels=[str(item) for item in emotion.get("secondary_labels", [])],
            all_labels=[str(item) for item in emotion.get("all_labels", [])],
            scores={str(label): float(score) for label, score in dict(emotion.get("scores", {})).items()},
            threshold=_coerce_float(emotion.get("threshold")),
            valence_score=_coerce_float(emotion.get("valence_score"), state.get("valence")),
            energy_score=_coerce_float(emotion.get("energy_score"), state.get("energy")),
            stress_score=_coerce_float(emotion.get("stress_score"), state.get("stress")),
            social_need_score=_coerce_float(emotion.get("social_need_score")),
            confidence=_coerce_float(emotion.get("confidence"), state.get("confidence")),
            dominant_signals=[str(item) for item in emotion.get("dominant_signals", [])],
            context_tags=[str(item) for item in emotion.get("context_tags", [])],
            enrichment_notes=[str(item) for item in emotion.get("enrichment_notes", [])],
            response_mode=_coerce_str(emotion.get("response_mode"), state.get("response_mode")),
            language=normalize_language_code(_coerce_str(emotion.get("language"), "en")),
            provider_name=_coerce_str(emotion.get("provider_name")),
            source=_coerce_str(emotion.get("source")),
        ),
        risk=AIRiskContractResponse(
            level=risk_level,
            flags=[str(item) for item in (risk_flags or [])],
        ),
        topics=AITopicsContractResponse(
            tags=[str(item) for item in (topic_tags or [])],
        ),
        response=AIResponseContractResponse(
            plan=_to_response_plan(response_plan),
            empathetic_text=empathetic_response,
            follow_up_question=follow_up_question,
            suggestion_text=gentle_suggestion,
            composed_text=ai_response,
            quote=response_quote,
        ),
        state=AIStateContractResponse(
            primary_label=state_primary_label,
            secondary_labels=state_secondary_labels,
            valence_score=_coerce_float(state.get("valence"), emotion.get("valence_score")),
            energy_score=_coerce_float(state.get("energy"), emotion.get("energy_score")),
            stress_score=_coerce_float(state.get("stress"), emotion.get("stress_score")),
            emotion_owner=_coerce_str(state.get("emotion_owner")),
            social_context=_coerce_str(state.get("social_context")),
            event_type=_coerce_str(state.get("event_type")),
            concern_target=_coerce_str(state.get("concern_target")),
            uncertainty=_coerce_float(state.get("uncertainty")),
            confidence=_coerce_float(state.get("confidence"), emotion.get("confidence")),
            response_mode=_coerce_str(state.get("response_mode"), emotion.get("response_mode")),
            risk_level=_coerce_str(state.get("risk_level"), risk_level),
        ),
        strategy=AIStrategyContractResponse(
            support_focus=_coerce_str(strategy.get("support_focus")),
            strategy_type=_coerce_str(strategy.get("strategy_type")),
            suggestion_budget=_coerce_str(strategy.get("suggestion_budget")),
            personalization_tone=_coerce_str(strategy.get("personalization_tone")),
            response_goal=_coerce_str(strategy.get("response_goal")),
            rationale=[str(item) for item in strategy.get("rationale", [])],
        ),
        memory=AIMemoryContractResponse(
            recent_checkin_count=_coerce_int(memory.get("recent_checkin_count")),
            dominant_negative_patterns=[str(item) for item in memory.get("dominant_negative_patterns", [])],
            dominant_positive_patterns=[str(item) for item in memory.get("dominant_positive_patterns", [])],
            recurring_triggers=[str(item) for item in memory.get("recurring_triggers", [])],
            recurring_social_contexts=[str(item) for item in memory.get("recurring_social_contexts", [])],
            last_seen_emotional_direction=_coerce_str(memory.get("last_seen_emotional_direction")),
            pattern_detected=_coerce_bool(memory.get("pattern_detected")),
            insight_features=AIInsightFeaturesContractResponse(
                is_negative_checkin=_coerce_bool(insights.get("is_negative_checkin")),
                is_positive_checkin=_coerce_bool(insights.get("is_positive_checkin")),
                work_trigger=_coerce_bool(insights.get("work_trigger")),
                relationship_strain=_coerce_bool(insights.get("relationship_strain")),
                deadline_related=_coerce_bool(insights.get("deadline_related")),
                loneliness_related=_coerce_bool(insights.get("loneliness_related")),
                positive_anchor_candidate=_coerce_bool(insights.get("positive_anchor_candidate")),
                social_support_signal=_coerce_bool(insights.get("social_support_signal")),
                high_stress_flag=_coerce_bool(insights.get("high_stress_flag")),
            ) if insights else None,
        ),
    )


def _coerce_str(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        return str(value)
    return None


def _coerce_float(*values: Any) -> float | None:
    for value in values:
        if value is None:
            continue
        return float(value)
    return None


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)
