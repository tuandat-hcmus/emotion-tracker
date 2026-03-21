from __future__ import annotations


def select_suggestion_family(
    *,
    response_mode: str,
    dominant_signals: set[str],
    suggestion_allowed: bool,
) -> str | None:
    if not suggestion_allowed:
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
) -> str:
    if risk_level != "low":
        return "empathy_only"
    if quote_allowed and response_mode == "celebratory_warm":
        return "empathy_plus_quote"
    if follow_up_question_allowed and response_mode in {"stress_supportive", "supportive_reflective", "validating_gentle"}:
        return "empathy_plus_followup"
    if suggestion_allowed:
        return "empathy_plus_suggestion"
    return "empathy_only"


def build_suggestion_text(
    *,
    suggestion_family: str | None,
    language: str,
) -> str | None:
    if suggestion_family is None:
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
) -> str | None:
    if response_mode == "stress_supportive":
        return (
            "Lúc này điều nào đang nặng nhất: khối lượng công việc, độ gấp, hay cảm giác mình không theo kịp?"
            if language == "vi"
            else "What feels heaviest right now — the amount of work, the urgency, or the feeling of not catching up?"
        )
    if response_mode == "validating_gentle":
        return (
            "Phần nào của chuyện này đang làm bạn căng nhất lúc này?"
            if language == "vi"
            else "What part of this feels most charged right now?"
        )
    if response_mode == "supportive_reflective":
        return (
            "Phần nào của điều này đang cần được nói ra rõ hơn một chút?"
            if language == "vi"
            else "What part of this feels most worth naming out loud right now?"
        )
    return None
