import logging

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.demo import (
    DemoAICoreDetailsResponse,
    DemoAICoreResponse,
    DemoEmotionResponse,
    DemoInsightFeaturesResponse,
    DemoMemorySummaryResponse,
    DemoNormalizedStateResponse,
    DemoRenderDebugResponse,
    DemoSupportResponse,
    DemoSupportStrategyResponse,
    DemoWeeklyInsightResponse,
)
from app.services.ai_core.language_service import detect_language
from app.services.companion_core import (
    build_companion_pipeline,
    build_emotional_memory_record,
    build_weekly_insight,
    get_demo_memory_store,
)
from app.services.demo_support_service import build_demo_safety_context, ensure_demo_enabled, list_recent_demo_memory
from app.services.emotion_service import analyze_emotion, normalize_emotion_analysis
from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError
from app.services.response_service import build_gemini_render_debug_bundle, render_supportive_response
from app.services.safety_service import detect_safety_risk, generate_safe_support_message
from app.services.topic_service import tag_topics

logger = logging.getLogger(__name__)


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _build_public_debug_bundle(
    *,
    selected_provider: str,
    gemini_call_attempted: bool,
    gemini_call_succeeded: bool,
    fallback_used: bool,
    fallback_reason: str | None,
    error_stage: str | None,
    response_parse_status: str | None,
    validation_error_summary: str | None,
) -> dict[str, object]:
    return {
        "selected_provider": selected_provider,
        "gemini_call_attempted": gemini_call_attempted,
        "gemini_call_succeeded": gemini_call_succeeded,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "error_stage": error_stage,
        "response_parse_status": response_parse_status,
        "validation_error_summary": validation_error_summary,
    }


def _summarize_gemini_failure(exc: Exception) -> tuple[str, str | None, str | None, str | None]:
    message = str(exc)
    lowered = message.casefold()
    if isinstance(exc, ProviderConfigurationError):
        if "requires gemini_api_key" in lowered:
            return "missing_api_key", "provider_configuration", "not_attempted", None
        if "google-genai" in lowered:
            return "missing_sdk", "provider_configuration", "not_attempted", None
        return "provider_configuration_error", "provider_configuration", "not_attempted", None

    if "invalid json" in lowered:
        return "invalid_json", "response_parse", "invalid_json", "invalid_json_response"
    if "empty text" in lowered:
        return "empty_response", "provider_execution", "empty_response", None
    if "empty empathetic_response" in lowered:
        return "schema_validation_failed", "schema_validation", "parsed_json", "missing_empathetic_response"
    if "invalid style" in lowered:
        return "schema_validation_failed", "schema_validation", "parsed_json", "invalid_style"
    if "invalid specificity" in lowered:
        return "schema_validation_failed", "schema_validation", "parsed_json", "invalid_specificity"
    if "empty reasoning_note" in lowered:
        return "schema_validation_failed", "schema_validation", "parsed_json", "missing_reasoning_note"
    return "provider_execution_error", "provider_execution", "not_parsed", "execution_error"


