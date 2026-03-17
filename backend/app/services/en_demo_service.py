from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.demo import DemoAICoreResponse, DemoEmotionResponse, DemoSupportResponse
from app.services.ai_core.language_service import detect_language
from app.services.emotion_service import analyze_emotion
from app.services.empathy_service import build_response_plan
from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError
from app.services.response_service import render_supportive_response
from app.services.safety_service import detect_safety_risk, generate_safe_support_message
from app.services.topic_service import tag_topics


def _detect_utterance_type(text: str) -> dict[str, object]:
    normalized = text.casefold().strip()
    tokens = normalized.split()
    evidence_spans: list[str] = []

    relationship_terms = {
        "girlfriend": "girlfriend",
        "boyfriend": "boyfriend",
        "partner": "partner",
        "wife": "wife",
        "husband": "husband",
        "friend": "friend",
        "mom": "mom",
        "mother": "mother",
        "dad": "dad",
        "father": "father",
        "sister": "sister",
        "brother": "brother",
    }
    health_terms = ("sick", "ill", "fever", "hospital", "hurt", "not well", "unwell")
    appreciation_terms = (
        "told me i'd be good",
        "told me i would be good",
        "told me i'd actually be good",
        "told me i would actually be good",
        "said i'd be good",
        "said i would be good",
        "good at helping",
        "good at this",
        "appreciated",
        "proud of me",
        "kindness",
        "thankful",
        "grateful",
    )
    low_energy_terms = ("tired", "drained", "low on battery", "empty", "flat", "exhausted")
    distress_terms = ("i feel", "i've been", "i have been", "can't stop", "cannot stop", "worried", "anxious", "overwhelmed")

    relationship_target = None
    for term, label in relationship_terms.items():
        if term in normalized:
            relationship_target = label
            evidence_spans.append(term)
            break

    health_related = any(term in normalized for term in health_terms)
    if health_related:
        evidence_spans.extend([term for term in health_terms if term in normalized])

    appreciation_or_recognition = any(term in normalized for term in appreciation_terms) or (
        "told me" in normalized and "good at" in normalized
    )
    if appreciation_or_recognition:
        evidence_spans.extend([term for term in appreciation_terms if term in normalized])

    low_energy_update = any(term in normalized for term in low_energy_terms)
    if low_energy_update:
        evidence_spans.extend([term for term in low_energy_terms if term in normalized])

    distress_checkin = any(term in normalized for term in distress_terms)
    if distress_checkin:
        evidence_spans.extend([term for term in distress_terms if term in normalized])

    short_personal_update = len(tokens) <= 8
    short_event_flag = short_personal_update and not distress_checkin
    relationship_concern = relationship_target is not None
    return {
        "short_personal_update": short_personal_update,
        "relationship_concern": relationship_concern,
        "health_related_update": health_related,
        "distress_checkin": distress_checkin,
        "appreciation_or_recognition": appreciation_or_recognition,
        "low_energy_update": low_energy_update,
        "relationship_target": relationship_target,
        "short_event_flag": short_event_flag,
        "evidence_spans": list(dict.fromkeys(evidence_spans)),
    }


def _apply_utterance_adjustments(
    text: str,
    emotion_analysis: dict[str, object],
    utterance_type: dict[str, object],
) -> dict[str, object]:
    del text
    adjusted = dict(emotion_analysis)
    if (
        utterance_type["short_personal_update"]
        and utterance_type["relationship_concern"]
        and utterance_type["health_related_update"]
    ):
        adjusted["primary_emotion"] = "anxiety"
        adjusted["secondary_emotions"] = ["sadness", "neutral"]
        adjusted["emotion_label"] = "anxiety"
        adjusted["label"] = "anxiety"
        adjusted["valence_score"] = -0.24
        adjusted["energy_score"] = 0.36
        adjusted["stress_score"] = 0.44
        adjusted["confidence"] = min(float(adjusted.get("confidence", 0.45)), 0.48)
        adjusted["response_mode"] = "supportive_reflective"
        dominant_signals = [str(item) for item in adjusted.get("dominant_signals", [])]
        adjusted["dominant_signals"] = list(dict.fromkeys(["anxiety_activation", "connection_need", *dominant_signals]))
        adjusted["provider_name"] = f"{adjusted.get('provider_name', 'unknown')}+en_demo_utterance_adjustment"
        source_metadata = dict(adjusted.get("source_metadata", {}))
        source_metadata["demo_adjustment"] = "short_relational_health_update"
        adjusted["source_metadata"] = source_metadata
    elif utterance_type["appreciation_or_recognition"]:
        adjusted["primary_emotion"] = "gratitude"
        adjusted["secondary_emotions"] = ["joy", "neutral"]
        adjusted["emotion_label"] = "gratitude"
        adjusted["label"] = "gratitude"
        adjusted["valence_score"] = 0.38
        adjusted["energy_score"] = 0.46
        adjusted["stress_score"] = min(float(adjusted.get("stress_score", 0.3)), 0.28)
        adjusted["confidence"] = max(float(adjusted.get("confidence", 0.0)), 0.52)
        adjusted["response_mode"] = "supportive_reflective" if float(adjusted.get("confidence", 0.0)) < 0.55 else "celebratory_warm"
        adjusted["provider_name"] = f"{adjusted.get('provider_name', 'unknown')}+en_demo_utterance_adjustment"
    elif utterance_type["low_energy_update"] and not utterance_type["relationship_concern"]:
        adjusted["response_mode"] = "low_energy_comfort"
    return adjusted


