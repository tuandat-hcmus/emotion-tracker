from __future__ import annotations

import hashlib
from typing import Any, Protocol

from app.services.gemini_render_service import GeminiRenderService, resolve_render_language
from app.services.provider_errors import ProviderConfigurationError
from app.services.response_policy_service import build_follow_up_question, build_suggestion_text


class ResponseGeneratorProvider(Protocol):
    def generate(
        self,
        *,
        transcript: str,
        emotion_analysis: dict[str, object],
        topic_tags: list[str],
        response_plan: dict[str, object],
        memory_summary: dict[str, object] | None = None,
    ) -> dict[str, object]:
        ...


def has_signal(emotion_analysis: dict[str, object], signal: str) -> bool:
    return signal in {str(item) for item in emotion_analysis.get("dominant_signals", [])}


def _pick(options: list[str], seed: str) -> str:
    """Deterministically pick from options using a hash seed for variety."""
    index = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(options)
    return options[index]


# --- Response pools for variety ---

_GREETING_RESPONSES = [
    "Hey, I'm here with you.",
    "Hi — take your time. No rush.",
    "Welcome back. I'm listening whenever you're ready.",
    "I'm glad you're here.",
]

_CELEBRATORY_RESPONSES = [
    "That sounds lighter, and in a good way.",
    "That sounds like a real exhale. Hold onto that feeling.",
    "Something shifted in a good direction — I can hear it.",
    "That's worth pausing on. It sounds genuinely good.",
]

_LOW_ENERGY_RESPONSES = [
    "That sounds quietly exhausting. You don't have to push through it right now.",
    "Low-energy days are real. You don't owe anyone brightness today.",
    "Sometimes the heaviest days look ordinary from the outside. This one sounds heavy.",
    "It sounds like you're running on fumes. That's hard.",
]

_GROUNDING_RESPONSES = [
    "That sounds like a lot to carry right now.",
    "There's a lot here, and you don't have to sort through all of it at once.",
    "It makes sense that this feels overwhelming — there's weight in what you're describing.",
    "When everything piles up like this, even small things start to feel heavy.",
]

_STRESS_RESPONSES = [
    "That sounds like a lot of pressure to carry.",
    "When pressure builds this fast, it's hard to think straight. That's completely normal.",
    "The pace you're describing would wear anyone down.",
    "That kind of pressure is exhausting even before you start solving it.",
]

_VALIDATION_RESPONSES = [
    "It makes sense that this is still with you.",
    "What you're feeling has real reasons behind it.",
    "You don't need to explain why this matters — it clearly does.",
    "Your feelings make sense here, even if they're complicated.",
]

_SADNESS_RESPONSES = [
    "There's real sadness in what you're sharing. I hear it.",
    "That kind of ache doesn't need a fix right now — just acknowledgment.",
    "It sounds like this goes deeper than just a bad day.",
    "Some sadness just needs space to exist for a while.",
]

_LONELINESS_RESPONSES = [
    "Loneliness can be sharp, especially when surrounded by people.",
    "Feeling disconnected like that is genuinely painful.",
    "That kind of quiet isolation is harder than most people realize.",
    "You're not strange for feeling alone in this. It's a real feeling.",
]

_ANXIETY_RESPONSES = [
    "That sounds like your mind has been spinning on this.",
    "Anxiety can make everything feel urgent, even things that can wait.",
    "When worry takes the wheel, even rest feels impossible.",
    "It sounds like there's a background hum of worry pulling at you.",
]

_GENERAL_RESPONSES = [
    "That seems to be sitting with you.",
    "I hear something in this that matters to you.",
    "There's more underneath what you just shared, isn't there?",
    "Thank you for putting that into words. It's not always easy.",
    "What you're describing sounds genuinely significant to you.",
]

_REFLECTIVE_RESPONSES = [
    "That seems to have stayed with you for a reason.",
    "Something about this keeps pulling your attention back.",
    "It sounds like you're still processing this — and that's okay.",
    "Reflection like this takes courage, even if it doesn't feel like it.",
]

_MISSING_RESPONSES = [
    "Missing someone can feel especially close at night.",
    "That kind of longing is a sign of how much they matter to you.",
    "The ache of missing someone is one of the most honest feelings there is.",
]

_GUILT_RESPONSES = [
    "This sounds like it has been sitting heavily with you.",
    "Guilt can be relentless, but the fact that you care this much says something.",
    "You're holding yourself accountable in a way that shows real empathy.",
]


