from __future__ import annotations


def select_suggestion_family(
    *,
    response_mode: str,
    dominant_signals: set[str],
    suggestion_allowed: bool,
    render_context: dict[str, object] | None = None,
    normalized_state: dict[str, object] | None = None,
    support_strategy: dict[str, object] | None = None,
) -> str | None:
    user_stance = str((render_context or {}).get("user_stance") or (normalized_state or {}).get("user_stance") or "")
    event_type = str((render_context or {}).get("event_type") or (normalized_state or {}).get("event_type") or "")

    if not suggestion_allowed:
        return None
    if user_stance == "worried_about_other" or event_type == "greeting_or_opening":
        return None
    if response_mode == "stress_supportive":
        return "scope_narrowing"
    if response_mode == "grounding_soft":
        return "pause_before_action" if "anger_friction" in dominant_signals else "small_grounding"
    if response_mode == "validating_gentle":
        return "pause_before_action" if "anger_friction" in dominant_signals else "self_validation"
    if response_mode == "low_energy_comfort":
        return "self_validation"
    if response_mode == "celebratory_warm":
        return "warm_reinforcement"
    return "gentle_reflection"


def select_response_variant(
    *,
    risk_level: str,
    response_mode: str,
    quote_allowed: bool,
    suggestion_allowed: bool,
    follow_up_question_allowed: bool,
    render_context: dict[str, object] | None = None,
    normalized_state: dict[str, object] | None = None,
    support_strategy: dict[str, object] | None = None,
) -> str:
    user_stance = str((render_context or {}).get("user_stance") or (normalized_state or {}).get("user_stance") or "")
    event_type = str((render_context or {}).get("event_type") or (normalized_state or {}).get("event_type") or "")
    support_focus = str((support_strategy or {}).get("support_focus") or "")
    response_goal = str((support_strategy or {}).get("response_goal") or "")
    short_personal_update = bool((render_context or {}).get("short_personal_update"))
    reflective_checkin = bool((render_context or {}).get("reflective_checkin"))
    distress_checkin = bool((render_context or {}).get("distress_checkin"))
    low_energy_update = bool((render_context or {}).get("low_energy_update"))
    positive_personal_update = bool((render_context or {}).get("positive_personal_update"))

    if risk_level != "low":
        return "empathy_only"
    if event_type == "greeting_or_opening":
        return "empathy_only"
    if response_goal == "reinforce_positive_moment":
        return "empathy_only"
    if user_stance == "worried_about_other" or support_focus == "relationship":
        return "empathy_plus_followup" if follow_up_question_allowed else "empathy_only"
    if quote_allowed and response_mode == "celebratory_warm":
        return "empathy_plus_quote"
    if response_mode == "supportive_reflective":
        if not follow_up_question_allowed:
            return "empathy_only"
        if short_personal_update or low_energy_update or positive_personal_update:
            return "empathy_only"
        if reflective_checkin or distress_checkin:
            return "empathy_plus_followup"
        return "empathy_only"
    if response_mode == "validating_gentle":
        if not follow_up_question_allowed:
            return "empathy_only"
        if short_personal_update or low_energy_update:
            return "empathy_only"
        return "empathy_plus_followup"
    if follow_up_question_allowed and response_mode == "stress_supportive":
        return "empathy_plus_followup"
    if suggestion_allowed:
        return "empathy_plus_suggestion"
    return "empathy_only"