def _apply_render_adjustments(
    text: str,
    emotion_analysis: dict[str, object],
    render_context,
) -> dict[str, object]:
    del text
    adjusted = dict(emotion_analysis)
    provider_name = str(adjusted.get("provider_name", "unknown"))
    source_metadata = dict(adjusted.get("source_metadata", {}))
    dominant_signals = [str(item) for item in adjusted.get("dominant_signals", [])]

    if render_context.event_type == "loved_one_unwell":
        adjusted["primary_emotion"] = "anxiety"
        adjusted["secondary_emotions"] = ["sadness", "neutral"]
        adjusted["emotion_label"] = "concerned"
        adjusted["label"] = "concerned"
        adjusted["valence_score"] = -0.24
        adjusted["energy_score"] = 0.34
        adjusted["stress_score"] = 0.44
        adjusted["confidence"] = min(max(float(adjusted.get("confidence", 0.45)), 0.44), 0.6)
        adjusted["response_mode"] = "supportive_reflective"
        adjusted["dominant_signals"] = _dedupe(["anxiety_activation", "connection_need", *dominant_signals])
        source_metadata["demo_adjustment"] = "loved_one_unwell"
    elif render_context.event_type == "recognition_or_praise":
        adjusted["primary_emotion"] = "gratitude"
        adjusted["secondary_emotions"] = ["joy", "neutral"]
        adjusted["emotion_label"] = "grateful"
        adjusted["label"] = "grateful"
        adjusted["valence_score"] = 0.42
        adjusted["energy_score"] = 0.46
        adjusted["stress_score"] = min(float(adjusted.get("stress_score", 0.3)), 0.24)
        adjusted["confidence"] = max(float(adjusted.get("confidence", 0.0)), 0.56)
        adjusted["response_mode"] = "celebratory_warm" if float(adjusted.get("confidence", 0.0)) >= 0.6 else "supportive_reflective"
        source_metadata["demo_adjustment"] = "recognition_or_praise"
    elif render_context.event_type == "relief_or_gratitude" and (
        render_context.positive_personal_update or render_context.appreciation_or_recognition
    ):
        adjusted["primary_emotion"] = "joy"
        adjusted["secondary_emotions"] = ["gratitude", "neutral"]
        adjusted["emotion_label"] = "bright"
        adjusted["label"] = "bright"
        adjusted["valence_score"] = max(float(adjusted.get("valence_score", 0.0)), 0.62)
        adjusted["energy_score"] = max(float(adjusted.get("energy_score", 0.0)), 0.52)
        adjusted["stress_score"] = min(float(adjusted.get("stress_score", 0.2)), 0.18)
        adjusted["confidence"] = max(float(adjusted.get("confidence", 0.0)), 0.62)
        adjusted["response_mode"] = "celebratory_warm"
        source_metadata["demo_adjustment"] = "positive_personal_update"
    elif render_context.event_type == "conflict_or_disappointment":
        adjusted["primary_emotion"] = "overwhelm"
        adjusted["secondary_emotions"] = ["anxiety", "sadness"]
        adjusted["emotion_label"] = "strained"
        adjusted["label"] = "strained"
        adjusted["valence_score"] = -0.38
        adjusted["energy_score"] = 0.5
        adjusted["stress_score"] = max(float(adjusted.get("stress_score", 0.0)), 0.56)
        adjusted["confidence"] = max(float(adjusted.get("confidence", 0.0)), 0.52)
        adjusted["response_mode"] = "validating_gentle"
        source_metadata["demo_adjustment"] = "responsibility_tension"
    elif render_context.event_type == "exhaustion_or_flatness":
        adjusted["response_mode"] = "low_energy_comfort"
        source_metadata["demo_adjustment"] = "low_energy_update"

    if render_context.other_person_state_mentioned and adjusted["primary_emotion"] in {"anger", "sadness"}:
        adjusted["primary_emotion"] = "anxiety"
        adjusted["secondary_emotions"] = ["sadness", "neutral"]
        adjusted["response_mode"] = "supportive_reflective"
        source_metadata["other_person_state_adjustment"] = True

    if source_metadata:
        adjusted["source_metadata"] = source_metadata
    if source_metadata.get("demo_adjustment") or source_metadata.get("other_person_state_adjustment"):
        adjusted["provider_name"] = f"{provider_name}+en_demo_render_adjustment"
    return adjusted