class MockResponseGeneratorProvider:
    def generate(
        self,
        *,
        transcript: str,
        emotion_analysis: dict[str, object],
        topic_tags: list[str],
        response_plan: dict[str, object],
        memory_summary: dict[str, object] | None = None,
    ) -> dict[str, object]:
        primary_topic = topic_tags[0] if topic_tags else "daily life"
        lowered_transcript = transcript.casefold()
        language = str(emotion_analysis.get("language", "en")).strip().lower()
        response_mode = str(emotion_analysis["response_mode"])
        primary_label = str(emotion_analysis.get("primary_label", "neutral"))
        suggestion_family = response_plan.get("suggestion_family")
        response_variant = str(response_plan.get("response_variant", "empathy_only"))
        render_context = dict(response_plan.get("render_context", {}))
        support_strategy = dict(response_plan.get("support_strategy", {}))
        user_stance = str(render_context.get("user_stance", ""))
        concern_target = str(render_context.get("concern_target") or "")
        relationship_role = str(render_context.get("relationship_role") or "")
        event_type = str(render_context.get("event_type") or "")
        other_person_emotion_word = str(render_context.get("other_person_emotion_word") or "")
        response_goal = str(support_strategy.get("response_goal") or "")
        low_energy_update = bool(render_context.get("low_energy_update"))
        positive_personal_update = bool(render_context.get("positive_personal_update"))
        reflective_checkin = bool(render_context.get("reflective_checkin"))

        # Build a seed for deterministic variety based on transcript content
        seed = transcript.strip()[:80]

        # Check memory for conversation continuity
        memory_turns = 0
        if memory_summary:
            memory_turns = int(memory_summary.get("turn_count", 0) or 0)

        def _target_phrase() -> str:
            if concern_target and concern_target != "named_person":
                return f"your {concern_target}"
            if relationship_role == "named_person":
                return "them"
            return "someone you care about"

        def _other_person_reflection() -> str:
            target = _target_phrase()
            observed = other_person_emotion_word or "off"
            options = [
                f"Seeing {target} seem {observed} can sit heavily with you.",
                f"It sounds like you're carrying some of what {target} is going through.",
                f"Worrying about {target} while managing your own feelings is a lot.",
            ]
            if concern_target == "friend":
                options.append("Seeing your friend struggle like this can really stay with you.")
            return _pick(options, seed)

        if language == "vi":
            primary_topic = topic_tags[0] if topic_tags else "đời sống hằng ngày"
            if response_mode == "celebratory_warm":
                empathetic_text = (
                    f"Có một sự ấm lại rất rõ trong điều bạn vừa kể về {primary_topic}. "
                    "Khoảnh khắc này xứng đáng được ghi nhận."
                )
            elif response_mode == "low_energy_comfort":
                empathetic_text = (
                    f"Nghe như năng lượng của bạn đang xuống thấp quanh chuyện {primary_topic}. "
                    "Mình ghi nhận sự mệt đó mà không ép bạn phải gượng lên ngay."
                )
            elif response_mode == "grounding_soft":
                empathetic_text = (
                    f"Có vẻ áp lực quanh chuyện {primary_topic} đang dồn lên khá nhiều. "
                    "Mình ở đây để cùng bạn giữ nhịp lại một chút."
                )
            elif response_mode == "stress_supportive":
                empathetic_text = (
                    f"Nghe như áp lực quanh chuyện {primary_topic} đang chồng lên nhau rất nhanh. "
                    "Khi mọi thứ cứ dồn dập như vậy, cảm giác không theo kịp thực sự rất mệt."
                )
            elif response_mode == "validating_gentle":
                empathetic_text = (
                    f"Mình nghe thấy phần nặng trong điều bạn vừa kể về {primary_topic}. "
                    "Cảm giác đó có lý do để tồn tại."
                )
            else:
                empathetic_text = (
                    f"Trong điều bạn vừa chia sẻ về {primary_topic}, có nhiều lớp cảm xúc đang đi cùng nhau. "
                    "Mình ghi nhận cả phần rõ ràng lẫn phần còn lẫn lộn đó."
                )

            suggestion_text = build_suggestion_text(
                suggestion_family=str(suggestion_family) if suggestion_family is not None else None,
                language="vi",
                render_context=render_context,
                support_strategy=support_strategy,
            )
            follow_up_question = build_follow_up_question(
                response_mode=response_mode,
                language="vi",
                render_context=render_context,
                support_strategy=support_strategy,
            )
            if response_variant == "empathy_only":
                suggestion_text = None
                follow_up_question = None
            elif response_variant == "empathy_plus_suggestion":
                follow_up_question = None
            elif response_variant == "empathy_plus_followup":
                suggestion_text = None
            elif response_variant == "empathy_plus_quote":
                suggestion_text = None
                follow_up_question = None
            return {
                "payload": {
                    "empathetic_text": empathetic_text,
                    "follow_up_question": follow_up_question,
                    "suggestion_text": suggestion_text,
                    "quote_text": None,
                    "composed_text": "",
                },
                "raw_renderer_output": None,
                "debug": {"renderer_selected": "mock", "render_language": "vi"},
            }

        # --- English responses with variety ---

        if event_type == "greeting_or_opening":
            empathetic_text = _pick(_GREETING_RESPONSES, seed)
        elif user_stance == "worried_about_other":
            empathetic_text = _other_person_reflection()
        elif user_stance == "guilty_toward_other":
            empathetic_text = _pick(_GUILT_RESPONSES, seed)
        elif response_goal == "reinforce_positive_moment" and response_mode == "celebratory_warm":
            empathetic_text = _pick(_CELEBRATORY_RESPONSES, seed)
        elif response_mode == "celebratory_warm":
            empathetic_text = _pick(_CELEBRATORY_RESPONSES, seed)
        elif response_mode == "low_energy_comfort":
            empathetic_text = _pick(_LOW_ENERGY_RESPONSES, seed)
        elif response_mode == "grounding_soft":
            empathetic_text = _pick(_GROUNDING_RESPONSES, seed)
        elif response_mode == "stress_supportive":
            empathetic_text = _pick(_STRESS_RESPONSES, seed)
        elif response_mode == "validating_gentle":
            empathetic_text = _pick(_VALIDATION_RESPONSES, seed)
        else:
            # Emotion-aware selection
            if primary_label in ("sadness", "sad"):
                empathetic_text = _pick(_SADNESS_RESPONSES, seed)
            elif primary_label in ("loneliness", "lonely"):
                empathetic_text = _pick(_LONELINESS_RESPONSES, seed)
            elif primary_label in ("anxiety", "anxious", "fear"):
                empathetic_text = _pick(_ANXIETY_RESPONSES, seed)
            elif "miss " in lowered_transcript:
                empathetic_text = _pick(_MISSING_RESPONSES, seed)
            elif reflective_checkin:
                empathetic_text = _pick(_REFLECTIVE_RESPONSES, seed)
            elif positive_personal_update:
                empathetic_text = _pick(_CELEBRATORY_RESPONSES, seed)
            elif low_energy_update or event_type == "exhaustion_or_flatness":
                empathetic_text = _pick(_LOW_ENERGY_RESPONSES, seed)
            else:
                empathetic_text = _pick(_GENERAL_RESPONSES, seed)

            if has_signal(emotion_analysis, "positive_affect"):
                empathetic_text = _pick(_CELEBRATORY_RESPONSES, seed)

        # Add continuity for multi-turn conversations
        if memory_turns > 1:
            continuity_prefix = _pick([
                "Staying with what you shared — ",
                "Building on that — ",
                "Hearing you further — ",
            ], seed + str(memory_turns))
            empathetic_text = continuity_prefix.lower() + empathetic_text[0].lower() + empathetic_text[1:]

        suggestion_text = build_suggestion_text(
            suggestion_family=str(suggestion_family) if suggestion_family is not None else None,
            language="en",
            render_context=render_context,
            support_strategy=support_strategy,
        )
        follow_up_question = build_follow_up_question(
            response_mode=response_mode,
            language="en",
            render_context=render_context,
            support_strategy=support_strategy,
        )
        if response_variant == "empathy_only":
            suggestion_text = None
            follow_up_question = None
        elif response_variant == "empathy_plus_suggestion":
            follow_up_question = None
        elif response_variant == "empathy_plus_followup":
            suggestion_text = None
        elif response_variant == "empathy_plus_quote":
            suggestion_text = None
            follow_up_question = None

        return {
            "payload": {
                "empathetic_text": empathetic_text,
                "follow_up_question": follow_up_question,
                "suggestion_text": suggestion_text,
                "quote_text": None,
                "composed_text": "",
            },
            "raw_renderer_output": None,
            "debug": {"renderer_selected": "mock", "render_language": resolve_render_language(emotion_analysis)},
        }


