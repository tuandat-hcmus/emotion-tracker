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
    plan["follow_up_question_allowed"] = (
        risk_level == "low"
        and str(emotion_analysis.get("language", "en")) == "en"
        and not bool(plan.get("avoid_advice"))
        and str(emotion_analysis.get("response_mode", "")) not in {"celebratory_warm", "grounding_soft"}
    )
    if str(emotion_analysis.get("response_mode", "")) == "stress_supportive" and risk_level == "low":
        plan["follow_up_question_allowed"] = True
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
    )
    plan["response_variant"] = select_response_variant(
        risk_level=risk_level,
        response_mode=response_mode,
        quote_allowed=bool(plan.get("quote_allowed")),
        suggestion_allowed=bool(plan.get("suggestion_allowed")),
        follow_up_question_allowed=bool(plan.get("follow_up_question_allowed")),
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
