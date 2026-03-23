from __future__ import annotations

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
        del transcript
        del memory_summary
        primary_topic = topic_tags[0] if topic_tags else "daily life"
        language = str(emotion_analysis.get("language", "en")).strip().lower()
        response_mode = str(emotion_analysis["response_mode"])
        acknowledgment_focus = str(response_plan.get("acknowledgment_focus", "mixed_state"))
        suggestion_family = response_plan.get("suggestion_family")
        response_variant = str(response_plan.get("response_variant", "empathy_only"))
        render_context = dict(response_plan.get("render_context", {}))
        support_strategy = dict(response_plan.get("support_strategy", {}))
        user_stance = str(render_context.get("user_stance", ""))
        concern_target = str(render_context.get("concern_target") or "")
        response_goal = str(support_strategy.get("response_goal") or "")

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
                    "Khi mọi thứ cứ dồn dập như vậy, cảm giác không theo kịp thực sự rất mệt và khó gánh."
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

        if user_stance == "worried_about_other":
            target = (
                f"your {concern_target}"
                if concern_target and concern_target != "named_person"
                else "someone you care about"
            )
            empathetic_text = (
                f"It can be hard to see {target} seem that weighed down. "
                "It makes sense if part of you feels worried and a little unsure what to do next."
            )
        elif user_stance == "guilty_toward_other":
            empathetic_text = (
                "It sounds like this is staying with you because you care and you wish it had gone differently. "
                "That can feel heavy to carry on your own."
            )
        elif response_goal == "reinforce_positive_moment" and response_mode == "celebratory_warm":
            empathetic_text = (
                f"That sounds like a real moment of relief around {primary_topic}. "
                "It makes sense if part of you wants to stay with that for a second."
            )
        elif response_mode == "celebratory_warm":
            empathetic_text = (
                f"I can hear a steadier, warmer note in what you shared about {primary_topic}. "
                "That shift sounds real, and it deserves to be noticed."
            )
        elif response_mode == "low_energy_comfort":
            empathetic_text = (
                f"It sounds like your energy is running low around {primary_topic}. "
                "I want to acknowledge that tiredness without pushing you to feel different right away."
            )
        elif response_mode == "grounding_soft":
            empathetic_text = (
                f"It sounds like the pressure around {primary_topic} is landing hard right now. "
                "You do not need to force yourself to be okay immediately."
            )
        elif response_mode == "stress_supportive":
            empathetic_text = (
                f"It sounds like the pressure around {primary_topic} is stacking faster than you can recover from it. "
                "When deadlines keep piling up, the feeling of not catching up can get exhausting very quickly."
            )
        elif response_mode == "validating_gentle":
            empathetic_text = (
                f"There is a lot of strain in what you shared about {primary_topic}. "
                "That reaction makes sense and does not need to be dismissed."
            )
        else:
            empathetic_text = (
                f"There are a few emotional layers moving together in what you shared about {primary_topic}. "
                "Nothing about that needs to be simplified too quickly."
            )
            if has_signal(emotion_analysis, "positive_affect") and acknowledgment_focus == "emotion_complexity":
                empathetic_text = (
                    f"There is something a little lighter in what you shared about {primary_topic}, even if it still has layers. "
                    "That steadier part deserves some room too."
                )

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