def _build_demo_response_text(
    *,
    text: str,
    emotion_analysis: dict[str, object],
    render_context,
    risk_level: str,
) -> tuple[str, str | None, str | None]:
    if risk_level in {"high", "medium"}:
        return (
            generate_safe_support_message(risk_level),
            None,
            "If you feel unsafe, please prioritize staying near someone you trust or reaching out for urgent local support.",
        )

    event_type = str(render_context.event_type)
    relationship_target = str(render_context.relationship_target or "someone close to you")
    target_phrase = f"your {relationship_target}" if relationship_target != "someone close to you" else relationship_target
    confidence = float(emotion_analysis["confidence"])
    low_confidence = confidence < 0.5

    if event_type == "loved_one_unwell":
        empathetic = (
            f"When {target_phrase} is unwell, even a short update can carry a lot of worry. "
            "It makes sense if part of your attention keeps circling back to them."
        )
        suggestion = "If it helps, pick one small check-in or one practical thing you can do and let that be enough for now."
    elif event_type == "recognition_or_praise":
        empathetic = (
            "Hearing that from someone you know can land in a real way. "
            "It makes sense if you are still taking in what those words meant to you."
        )
        suggestion = "If you want, keep the exact line that felt most real."
    elif event_type == "relief_or_gratitude":
        empathetic = (
            "That kind of news can make everything feel a little brighter all at once. "
            "You do not need to downplay a good moment for it to count."
        )
        suggestion = "If you want, you can let yourself enjoy this moment before trying to figure out anything else."
    elif event_type == "deadline_pressure":
        empathetic = (
            "Having deadlines pile up for days can make everything feel tight and crowded. "
            "You do not have to pretend it is manageable for it to count as a lot."
        )
        suggestion = "If it helps, choose the next smallest thing instead of the whole pile."
    elif event_type == "loneliness_or_disconnection":
        empathetic = (
            "Feeling left out can land in a quiet but heavy way. "
            "It makes sense that this would leave you feeling a bit far from everyone."
        )
        suggestion = "If it helps, one small reach-out still counts even if you do not have much energy for more."
    elif event_type == "conflict_or_disappointment":
        empathetic = (
            "It makes sense that this is sitting heavily after feeling like you let someone down. "
            "That kind of tension can linger even when the moment itself is over."
        )
        suggestion = "If it helps, one honest next step is enough for tonight."
    elif event_type == "exhaustion_or_flatness":
        empathetic = (
            "Being this tired can flatten everything a little. "
            "You do not need to force meaning or momentum out of a low-energy day."
        )
        suggestion = "If it helps, let the next thing be small and easy on purpose."
    else:
        empathetic = (
            "It makes sense if this feels hard to name cleanly. "
            "More than one feeling can be present without you needing to sort it all out right now."
        )
        suggestion = "If it helps, name the part that feels most immediate and leave the rest alone for now."

    if low_confidence and render_context.short_event_flag:
        empathetic = (
            f"Even from a short update like \"{text}\", it makes sense that something emotionally important is sitting underneath. "
            + empathetic
        )
    elif low_confidence:
        empathetic = "From what you shared, the clearest part is this: " + empathetic[0].lower() + empathetic[1:]

    return empathetic, suggestion, None


def _classify_gemini_failure(exc: Exception) -> dict[str, object]:
    message = str(exc)
    if "requires GEMINI_API_KEY" in message or "requires the 'google-genai' package" in message:
        return {
            "gemini_call_attempted": False,
            "gemini_call_succeeded": False,
            "gemini_parse_succeeded": None,
            "gemini_validation_succeeded": None,
        }
    if "returned invalid JSON" in message or "returned empty text" in message:
        return {
            "gemini_call_attempted": True,
            "gemini_call_succeeded": False,
            "gemini_parse_succeeded": False,
            "gemini_validation_succeeded": None,
        }
    if (
        "returned invalid style" in message
        or "returned invalid specificity" in message
        or "returned empty reasoning_note" in message
        or "returned empty empathetic_response" in message
    ):
        return {
            "gemini_call_attempted": True,
            "gemini_call_succeeded": False,
            "gemini_parse_succeeded": True,
            "gemini_validation_succeeded": False,
        }
    if "Gemini response generation failed:" in message:
        return {
            "gemini_call_attempted": True,
            "gemini_call_succeeded": False,
            "gemini_parse_succeeded": None,
            "gemini_validation_succeeded": None,
        }
    return {
        "gemini_call_attempted": None,
        "gemini_call_succeeded": False,
        "gemini_parse_succeeded": None,
        "gemini_validation_succeeded": None,
    }


