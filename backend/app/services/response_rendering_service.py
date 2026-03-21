from __future__ import annotations

from app.core.config import get_settings
from app.schemas.me import QuoteResponse
from app.services.quote_service import select_quote
from app.services.response_postcheck_service import postcheck_rendered_response
from app.services.safety_service import generate_safe_support_message


def compose_response(
    *,
    empathetic_text: str,
    follow_up_question: str | None,
    suggestion_text: str | None,
    quote: QuoteResponse | None,
) -> str:
    parts = [empathetic_text]
    if suggestion_text:
        parts.append(suggestion_text)
    if follow_up_question:
        parts.append(follow_up_question)
    if quote:
        parts.append(quote.short_text)
    return " ".join(part.strip() for part in parts if part and part.strip())


def build_safe_support_payload(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    risk_level: str,
    response_plan: dict[str, object],
) -> dict[str, object]:
    settings = get_settings()
    empathetic_text = generate_safe_support_message(
        risk_level,
        language=str(emotion_analysis.get("language", getattr(settings, "response_default_language", "en"))),
    )
    repaired = postcheck_rendered_response(
        rendered={
            "empathetic_text": empathetic_text,
            "follow_up_question": None,
            "suggestion_text": None,
            "quote_text": None,
            "composed_text": empathetic_text,
        },
        response_plan=response_plan,
        fallback_empathetic_text=empathetic_text,
        quote_text=None,
        transcript=transcript,
        language=str(emotion_analysis.get("language", getattr(settings, "response_default_language", "en"))),
    )
    return {
        "empathetic_response": repaired["empathetic_text"],
        "follow_up_question": repaired["follow_up_question"],
        "gentle_suggestion": repaired["suggestion_text"],
        "quote": None,
        "ai_response": repaired["composed_text"],
        "provider_name": "safety_template",
        "raw_renderer_output": None,
        "debug": {
            "renderer_selected": "safety_template",
            "fallback_triggered": True,
            "fallback_reason": "risk_level_requires_safe_template",
        },
    }


def build_standard_support_payload(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    risk_level: str,
    response_plan: dict[str, object],
    user_id: str,
    quote_opt_in: bool,
    provider_payload: dict[str, object],
    provider_name: str,
) -> dict[str, object]:
    quote = None
    if bool(response_plan.get("quote_allowed")):
        quote = select_quote(
            quote_opt_in=quote_opt_in,
            latest_emotion_label=str(emotion_analysis["primary_label"]),
            latest_risk_level=risk_level,
            user_id=user_id,
        )
    repaired = postcheck_rendered_response(
        rendered=dict(provider_payload.get("payload", {})),
        response_plan=response_plan,
        fallback_empathetic_text=str(dict(provider_payload.get("payload", {})).get("empathetic_text") or ""),
        quote_text=quote.short_text if quote is not None else None,
        transcript=transcript,
        language=str(emotion_analysis.get("language", "en")),
    )
    return {
        "empathetic_response": repaired["empathetic_text"],
        "follow_up_question": repaired["follow_up_question"],
        "gentle_suggestion": repaired["suggestion_text"],
        "quote": quote,
        "ai_response": compose_response(
            empathetic_text=repaired["empathetic_text"],
            follow_up_question=repaired["follow_up_question"],
            suggestion_text=repaired["suggestion_text"],
            quote=quote,
        ),
        "provider_name": provider_name,
        "raw_renderer_output": provider_payload.get("raw_renderer_output"),
        "debug": provider_payload.get("debug"),
    }
