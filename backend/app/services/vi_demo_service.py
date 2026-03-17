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


def _topic_fragment(topic_tags: list[str], context_tag: str | None) -> str:
    lead = context_tag.strip() if context_tag and context_tag.strip() else (topic_tags[0] if topic_tags else "")
    return f" quanh chuyện {lead}" if lead else ""


def _confidence_prefix(confidence: float) -> str:
    if confidence >= 0.68:
        return ""
    if confidence >= 0.5:
        return "Từ điều bạn chia sẻ, mình đoán là "
    return "Có thể mình chưa nghe hết mọi lớp cảm xúc, nhưng lúc này "


def _with_sentence_start(prefix: str, fragment: str) -> str:
    if prefix:
        return f"{prefix}{fragment}"
    if not fragment:
        return fragment
    return fragment[0].upper() + fragment[1:]


def _maybe_adjust_short_event_emotion(
    text: str,
    emotion_analysis: dict[str, object],
    topic_tags: list[str],
) -> dict[str, object]:
    normalized = text.casefold().strip()
    if len(normalized) > 80:
        return emotion_analysis

    relation_markers = (
        "người yêu",
        "nguoi yeu",
        "mẹ",
        "me ",
        "bố",
        "bo ",
        "ba ",
        "anh trai",
        "chị gái",
        "em mình",
        "ban than",
        "bạn thân",
    )
    health_markers = (
        "ốm",
        "om ",
        "mệt",
        "met ",
        "sốt",
        "sot ",
        "đau",
        "dau ",
        "bệnh",
        "benh ",
        "không khỏe",
        "khong khoe",
    )
    if not any(token in normalized for token in relation_markers):
        return emotion_analysis
    if not any(token in normalized for token in health_markers):
        return emotion_analysis

    adjusted = dict(emotion_analysis)
    current_primary = str(adjusted.get("primary_emotion", "neutral"))
    if current_primary in {"neutral", "sadness", "loneliness"}:
        adjusted["primary_emotion"] = "anxiety"
        secondaries = [str(item) for item in adjusted.get("secondary_emotions", []) if str(item) != "anxiety"]
        adjusted["secondary_emotions"] = (["sadness"] + secondaries)[:3]
        adjusted["emotion_label"] = "lo lắng"
        adjusted["label"] = "lo lắng"
        adjusted["valence_score"] = -0.28
        adjusted["energy_score"] = max(0.3, min(0.5, float(adjusted.get("energy_score", 0.3))))
        adjusted["stress_score"] = max(0.42, float(adjusted.get("stress_score", 0.0)))
        adjusted["confidence"] = min(float(adjusted.get("confidence", 0.4)), 0.46)
        adjusted["response_mode"] = "supportive_reflective"
        dominant_signals = [str(item) for item in adjusted.get("dominant_signals", [])]
        adjusted["dominant_signals"] = list(
            dict.fromkeys(["anxiety_activation", "connection_need", *dominant_signals])
        )
        adjusted["provider_name"] = f"{adjusted.get('provider_name', 'unknown')}+vi_demo_short_event_adjustment"
        source_metadata = dict(adjusted.get("source_metadata", {}))
        source_metadata["demo_adjustment"] = "short_relationship_health_event"
        adjusted["source_metadata"] = source_metadata
        if "sức khỏe" in topic_tags and "tình cảm" in topic_tags:
            adjusted["social_need_score"] = max(float(adjusted.get("social_need_score", 0.0)), 0.34)
    return adjusted


