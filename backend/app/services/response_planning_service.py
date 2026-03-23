from app.services.empathy_service import build_response_plan as _build_response_plan
from app.services.response_policy_service import select_response_variant, select_suggestion_family


def build_response_plan(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    risk_level: str,
    topic_tags: list[str],
    memory_summary: dict[str, object] | None = None,
    recent_trend: dict[str, object] | None = None,
    session_mode: str | None = None,
    render_context: dict[str, object] | None = None,
    normalized_state: dict[str, object] | None = None,
    support_strategy: dict[str, object] | None = None,
) -> dict[str, object]:
    plan = _build_response_plan(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        recent_trend=memory_summary if memory_summary is not None else recent_trend,
    )
    response_mode = str(emotion_analysis.get("response_mode", "supportive_reflective"))
    dominant_signals = {str(item) for item in emotion_analysis.get("dominant_signals", [])}
    render_context_data = render_context or {}
    normalized_state_data = normalized_state or {}
    support_strategy_data = support_strategy or {}
    user_stance = str(
        render_context_data.get("user_stance")
        or normalized_state_data.get("user_stance")
        or "processing_self"
    )
    event_type = str(
        render_context_data.get("event_type")
        or normalized_state_data.get("event_type")
        or "uncertain_mixed_state"
    )
    support_focus = str(support_strategy_data.get("support_focus") or "user")

    plan["follow_up_question_allowed"] = (
        risk_level == "low"
        and str(emotion_analysis.get("language", "en")) == "en"
        and not bool(plan.get("avoid_advice"))
        and str(emotion_analysis.get("response_mode", "")) not in {"celebratory_warm", "grounding_soft"}
    )
    if str(emotion_analysis.get("response_mode", "")) == "stress_supportive" and risk_level == "low":
        plan["follow_up_question_allowed"] = True
    if user_stance == "worried_about_other" or event_type in {"other_person_distress", "loved_one_unwell"}:
        plan["opening_style"] = "careful_presence"
        plan["acknowledgment_focus"] = "care_for_other"
        plan["suggestion_allowed"] = False
        plan["suggestion_style"] = "none"
        plan["quote_allowed"] = False
        plan["avoid_advice"] = True
        plan["tone"] = "gentle_companion"
        plan["max_sentences"] = min(int(plan.get("max_sentences", 3)), 2)
        plan["follow_up_question_allowed"] = (
            risk_level == "low" and str(emotion_analysis.get("language", "en")) == "en"
        )
    elif user_stance == "guilty_toward_other" or event_type == "responsibility_tension":
        plan["acknowledgment_focus"] = "repair_tension"
        plan["max_sentences"] = min(int(plan.get("max_sentences", 3)), 2)
    elif support_focus == "relationship":
        plan["max_sentences"] = min(int(plan.get("max_sentences", 3)), 2)
    elif len(transcript.split()) <= 2 and event_type == "uncertain_mixed_state":
        plan["suggestion_allowed"] = False
        plan["quote_allowed"] = False
        plan["max_sentences"] = 1

    if session_mode == "realtime":
        plan["max_sentences"] = 1
        plan["quote_allowed"] = False
        plan["suggestion_allowed"] = False
        plan["suggestion_style"] = "none"
        if risk_level == "low":
            plan["follow_up_question_allowed"] = True
    plan["response_mode"] = response_mode
    plan["evidence_bound"] = True
    plan["suggestion_family"] = select_suggestion_family(
        response_mode=response_mode,
        dominant_signals=dominant_signals,
        suggestion_allowed=bool(plan.get("suggestion_allowed")),
        render_context=render_context_data,
        normalized_state=normalized_state_data,
        support_strategy=support_strategy_data,
    )
    plan["response_variant"] = select_response_variant(
        risk_level=risk_level,
        response_mode=response_mode,
        quote_allowed=bool(plan.get("quote_allowed")),
        suggestion_allowed=bool(plan.get("suggestion_allowed")),
        follow_up_question_allowed=bool(plan.get("follow_up_question_allowed")),
        render_context=render_context_data,
        normalized_state=normalized_state_data,
        support_strategy=support_strategy_data,
    )
    if plan["response_variant"] == "empathy_plus_followup":
        plan["suggestion_allowed"] = False
    elif plan["response_variant"] == "empathy_plus_suggestion":
        plan["follow_up_question_allowed"] = False
    elif plan["response_variant"] == "empathy_plus_quote":
        plan["suggestion_allowed"] = False
        plan["follow_up_question_allowed"] = False
    elif plan["response_variant"] == "empathy_only":
        plan["suggestion_allowed"] = False
        plan["follow_up_question_allowed"] = False
    return plan