def _run_en_demo_payload(
    *,
    text: str,
    user_name: str | None = None,
    context_tag: str | None = None,
    include_debug: bool = False,
) -> tuple[DemoAICoreResponse, dict[str, object] | None]:
    del user_name

    settings = get_settings()
    ensure_demo_enabled(get_settings_fn=get_settings)

    detected_language = detect_language(text)
    if detected_language == "zh":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chinese is disabled in the current AI core demo preset.",
        )
    if detected_language != "vi":
        detected_language = "en"

    safety_result, risk_level, topic_tags = build_demo_safety_context(
        text,
        context_tag,
        detect_safety_risk_fn=detect_safety_risk,
        tag_topics_fn=tag_topics,
    )
    memory_store = get_demo_memory_store()
    recent_memory = list_recent_demo_memory("en-demo", days=7, get_demo_memory_store_fn=lambda: memory_store)
    companion_pipeline = build_companion_pipeline(
        transcript=text,
        emotion_analysis={
            **analyze_emotion(text, risk_level=risk_level, audio_path=None),
            "language": detected_language,
        },
        topic_tags=topic_tags,
        risk_level=risk_level,
        context_tag=context_tag,
        memory_records=recent_memory,
        emotion_postprocessor=lambda analysis, render_context: _apply_render_adjustments(text, analysis, render_context),
    )
    render_context = companion_pipeline.render_context
    emotion_analysis = companion_pipeline.emotion_analysis
    if "primary_label" not in emotion_analysis:
        emotion_analysis = normalize_emotion_analysis(emotion_analysis, risk_level)
    normalized_state = companion_pipeline.normalized_state
    memory_summary = companion_pipeline.memory_summary
    insight_features = companion_pipeline.insight_features
    support_strategy = companion_pipeline.support_strategy
    response_plan = companion_pipeline.response_plan

    low_confidence_flag = float(emotion_analysis["confidence"]) < 0.5
    render_payload = {
        "input_text": text,
        "language": str(emotion_analysis["language"]),
        "primary_emotion": str(emotion_analysis["primary_emotion"]),
        "secondary_emotions": [str(item) for item in emotion_analysis["secondary_emotions"]],
        "confidence": float(emotion_analysis["confidence"]),
        "valence_score": float(emotion_analysis["valence_score"]),
        "energy_score": float(emotion_analysis["energy_score"]),
        "stress_score": float(emotion_analysis["stress_score"]),
        "response_mode": str(emotion_analysis["response_mode"]),
        "topic_tags": topic_tags,
        "risk_level": risk_level,
        "utterance_type": render_context.utterance_type,
        "event_type": render_context.event_type,
        "relationship_target": render_context.relationship_target,
        "short_event_flag": render_context.short_event_flag,
        "low_confidence_flag": low_confidence_flag,
        "evidence_spans": [str(item) for item in render_context.evidence_spans],
        "social_context": render_context.social_context,
        "concern_target": render_context.concern_target,
        "suggestion_allowed": True,
        "memory_summary": memory_summary.model_dump(),
        "insight_features": insight_features.model_dump(),
    }

    demo_provider = (settings.ai_core_demo_response_provider or "gemini").casefold().strip()
    support_provider_name = "template"
    fallback_reason = None
    gemini_path_entered = False
    gemini_api_key_detected = bool(settings.gemini_api_key)
    request_language = detected_language
    configured_demo_language = str(getattr(settings, "ai_core_demo_language", "en"))
    gemini_call_attempted = False
    gemini_call_succeeded = False
    gemini_parse_succeeded = None
    gemini_validation_succeeded = None
    fallback_used = False
    error_stage = None
    response_parse_status = None
    validation_error_summary = None
    debug_bundle = None
    if demo_provider == "gemini" and risk_level == "low":
        gemini_path_entered = True
        demo_response_plan = dict(response_plan)
        demo_response_plan["quote_allowed"] = False
        demo_response_plan["render_payload"] = render_payload
        if include_debug or settings.ai_render_debug:
            debug_bundle = build_gemini_render_debug_bundle(
                transcript=text,
                emotion_analysis=emotion_analysis,
                topic_tags=topic_tags,
                response_plan=demo_response_plan,
            )
        gemini_call_attempted = True
        try:
            rendered = render_supportive_response(
                transcript=text,
                emotion_analysis=emotion_analysis,
                topic_tags=topic_tags,
                risk_level=risk_level,
                response_plan=demo_response_plan,
                user_id="en-demo",
                quote_opt_in=False,
                provider_override="gemini",
            )
            empathetic_response = str(rendered["empathetic_response"])
            gentle_suggestion = str(rendered["gentle_suggestion"]) if rendered["gentle_suggestion"] is not None else None
            safety_note = str(rendered["safety_note"]) if rendered.get("safety_note") is not None else None
            support_provider_name = str(rendered.get("provider_name", "gemini"))
            renderer_debug = rendered.get("debug") or {}
            gemini_call_attempted = bool(renderer_debug.get("gemini_call_attempted", gemini_call_attempted))
            gemini_call_succeeded = bool(renderer_debug.get("gemini_call_succeeded", True))
            gemini_parse_succeeded = renderer_debug.get("gemini_parse_succeeded", True)
            gemini_validation_succeeded = renderer_debug.get("gemini_validation_succeeded", True)
            response_parse_status = "parsed_json"
            if include_debug or settings.ai_render_debug:
                debug_bundle = {
                    **(debug_bundle or {}),
                    "memory_summary": memory_summary.model_dump(),
                    "insight_features": insight_features.model_dump(),
                    "request_language": request_language,
                    "configured_demo_language": configured_demo_language,
                    "selected_demo_provider": demo_provider,
                    "gemini_path_entered": gemini_path_entered,
                    "gemini_api_key_detected": gemini_api_key_detected,
                    "gemini_call_attempted": gemini_call_attempted,
                    "gemini_call_succeeded": gemini_call_succeeded,
                    "gemini_parse_succeeded": gemini_parse_succeeded,
                    "gemini_validation_succeeded": gemini_validation_succeeded,
                    "renderer_selected": support_provider_name,
                    "fallback_triggered": False,
                    "fallback_reason": None,
                    "raw_renderer_output": rendered.get("raw_renderer_output"),
                    "renderer_debug": renderer_debug,
                }
        except (ProviderConfigurationError, ProviderExecutionError) as exc:
            empathetic_response, gentle_suggestion, safety_note = _build_demo_response_text(
                text=text,
                emotion_analysis=emotion_analysis,
                render_context=render_context,
                risk_level=risk_level,
            )
            support_provider_name = "template_fallback"
            fallback_used = True
            fallback_reason, error_stage, response_parse_status, validation_error_summary = _summarize_gemini_failure(exc)
            failure_debug = _classify_gemini_failure(exc)
            gemini_call_attempted = failure_debug["gemini_call_attempted"] if failure_debug["gemini_call_attempted"] is not None else gemini_call_attempted
            gemini_call_succeeded = bool(failure_debug["gemini_call_succeeded"])
            gemini_parse_succeeded = failure_debug["gemini_parse_succeeded"]
            gemini_validation_succeeded = failure_debug["gemini_validation_succeeded"]
            logger.warning(
                "en_demo_gemini_fallback selected_provider=%s fallback_reason=%s error_stage=%s validation_error_summary=%s attempted=%s succeeded=%s",
                demo_provider,
                fallback_reason,
                error_stage,
                validation_error_summary,
                gemini_call_attempted,
                gemini_call_succeeded,
            )
            if include_debug or settings.ai_render_debug:
                debug_bundle = {
                    **(debug_bundle or {}),
                    "memory_summary": memory_summary.model_dump(),
                    "insight_features": insight_features.model_dump(),
                    "request_language": request_language,
                    "configured_demo_language": configured_demo_language,
                    "selected_demo_provider": demo_provider,
                    "gemini_path_entered": gemini_path_entered,
                    "gemini_api_key_detected": gemini_api_key_detected,
                    "gemini_call_attempted": gemini_call_attempted,
                    "gemini_call_succeeded": gemini_call_succeeded,
                    "gemini_parse_succeeded": gemini_parse_succeeded,
                    "gemini_validation_succeeded": gemini_validation_succeeded,
                    "renderer_selected": support_provider_name,
                    "fallback_triggered": True,
                    "fallback_reason": fallback_reason,
                    "validation_error_summary": validation_error_summary,
                    "raw_renderer_output": None,
                }
    else:
        empathetic_response, gentle_suggestion, safety_note = _build_demo_response_text(
            text=text,
            emotion_analysis=emotion_analysis,
            render_context=render_context,
            risk_level=risk_level,
        )
        fallback_used = True
        if demo_provider != "gemini":
            fallback_reason = "provider_not_selected"
            error_stage = "provider_selection"
            response_parse_status = "not_attempted"
        else:
            fallback_reason = "risk_policy_template"
            error_stage = "risk_policy"
            response_parse_status = "not_attempted"
        if include_debug or settings.ai_render_debug:
            debug_bundle = {
                "render_payload": render_payload,
                "memory_summary": memory_summary.model_dump(),
                "insight_features": insight_features.model_dump(),
                "request_language": request_language,
                "configured_demo_language": configured_demo_language,
                "selected_demo_provider": demo_provider,
                "gemini_path_entered": gemini_path_entered,
                "gemini_api_key_detected": gemini_api_key_detected,
                "gemini_call_attempted": gemini_call_attempted,
                "gemini_call_succeeded": gemini_call_succeeded,
                "gemini_parse_succeeded": gemini_parse_succeeded,
                "gemini_validation_succeeded": gemini_validation_succeeded,
                "renderer_selected": support_provider_name,
                "fallback_triggered": demo_provider != "gemini" or risk_level != "low",
                "fallback_reason": fallback_reason,
                "validation_error_summary": validation_error_summary,
                "raw_renderer_output": None,
            }

    payload = DemoAICoreResponse(
        input_text=text,
        language=str(emotion_analysis["language"]),
        topic_tags=topic_tags,
        risk_level=risk_level,
        risk_flags=[str(flag) for flag in safety_result["risk_flags"]],
        emotion=DemoEmotionResponse(
            primary_label=str(emotion_analysis["primary_label"]),
            secondary_labels=[str(item) for item in emotion_analysis["secondary_labels"]],
            all_labels=[str(item) for item in emotion_analysis["all_labels"]],
            scores={str(label): float(score) for label, score in dict(emotion_analysis["scores"]).items()},
            threshold=(
                float(emotion_analysis["threshold"]) if emotion_analysis["threshold"] is not None else None
            ),
            valence_score=float(emotion_analysis["valence_score"]),
            energy_score=float(emotion_analysis["energy_score"]),
            stress_score=float(emotion_analysis["stress_score"]),
            confidence=float(emotion_analysis["confidence"]),
            provider_name=str(emotion_analysis["provider_name"]),
            source=str(emotion_analysis["source"]),
            dominant_signals=[str(item) for item in emotion_analysis["dominant_signals"]],
            context_tags=[str(item) for item in emotion_analysis.get("context_tags", [])],
            response_mode="safe_support" if risk_level in {"high", "medium"} else str(emotion_analysis["response_mode"]),
        ),
        support=DemoSupportResponse(
            empathetic_response=empathetic_response,
            gentle_suggestion=gentle_suggestion,
            safety_note=safety_note,
            provider_name=support_provider_name,
        ),
        ai_core=DemoAICoreDetailsResponse(
            normalized_state=DemoNormalizedStateResponse(
                primary_emotion=normalized_state.primary_emotion,
                secondary_emotions=normalized_state.secondary_emotions,
                valence=normalized_state.valence,
                energy=normalized_state.energy,
                stress=normalized_state.stress,
                emotion_owner=normalized_state.emotion_owner,
                social_context=normalized_state.social_context,
                event_type=normalized_state.event_type,
                concern_target=normalized_state.concern_target,
                uncertainty=normalized_state.uncertainty,
                confidence=normalized_state.confidence,
                response_mode=normalized_state.response_mode,
                risk_level=normalized_state.risk_level,
            ),
            support_strategy=DemoSupportStrategyResponse(
                support_focus=support_strategy.support_focus,
                strategy_type=support_strategy.strategy_type,
                suggestion_budget=support_strategy.suggestion_budget,
                personalization_tone=support_strategy.personalization_tone,
                response_goal=support_strategy.response_goal,
                rationale=support_strategy.rationale,
            ),
            memory_summary=DemoMemorySummaryResponse(
                recent_checkin_count=memory_summary.recent_checkin_count,
                dominant_negative_patterns=memory_summary.dominant_negative_patterns,
                dominant_positive_patterns=memory_summary.dominant_positive_patterns,
                recurring_triggers=memory_summary.recurring_triggers,
                recurring_social_contexts=memory_summary.recurring_social_contexts,
                last_seen_emotional_direction=memory_summary.last_seen_emotional_direction,
                pattern_detected=memory_summary.pattern_detected,
            ),
            insight_features=DemoInsightFeaturesResponse(
                is_negative_checkin=insight_features.is_negative_checkin,
                is_positive_checkin=insight_features.is_positive_checkin,
                work_trigger=insight_features.work_trigger,
                relationship_strain=insight_features.relationship_strain,
                deadline_related=insight_features.deadline_related,
                loneliness_related=insight_features.loneliness_related,
                positive_anchor_candidate=insight_features.positive_anchor_candidate,
                social_support_signal=insight_features.social_support_signal,
                high_stress_flag=insight_features.high_stress_flag,
            ),
            memory_records_used=len(recent_memory),
        ),
    )
    if include_debug or settings.ai_render_debug:
        payload.debug = DemoRenderDebugResponse.model_validate(
            _build_public_debug_bundle(
                selected_provider=demo_provider,
                gemini_call_attempted=gemini_call_attempted,
                gemini_call_succeeded=gemini_call_succeeded,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                error_stage=error_stage,
                response_parse_status=response_parse_status,
                validation_error_summary=validation_error_summary,
            )
        )
    memory_store.append(
        build_emotional_memory_record(
            user_id="en-demo",
            transcript=text,
            topic_tags=topic_tags,
            risk_level=risk_level,
            normalized_state=normalized_state,
            support_strategy=support_strategy,
            insight_features=insight_features,
            response_provider=support_provider_name,
            response_mode=str(emotion_analysis["response_mode"]),
            suggestion_given=gentle_suggestion is not None,
            support_metadata={
                "response_goal": support_strategy.response_goal,
                "support_focus": support_strategy.support_focus,
            },
        )
    )
    return payload, debug_bundle