def _topic_fragment(topic_tags: list[str], context_tag: str | None) -> str:
    lead = context_tag.strip() if context_tag and context_tag.strip() else (topic_tags[0] if topic_tags else "")
    return f" around {lead}" if lead else ""


def _confidence_prefix(confidence: float) -> str:
    if confidence >= 0.68:
        return ""
    if confidence >= 0.5:
        return "From what you're sharing, it seems like "
    return "I may not be catching every layer of this, but right now "


def _with_sentence_start(prefix: str, fragment: str) -> str:
    if prefix:
        return f"{prefix}{fragment}"
    if not fragment:
        return fragment
    return fragment[0].upper() + fragment[1:]


def _build_demo_response_text(
    *,
    emotion_analysis: dict[str, object],
    utterance_type: dict[str, object],
    risk_level: str,
    topic_tags: list[str],
    context_tag: str | None,
) -> tuple[str, str | None, str | None]:
    if risk_level in {"high", "medium"}:
        return (
            generate_safe_support_message(risk_level),
            None,
            "If you feel unsafe, please prioritize staying near someone you trust or reaching out for urgent local support.",
        )

    response_mode = str(emotion_analysis["response_mode"])
    primary_emotion = str(emotion_analysis["primary_emotion"])
    confidence = float(emotion_analysis["confidence"])
    stress_score = float(emotion_analysis["stress_score"])
    topic = _topic_fragment(topic_tags, context_tag)
    prefix = _confidence_prefix(confidence)

    if utterance_type["relationship_concern"] and utterance_type["health_related_update"]:
        target = str(utterance_type.get("relationship_target") or "someone close to you")
        empathetic = (
            f"{_with_sentence_start(prefix, f'it makes sense that your attention is going to your {target} first')}. "
            "When someone you care about is unwell, even a short update can leave a lot of concern sitting in the background."
        )
        suggestion = "If it helps, one small check-in or one practical act of care may feel steadier than looping alone."
        return empathetic, suggestion, None

    if utterance_type["appreciation_or_recognition"]:
        empathetic = (
            f"{_with_sentence_start(prefix, f'that kind of recognition can land more deeply than people expect{topic}')}. "
            "It makes sense if part of you is still taking in what it means."
        )
        suggestion = "If you want, hold onto the exact words that felt most believable."
        return empathetic, suggestion, None

    if utterance_type["short_personal_update"] and confidence < 0.5:
        empathetic = (
            "This sounds more like a quick snapshot than a full check-in. "
            f"{_with_sentence_start('', f'from the little you shared, there may be something emotionally important sitting underneath{topic}') }."
        )
        suggestion = "If you want, adding one more sentence about what this stirred in you would make the signal clearer."
        return empathetic, suggestion, None

    if response_mode == "celebratory_warm":
        if primary_emotion == "gratitude":
            empathetic = (
                f"{_with_sentence_start(prefix, f'I can hear some gratitude and relief{topic}')}. "
                "Whatever softened for you today seems real, and it deserves to be noticed."
            )
        else:
            empathetic = (
                f"{_with_sentence_start(prefix, f'there is a brighter note in what you just shared{topic}')}. "
                "You do not have to make it bigger than it is for it to matter."
            )
        suggestion = "If you want, hold onto one detail from today that felt a little steadier."
    elif response_mode == "grounding_soft":
        empathetic = (
            f"{_with_sentence_start(prefix, f'the pressure sounds pretty intense{topic}')}. "
            "You do not need to force yourself to feel okay right away for this to count as a hard moment."
        )
        suggestion = "If it helps, let your shoulders drop and exhale a little more slowly once."
    elif response_mode == "low_energy_comfort":
        if primary_emotion == "loneliness":
            empathetic = (
                f"{_with_sentence_start(prefix, f'this sounds lonely and heavy{topic}')}. "
                "Saying it out loud already counts as a gentle way of taking care of yourself."
            )
        else:
            empathetic = (
                f"{_with_sentence_start(prefix, f'your energy sounds really low{topic}')}. "
                "I want to acknowledge that tiredness without pushing you to snap out of it."
            )
        suggestion = "If you can, give yourself one very small pause without asking anything else from yourself."
    elif response_mode == "validating_gentle":
        empathetic = (
            f"{_with_sentence_start(prefix, f'there is a lot of strain in what you just described{topic}')}. "
            "That reaction makes sense, especially if this has been sitting with you for a while."
        )
        suggestion = "If it feels right, give yourself a beat before deciding what needs to happen next."
    else:
        if primary_emotion == "anxiety":
            empathetic = (
                f"{_with_sentence_start(prefix, f'there is a real thread of worry here{topic}')}. "
                "At the same time, it sounds like part of you is still trying to stay steady."
            )
        elif primary_emotion == "overwhelm":
            empathetic = (
                f"{_with_sentence_start(prefix, f'too much may be landing at once{topic}')}. "
                "I can hear both the part of you that wants to keep going and the part that is getting worn down."
            )
        else:
            empathetic = (
                f"{_with_sentence_start(prefix, f'there are a few emotional layers moving together here{topic}')}. "
                "Nothing about that needs to be cleaned up too quickly."
            )
        suggestion = None if stress_score >= 0.62 else "If you want, name the heaviest part first and leave the rest for later."

    if confidence < 0.45:
        empathetic = "I may not be reading every part of this perfectly. " + empathetic

    return empathetic, suggestion, None