class GeminiResponseGeneratorProvider:
    def __init__(self) -> None:
        self._service = GeminiRenderService()

    def generate(
        self,
        *,
        transcript: str,
        emotion_analysis: dict[str, object],
        topic_tags: list[str],
        response_plan: dict[str, object],
        memory_summary: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return self._service.render(
            transcript=transcript,
            emotion_analysis=emotion_analysis,
            topic_tags=topic_tags,
            response_plan=response_plan,
            memory_summary=memory_summary,
        )


def get_response_generator_provider_from_settings(
    settings: Any,
    provider_name: str | None = None,
) -> ResponseGeneratorProvider:
    selected_provider = (provider_name or settings.response_provider).strip().casefold()

    if selected_provider == "gemini":
        return GeminiResponseGeneratorProvider()
    if settings.use_mock_response or selected_provider == "mock":
        return MockResponseGeneratorProvider()
    raise ProviderConfigurationError(f"Unsupported response provider: {selected_provider}")


def get_response_provider_name_from_settings(
    settings: Any,
    provider_name: str | None = None,
) -> str:
    selected_provider = (provider_name or settings.response_provider).strip().casefold()
    if selected_provider == "gemini":
        return "gemini"
    if settings.use_mock_response or selected_provider == "mock":
        return "mock"
    return selected_provider