def build_en_demo_payload(
    *,
    text: str,
    user_name: str | None = None,
    context_tag: str | None = None,
) -> DemoAICoreResponse:
    payload, _ = _run_en_demo_payload(text=text, user_name=user_name, context_tag=context_tag, include_debug=False)
    return payload


def build_en_demo_payload_with_debug(
    *,
    text: str,
    user_name: str | None = None,
    context_tag: str | None = None,
) -> tuple[DemoAICoreResponse, dict[str, object] | None]:
    return _run_en_demo_payload(text=text, user_name=user_name, context_tag=context_tag, include_debug=True)


def build_en_weekly_insight(user_id: str = "en-demo") -> DemoWeeklyInsightResponse:
    records = get_demo_memory_store().list_recent(user_id, days=7)
    insight = build_weekly_insight(user_id, records)
    return DemoWeeklyInsightResponse(
        period_start=insight.period_start.isoformat() if insight.period_start else None,
        period_end=insight.period_end.isoformat() if insight.period_end else None,
        total_checkins=insight.total_checkins,
        emotional_trend=insight.emotional_trend,
        common_negative_triggers=insight.common_negative_triggers,
        common_positive_anchors=insight.common_positive_anchors,
        recurring_contexts=insight.recurring_contexts,
        stress_heavy_contexts=insight.stress_heavy_contexts,
        recurring_relational_patterns=insight.recurring_relational_patterns,
        dominant_emotions=insight.dominant_emotions,
        suggested_reflection_focus=insight.suggested_reflection_focus,
        records_considered_for_insight=insight.records_considered_for_insight,
        summary=insight.summary,
        insight_summary_text=insight.insight_summary_text,
    )