def build_en_demo_payload(
    *,
    text: str,
    user_name: str | None = None,
    context_tag: str | None = None,
) -> DemoAICoreResponse:
    del user_name

    settings = get_settings()
    if not settings.enable_ai_core_demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI core demo is disabled")

    detected_language = detect_language(text)
    if detected_language == "zh":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chinese is disabled in the current AI core demo preset.",
        )

    safety_result = detect_safety_risk(text)
    risk_level = str(safety_result["risk_level"])
    topic_tags = tag_topics(text)
    if context_tag and context_tag.strip() and context_tag.strip() not in topic_tags:
        topic_tags = [context_tag.strip(), *topic_tags][:3]

    utterance_type = _detect_utterance_type(text)
    emotion_analysis = analyze_emotion(text, risk_level=risk_level, audio_path=None)
    emotion_analysis = _apply_utterance_adjustments(text, emotion_analysis, utterance_type)
    response_plan = build_response_plan(
        transcript=text,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        recent_trend=None,
    )
    low_confidence_flag = float(emotion_analysis["confidence"]) < 0.5
    render_payload = {
        "input_text": text,
        "topic_tags": topic_tags,
        "primary_emotion": emotion_analysis["primary_emotion"],
        "secondary_emotions": emotion_analysis["secondary_emotions"],
        "confidence": emotion_analysis["confidence"],
        "response_mode": emotion_analysis["response_mode"],
        "utterance_type": utterance_type,
        "relationship_target": utterance_type["relationship_target"],
        "short_event_flag": utterance_type["short_event_flag"],
        "low_confidence_flag": low_confidence_flag,
        "evidence_spans": utterance_type["evidence_spans"],
    }
    demo_provider = (settings.ai_core_demo_response_provider or "gemini").casefold().strip()
    support_provider_name = "template"
    if demo_provider == "gemini" and risk_level == "low":
        try:
            demo_response_plan = dict(response_plan)
            demo_response_plan["quote_allowed"] = False
            demo_response_plan["render_payload"] = render_payload
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
        except (ProviderConfigurationError, ProviderExecutionError):
            empathetic_response, gentle_suggestion, safety_note = _build_demo_response_text(
                emotion_analysis=emotion_analysis,
                utterance_type=utterance_type,
                risk_level=risk_level,
                topic_tags=topic_tags,
                context_tag=context_tag,
            )
            support_provider_name = "template_fallback"
    else:
        empathetic_response, gentle_suggestion, safety_note = _build_demo_response_text(
            emotion_analysis=emotion_analysis,
            utterance_type=utterance_type,
            risk_level=risk_level,
            topic_tags=topic_tags,
            context_tag=context_tag,
        )

    return DemoAICoreResponse(
        input_text=text,
        language=str(emotion_analysis["language"]),
        topic_tags=topic_tags,
        risk_level=risk_level,
        risk_flags=[str(flag) for flag in safety_result["risk_flags"]],
        emotion=DemoEmotionResponse(
            primary_emotion=str(emotion_analysis["primary_emotion"]),
            secondary_emotions=[str(item) for item in emotion_analysis["secondary_emotions"]],
            emotion_label=str(emotion_analysis["emotion_label"]),
            valence_score=float(emotion_analysis["valence_score"]),
            energy_score=float(emotion_analysis["energy_score"]),
            stress_score=float(emotion_analysis["stress_score"]),
            confidence=float(emotion_analysis["confidence"]),
            provider_name=str(emotion_analysis["provider_name"]),
            response_mode="safe_support" if risk_level in {"high", "medium"} else str(emotion_analysis["response_mode"]),
        ),
        support=DemoSupportResponse(
            empathetic_response=empathetic_response,
            gentle_suggestion=gentle_suggestion,
            safety_note=safety_note,
            provider_name=support_provider_name,
        ),
    )
