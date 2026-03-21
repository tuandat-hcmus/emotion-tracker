from __future__ import annotations

from app.core.config import get_settings
from app.services.gemini_render_service import build_render_messages, resolve_render_language
from app.services.response_provider_service import (
    MockResponseGeneratorProvider,
    ResponseGeneratorProvider,
    get_response_generator_provider_from_settings,
    get_response_provider_name_from_settings,
)
from app.services.response_rendering_service import build_safe_support_payload, build_standard_support_payload
from app.services.safety_service import should_use_standard_support_rendering


def build_gemini_render_debug_bundle(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    topic_tags: list[str],
    response_plan: dict[str, object],
    memory_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    system_prompt, final_prompt = build_render_messages(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        response_plan=response_plan,
        memory_summary=memory_summary,
    )
    return {
        "language": resolve_render_language(emotion_analysis),
        "system_prompt": system_prompt,
        "final_prompt": final_prompt,
        "response_plan": response_plan,
    }


def get_response_generator_provider(provider_name: str | None = None) -> ResponseGeneratorProvider:
    settings = get_settings()
    return get_response_generator_provider_from_settings(settings, provider_name)


def get_response_provider_name(provider_name: str | None = None) -> str:
    settings = get_settings()
    return get_response_provider_name_from_settings(settings, provider_name)


def render_supportive_response(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    topic_tags: list[str],
    risk_level: str,
    response_plan: dict[str, object],
    user_id: str,
    quote_opt_in: bool = True,
    provider_override: str | None = None,
    memory_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    if not should_use_standard_support_rendering(risk_level):
        return build_safe_support_payload(
            transcript=transcript,
            emotion_analysis=emotion_analysis,
            risk_level=risk_level,
            response_plan=response_plan,
        )

    provider = get_response_generator_provider(provider_override)
    provider_payload = provider.generate(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        response_plan=response_plan,
        memory_summary=memory_summary,
    )
    return build_standard_support_payload(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        risk_level=risk_level,
        response_plan=response_plan,
        user_id=user_id,
        quote_opt_in=quote_opt_in,
        provider_payload=provider_payload,
        provider_name=get_response_provider_name(provider_override),
    )


def generate_supportive_response(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    topic_tags: list[str],
    risk_level: str,
    response_plan: dict[str, object],
    user_id: str,
    quote_opt_in: bool = True,
    memory_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    payload = render_supportive_response(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        response_plan=response_plan,
        user_id=user_id,
        quote_opt_in=quote_opt_in,
        memory_summary=memory_summary,
    )
    return {
        "empathetic_response": str(payload["empathetic_response"]),
        "follow_up_question": payload["follow_up_question"],
        "gentle_suggestion": payload["gentle_suggestion"],
        "quote": payload["quote"],
        "ai_response": str(payload["ai_response"]),
    }


def generate_empathetic_response(
    transcript: str,
    emotion_label: str,
    topic_tags: list[str],
) -> str:
    payload = MockResponseGeneratorProvider().generate(
        transcript=transcript,
        emotion_analysis={
            "primary_label": emotion_label,
            "response_mode": "supportive_reflective",
            "stress_score": 0.0,
            "language": get_settings().response_default_language,
        },
        topic_tags=topic_tags,
        response_plan={
            "suggestion_allowed": False,
            "suggestion_style": "none",
            "quote_allowed": False,
            "avoid_advice": True,
            "follow_up_question_allowed": False,
        },
        memory_summary=None,
    )
    return str(dict(payload["payload"]).get("empathetic_text", ""))
