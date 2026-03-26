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
        del memory_summary
        primary_topic = topic_tags[0] if topic_tags else "daily life"
        lowered_transcript = transcript.casefold()
        language = str(emotion_analysis.get("language", "en")).strip().lower()
        response_mode = str(emotion_analysis["response_mode"])
        acknowledgment_focus = str(response_plan.get("acknowledgment_focus", "mixed_state"))
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
        short_personal_update = bool(render_context.get("short_personal_update"))
        reflective_checkin = bool(render_context.get("reflective_checkin"))
        low_energy_update = bool(render_context.get("low_energy_update"))
        positive_personal_update = bool(render_context.get("positive_personal_update"))

        def _target_phrase() -> str:
            if concern_target and concern_target != "named_person":
                return f"your {concern_target}"
            if relationship_role == "named_person":
                return "them"
            return "someone you care about"

        def _other_person_reflection() -> str:
            target = _target_phrase()
            if concern_target == "friend":
                return "Seeing your friend seem this down can really stay with you."
            if concern_target in {"crush", "partner", "girlfriend", "boyfriend", "wife", "husband"}:
                observed = other_person_emotion_word or "off"
                return f"It can feel unsettling when {target} seems {observed}."
            observed = other_person_emotion_word or "off"
            return f"Seeing {target} seem {observed} can sit heavily with you."

        def _stress_reflection() -> str:
            if "can't keep up" in lowered_transcript or "cannot keep up" in lowered_transcript:
                return "Feeling like you can't keep up can get exhausting fast."
            if "deadline" in lowered_transcript:
                return "That deadline pressure sounds heavy."
            return "That sounds like a lot of pressure to carry."

        def _supportive_reflection() -> str:
            if "check in" in lowered_transcript:
                return "I'm glad you checked in."
            if "nothing big happened" in lowered_transcript or "ordinary" in lowered_transcript or "normal day" in lowered_transcript:
                return "A quieter day still counts."
            if "miss " in lowered_transcript:
                return "Missing someone can feel especially close at night."
            if "should have" in lowered_transcript or "wish i could take it back" in lowered_transcript:
                return "That seems to be lingering with you."
            if "lighter than yesterday" in lowered_transcript or "a little easier" in lowered_transcript:
                return "It sounds a little lighter today."
            if "not as stuck" in lowered_transcript:
                return "Even a small shift away from stuck can matter."
            if "calmer" in lowered_transcript:
                return "It sounds a little steadier right now."
            if "interrupt" in lowered_transcript or "annoyed" in lowered_transcript:
                return "That would wear on you."
            if low_energy_update or event_type == "exhaustion_or_flatness":
                if "empty" in lowered_transcript or "flat" in lowered_transcript:
                    return "That sounds flat and draining."
                return "That sounds like a low-energy kind of day."
            if positive_personal_update:
                return "There is something a little lighter in this."
            if reflective_checkin:
                return "That seems to have stayed with you."
            if short_personal_update:
                return "I'm here with you."
            return "That seems to be sitting with you."

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

        if event_type == "greeting_or_opening":
            empathetic_text = "Hey, I'm here with you."
        elif user_stance == "worried_about_other":
            empathetic_text = _other_person_reflection()
        elif user_stance == "guilty_toward_other":
            empathetic_text = (
                "This sounds like it has been sitting heavily with you."
            )
        elif response_goal == "reinforce_positive_moment" and response_mode == "celebratory_warm":
            empathetic_text = (
                "That sounds like a real exhale."
            )
        elif response_mode == "celebratory_warm":
            empathetic_text = (
                "That sounds lighter, and in a good way."
            )
        elif response_mode == "low_energy_comfort":
            empathetic_text = (
                "That sounds quietly exhausting."
            )
        elif response_mode == "grounding_soft":
            empathetic_text = (
                "That sounds like a lot to carry right now."
            )
        elif response_mode == "stress_supportive":
            empathetic_text = _stress_reflection()
        elif response_mode == "validating_gentle":
            empathetic_text = (
                "It makes sense that this is still with you."
            )
        else:
            empathetic_text = _supportive_reflection()
            if has_signal(emotion_analysis, "positive_affect") and acknowledgment_focus == "emotion_complexity":
                empathetic_text = (
                    "There is something a little lighter in this too."
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
