from __future__ import annotations

import json
import logging

from app.core.config import get_settings
from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError

logger = logging.getLogger(__name__)

RENDER_RESPONSE_SCHEMA: dict[str, object] = {
    "type": "OBJECT",
    "properties": {
        "empathetic_text": {"type": "STRING", "nullable": True},
        "follow_up_question": {"type": "STRING", "nullable": True},
        "suggestion_text": {"type": "STRING", "nullable": True},
        "quote_text": {"type": "STRING", "nullable": True},
        "composed_text": {"type": "STRING"},
    },
    "required": [
        "empathetic_text",
        "follow_up_question",
        "suggestion_text",
        "quote_text",
        "composed_text",
    ],
}


def resolve_render_language(emotion_analysis: dict[str, object]) -> str:
    settings = get_settings()
    detected_language = str(emotion_analysis.get("language", "")).strip().lower()
    if detected_language in {"vi"}:
        return detected_language
    return settings.response_default_language


def build_render_messages(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    topic_tags: list[str],
    response_plan: dict[str, object],
    memory_summary: dict[str, object] | None = None,
) -> tuple[str, str]:
    render_language = resolve_render_language(emotion_analysis)
    system_prompt = (
        "You are a supportive emotional companion, not a therapist.\n"
        "Help the user feel heard.\n"
        "Use the provided structured inputs as the source of truth.\n"
        "Reflect only the emotional tone provided in structured inputs.\n"
        "Do not introduce specific events, outcomes, arguments, conflict, failures, or missed deadlines unless they are explicitly stated in the transcript.\n"
        "Treat deadline_pressure and similar context as abstract pressure only, not as proof that any deadline was missed.\n"
        "Use transcript-safe wording such as pressure, things piling up, overwhelm, frustration, or difficulty settling when the transcript supports them.\n"
        "Do not diagnose mental health conditions.\n"
        "Do not make clinical claims.\n"
        "Do not contradict emotion_analysis.\n"
        "Do not invent emotions or state.\n"
        "Keep wording at the same level of certainty as the transcript and structured inputs.\n"
        "Prefer safe, abstract emotional language unless the transcript explicitly contains more concrete detail.\n"
        "Do not override planner decisions, emotion labels, or response variant.\n"
        "The selected response_variant must control which components are present.\n"
        "If response_variant is empathy_only, return only empathetic_text and leave the others null.\n"
        "If response_variant is empathy_plus_suggestion, return empathetic_text plus suggestion_text only.\n"
        "If response_variant is empathy_plus_followup, return empathetic_text plus follow_up_question only.\n"
        "If response_variant is empathy_plus_quote, return empathetic_text plus quote_text only.\n"
        "Use suggestion_family as a general strategy class, not as a cue to invent a concrete story.\n"
        "If suggestion_allowed is false, suggestion_text must be null.\n"
        "If follow_up_question_allowed is false, follow_up_question must be null.\n"
        "If quote_allowed is false, quote_text must be null.\n"
        "Use English by default.\n"
        "Return valid JSON only."
    )
    user_payload = {
        "default_language": render_language,
        "transcript": transcript,
        "emotion_analysis": {
            "primary_label": emotion_analysis.get("primary_label"),
            "secondary_labels": emotion_analysis.get("secondary_labels", []),
            "all_labels": emotion_analysis.get("all_labels", []),
            "scores": emotion_analysis.get("scores", {}),
            "confidence": emotion_analysis.get("confidence"),
            "response_mode": emotion_analysis.get("response_mode"),
            "dominant_signals": emotion_analysis.get("dominant_signals", []),
            "context_tags": emotion_analysis.get("context_tags", []),
        },
        "risk_level": "low",
        "topic_tags": topic_tags,
        "response_plan": {
            "opening_style": response_plan.get("opening_style"),
            "acknowledgment_focus": response_plan.get("acknowledgment_focus"),
            "suggestion_allowed": response_plan.get("suggestion_allowed"),
            "suggestion_style": response_plan.get("suggestion_style"),
            "quote_allowed": response_plan.get("quote_allowed"),
            "avoid_advice": response_plan.get("avoid_advice"),
            "tone": response_plan.get("tone"),
            "max_sentences": response_plan.get("max_sentences"),
            "follow_up_question_allowed": response_plan.get("follow_up_question_allowed"),
            "suggestion_family": response_plan.get("suggestion_family"),
            "response_variant": response_plan.get("response_variant"),
            "response_mode": response_plan.get("response_mode"),
            "evidence_bound": response_plan.get("evidence_bound", True),
        },
        "memory_summary": memory_summary or {},
    }
    return system_prompt, json.dumps(user_payload, ensure_ascii=False)


class GeminiRenderService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_enabled:
            raise ProviderConfigurationError("Gemini renderer is disabled")
        if not settings.gemini_api_key:
            raise ProviderConfigurationError("Response provider 'gemini' requires GEMINI_API_KEY")
        try:
            from google import genai
        except ImportError as exc:
            raise ProviderConfigurationError(
                "Response provider 'gemini' requires the 'google-genai' package to be installed"
            ) from exc
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_text_model
        self._structured_output = settings.response_use_structured_output

    def render(
        self,
        *,
        transcript: str,
        emotion_analysis: dict[str, object],
        topic_tags: list[str],
        response_plan: dict[str, object],
        memory_summary: dict[str, object] | None = None,
    ) -> dict[str, object]:
        system_prompt, user_prompt = build_render_messages(
            transcript=transcript,
            emotion_analysis=emotion_analysis,
            topic_tags=topic_tags,
            response_plan=response_plan,
            memory_summary=memory_summary,
        )
        generation_config: dict[str, object] = {
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "system_instruction": system_prompt,
        }
        if self._structured_output:
            generation_config["response_schema"] = RENDER_RESPONSE_SCHEMA
        logger.info(
            "gemini_render.start model=%s language=%s response_variant=%s response_mode=%s structured_output=%s",
            self._model,
            resolve_render_language(emotion_analysis),
            response_plan.get("response_variant"),
            response_plan.get("response_mode"),
            self._structured_output,
        )
        try:
            result = self._client.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=generation_config,
            )
        except Exception as exc:
            logger.exception(
                "gemini_render.failed model=%s language=%s response_variant=%s",
                self._model,
                resolve_render_language(emotion_analysis),
                response_plan.get("response_variant"),
            )
            raise ProviderExecutionError(f"Gemini response rendering failed: {exc}") from exc
        output_text = getattr(result, "text", None)
        if not output_text:
            raise ProviderExecutionError("Gemini response rendering returned empty text")
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ProviderExecutionError("Gemini response rendering returned invalid JSON") from exc
        logger.info(
            "gemini_render.complete model=%s language=%s response_variant=%s chars=%s",
            self._model,
            resolve_render_language(emotion_analysis),
            response_plan.get("response_variant"),
            len(output_text),
        )
        return {
            "payload": payload,
            "raw_renderer_output": output_text,
            "debug": {
                "renderer_selected": "gemini",
                "gemini_call_attempted": True,
                "gemini_call_succeeded": True,
                "gemini_parse_succeeded": True,
                "gemini_validation_succeeded": True,
                "render_language": resolve_render_language(emotion_analysis),
                "response_plan": response_plan,
            },
        }