def build_suggestion_text(
    *,
    suggestion_family: str | None,
    language: str,
    render_context: dict[str, object] | None = None,
    normalized_state: dict[str, object] | None = None,
    support_strategy: dict[str, object] | None = None,
) -> str | None:
    user_stance = str((render_context or {}).get("user_stance") or (normalized_state or {}).get("user_stance") or "")

    if suggestion_family is None:
        return None
    if user_stance == "worried_about_other":
        return None
    if language == "vi":
        templates = {
            "small_grounding": "Nếu thấy hợp, chỉ cần chậm lại một nhịp trước khi quyết định điều tiếp theo.",
            "scope_narrowing": "Nếu thấy hợp, chỉ chọn đúng một việc nhỏ nhất cần làm tiếp theo thay vì nhìn cả đống việc cùng lúc.",
            "gentle_reflection": "Nếu muốn, bạn có thể gọi tên phần đang nặng nhất trước rồi để phần còn lại lại sau.",
            "self_validation": "Nếu muốn, bạn có thể tự nhắc rằng cảm giác này đủ khó rồi và bạn không cần ép mình xử lý hết ngay bây giờ.",
            "warm_reinforcement": "Nếu muốn, hãy giữ lại một chi tiết nhỏ cho thấy phần dịu hơn này là có thật.",
            "pause_before_action": "Nếu thấy hợp, cho mình một khoảng dừng ngắn trước khi phản ứng hoặc quyết định điều gì tiếp theo.",
        }
    else:
        templates = {
            "small_grounding": "If it helps, slow this down to one calmer beat before deciding what comes next.",
            "scope_narrowing": "If it helps, narrow this down to the very next smallest thing instead of the whole pile.",
            "gentle_reflection": "If you want, name the heaviest part first and let the rest stay in the background for now.",
            "self_validation": "If it helps, remind yourself that this already feels like a lot, and you do not have to solve all of it at once.",
            "warm_reinforcement": "If you want, hold onto one small detail that shows this steadier moment is real.",
            "pause_before_action": "If it helps, give yourself one short pause before you react or decide what comes next.",
        }
    return templates.get(suggestion_family)


def build_follow_up_question(
    *,
    response_mode: str,
    language: str,
    render_context: dict[str, object] | None = None,
    normalized_state: dict[str, object] | None = None,
    support_strategy: dict[str, object] | None = None,
) -> str | None:
    context = render_context or {}
    state = normalized_state or {}
    user_stance = str(context.get("user_stance") or state.get("user_stance") or "")
    event_type = str(context.get("event_type") or state.get("event_type") or "")
    concern_target = str(context.get("concern_target") or state.get("concern_target") or "")
    relationship_role = str(context.get("relationship_role") or state.get("relationship_role") or "")
    evidence_spans = [str(item) for item in context.get("evidence_spans") or state.get("evidence_spans") or []]
    joined_evidence = " ".join(evidence_spans).casefold()

    if user_stance == "worried_about_other" or event_type in {"other_person_distress", "loved_one_unwell"}:
        if concern_target in {"friend", "sister", "brother", "mom", "mother", "dad", "father"}:
            return (
                "Điều gì đang làm bạn lo nhất cho họ lúc này?"
                if language == "vi"
                else "What are you most worried about here?"
            )
        if concern_target in {"crush", "partner", "girlfriend", "boyfriend", "wife", "husband"} or relationship_role == "named_person":
            return (
                "Phần nào của chuyện này vẫn còn ở lại với bạn nhiều nhất?"
                if language == "vi"
                else "What part of this is staying with you most?"
            )
        return (
            "Lúc này điều gì đang nặng nhất với bạn ở chuyện này?"
            if language == "vi"
            else "What feels heaviest here for you?"
        )
    if user_stance == "guilty_toward_other" or event_type == "responsibility_tension":
        return (
            "Phần nào của chuyện này vẫn còn nằm trong đầu bạn?"
            if language == "vi"
            else "What part of this is staying with you most?"
        )
    if response_mode == "stress_supportive":
        if "keep up" in joined_evidence or "pressure" in joined_evidence:
            return (
                "Lúc này nặng hơn ở áp lực đó, hay ở cảm giác mình đang hụt lại?"
                if language == "vi"
                else "Is it the pressure itself, or the feeling of falling behind?"
            )
        return (
            "Lúc này điều gì đang nặng nhất?"
            if language == "vi"
            else "What feels heaviest right now?"
        )
    if response_mode == "validating_gentle":
        return (
            "Phần nào của chuyện này vẫn còn vướng ở bạn?"
            if language == "vi"
            else "What part of this still stings most?"
        )
    if response_mode == "supportive_reflective":
        return (
            "Nếu muốn, phần nào thấy khó nói nhất?"
            if language == "vi"
            else "What feels hardest to say out loud?"
        )
    return None