def _build_demo_response_text(
    *,
    emotion_analysis: dict[str, object],
    response_plan: dict[str, object],
    risk_level: str,
    topic_tags: list[str],
    context_tag: str | None,
) -> tuple[str, str | None, str | None]:
    del response_plan

    if risk_level in {"high", "medium"}:
        return (
            generate_safe_support_message(risk_level),
            None,
            "Nếu thấy mình không an toàn, hãy ưu tiên ở gần một người đáng tin hoặc tìm hỗ trợ khẩn cấp tại nơi bạn đang ở.",
        )

    response_mode = str(emotion_analysis["response_mode"])
    primary_emotion = str(emotion_analysis["primary_emotion"])
    confidence = float(emotion_analysis["confidence"])
    stress_score = float(emotion_analysis["stress_score"])
    topic = _topic_fragment(topic_tags, context_tag)
    prefix = _confidence_prefix(confidence)

    if response_mode == "celebratory_warm":
        if primary_emotion == "gratitude":
            empathetic = (
                f"{_with_sentence_start(prefix, f'mình nghe khá rõ sự biết ơn và nhẹ lại{topic}')}. "
                "Có vẻ bạn đang chạm vào một điều thật sự nâng đỡ mình, và cảm giác đó đáng được giữ lại thêm một chút."
            )
        else:
            empathetic = (
                f"{_with_sentence_start(prefix, f'mình nghe thấy một phần sáng hơn trong điều bạn vừa kể{topic}')}. "
                "Khoảnh khắc dễ chịu này không cần làm gì lớn lao, chỉ cần được công nhận là đã có thật."
            )
        suggestion = "Nếu muốn, bạn có thể giữ lại một chi tiết nhỏ đang làm hôm nay dễ thở hơn."
    elif response_mode == "grounding_soft":
        empathetic = (
            f"{_with_sentence_start(prefix, f'áp lực đang dồn lên bạn khá nhiều{topic}')}. "
            "Mình không nghĩ bạn cần ép mình phải ổn ngay bây giờ, chỉ cần chậm lại một nhịp cũng đã là đủ."
        )
        suggestion = "Nếu thấy hợp, thử thả vai xuống và hít ra chậm hơn một nhịp."
    elif response_mode == "low_energy_comfort":
        if primary_emotion == "loneliness" and confidence >= 0.62 and "sức khỏe" not in topic_tags:
            empathetic = (
                f"{_with_sentence_start(prefix, f'bạn đã ôm cảm giác lạc lõng này khá lâu{topic}')}. "
                "Chỉ riêng việc bạn nói ra nó lúc này cũng đã là một cách tự dịu mình rất tử tế."
            )
        else:
            empathetic = (
                f"{_with_sentence_start(prefix, f'năng lượng của bạn đang xuống khá thấp{topic}')}. "
                "Mình muốn ghi nhận sự mệt đó mà không bắt bạn phải gượng lên ngay."
            )
        suggestion = "Nếu được, cho mình một khoảng nghỉ thật ngắn mà không ép phải làm thêm gì ngay."
    elif response_mode == "validating_gentle":
        empathetic = (
            f"{_with_sentence_start(prefix, f'có một phần nặng và căng trong điều bạn vừa kể{topic}')}. "
            "Phản ứng đó không hề quá đáng, nó cho thấy chuyện này thật sự chạm vào bạn."
        )
        suggestion = "Nếu thấy hợp, lùi lại một nhịp trước khi phải quyết định hay phản hồi điều gì tiếp theo."
    else:
        if primary_emotion == "overwhelm":
            empathetic = (
                f"{_with_sentence_start(prefix, f'mọi thứ đang hơi dồn lại cùng một lúc{topic}')}. "
                "Mình nghe ra cả phần muốn cố tiếp lẫn phần đã bắt đầu mỏi, và cả hai đều rất dễ hiểu."
            )
        elif primary_emotion == "anxiety":
            empathetic = (
                f"{_with_sentence_start(prefix, f'bạn đang mang theo một nỗi lo khá rõ{topic}')}. "
                "Dù vậy, mình vẫn nghe thấy trong đó một phần đang cố giữ nhịp để đi tiếp."
            )
        else:
            empathetic = (
                f"{_with_sentence_start(prefix, f'điều bạn vừa chia sẻ có nhiều lớp cảm xúc đi cùng nhau{topic}')}. "
                "Mình muốn giữ nguyên cả phần nặng lẫn phần vẫn còn hy vọng, thay vì ép nó phải gọn lại quá sớm."
            )
        suggestion = None if stress_score >= 0.62 else "Nếu muốn, thử gọi tên phần nào đang nặng nhất và phần nào vẫn còn hy vọng."

    if confidence < 0.45:
        suggestion = None if suggestion is None else suggestion
        empathetic = (
            "Mình có thể chưa nắm hết mọi sắc thái trong điều bạn vừa nói. "
            + empathetic[0].lower()
            + empathetic[1:]
        )

    return empathetic, suggestion, None


def build_vi_demo_payload(
    *,
    text: str,
    user_name: str | None = None,
    context_tag: str | None = None,
) -> DemoAICoreResponse:
    del user_name

    settings = get_settings()
    if not settings.enable_ai_core_demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI core demo is disabled")

    requested_language = settings.ai_core_demo_language or settings.demo_locale
    detected_language = detect_language(text)
    if requested_language == "vi" and detected_language != "vi":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Current demo preset only supports Vietnamese text input.",
        )
    if settings.ai_core_demo_disable_zh and detected_language == "zh":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chinese is disabled in the current AI core demo preset.",
        )

    safety_result = detect_safety_risk(text)
    risk_level = str(safety_result["risk_level"])
    topic_tags = tag_topics(text)
    if context_tag and context_tag.strip() and context_tag.strip() not in topic_tags:
        topic_tags = [context_tag.strip(), *topic_tags][:3]

    emotion_analysis = analyze_emotion(text, risk_level=risk_level, audio_path=None)
    emotion_analysis = _maybe_adjust_short_event_emotion(text, emotion_analysis, topic_tags)
    response_plan = build_response_plan(
        transcript=text,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        recent_trend=None,
    )
    demo_provider = settings.ai_core_demo_response_provider.casefold().strip()
    empathetic_response: str
    gentle_suggestion: str | None
    safety_note: str | None
    support_provider_name = "template"
    if demo_provider == "gemini" and risk_level == "low":
        try:
            demo_response_plan = dict(response_plan)
            demo_response_plan["quote_allowed"] = False
            rendered = render_supportive_response(
                transcript=text,
                emotion_analysis=emotion_analysis,
                topic_tags=topic_tags,
                risk_level=risk_level,
                response_plan=demo_response_plan,
                user_id="vi-demo",
                quote_opt_in=False,
                provider_override="gemini",
            )
            empathetic_response = str(rendered["empathetic_response"])
            gentle_suggestion = (
                str(rendered["gentle_suggestion"]) if rendered["gentle_suggestion"] is not None else None
            )
            safety_note = None
            support_provider_name = str(rendered.get("provider_name", "gemini"))
        except (ProviderConfigurationError, ProviderExecutionError):
            empathetic_response, gentle_suggestion, safety_note = _build_demo_response_text(
                emotion_analysis=emotion_analysis,
                response_plan=response_plan,
                risk_level=risk_level,
                topic_tags=topic_tags,
                context_tag=context_tag,
            )
            support_provider_name = "template_fallback"
    else:
        empathetic_response, gentle_suggestion, safety_note = _build_demo_response_text(
            emotion_analysis=emotion_analysis,
            response_plan=response_plan,
            risk_level=risk_level,
            topic_tags=topic_tags,
            context_tag=context_tag,
        )
        support_provider_name = "template"

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
