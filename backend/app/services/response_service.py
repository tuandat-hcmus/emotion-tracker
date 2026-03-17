import json
from typing import Any, Protocol

from app.core.config import get_settings
from app.schemas.me import QuoteResponse
from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError
from app.services.quote_service import select_quote
from app.services.safety_service import generate_safe_support_message


class ResponseGeneratorProvider(Protocol):
    def generate(
        self,
        *,
        transcript: str,
        emotion_analysis: dict[str, object],
        topic_tags: list[str],
        response_plan: dict[str, object],
    ) -> dict[str, object]:
        ...


def _compose_legacy_response(
    empathetic_response: str,
    gentle_suggestion: str | None,
    quote: QuoteResponse | None,
) -> str:
    parts = [empathetic_response]
    if gentle_suggestion:
        parts.append(gentle_suggestion)
    if quote:
        parts.append(quote.short_text)
    return " ".join(part.strip() for part in parts if part and part.strip())


def _has_signal(emotion_analysis: dict[str, object], signal: str) -> bool:
    return signal in {str(item) for item in emotion_analysis.get("dominant_signals", [])}


class MockResponseGeneratorProvider:
    def generate(
        self,
        *,
        transcript: str,
        emotion_analysis: dict[str, object],
        topic_tags: list[str],
        response_plan: dict[str, object],
    ) -> dict[str, object]:
        del transcript
        primary_topic = topic_tags[0] if topic_tags else "đời sống hằng ngày"
        language = str(emotion_analysis.get("language", "en"))
        response_mode = str(emotion_analysis["response_mode"])
        stress_score = float(emotion_analysis["stress_score"])
        acknowledgment_focus = str(response_plan.get("acknowledgment_focus", "mixed_state"))
        opening_style = str(response_plan.get("opening_style", "reflective"))

        if language == "en":
            primary_topic = topic_tags[0] if topic_tags else "daily life"
            if response_mode == "celebratory_warm":
                empathetic_response = (
                    f"I can hear a warmer note in what you shared about {primary_topic}. "
                    "Whatever softened here seems real, and it deserves to be noticed."
                )
            elif response_mode == "low_energy_comfort":
                empathetic_response = (
                    f"It sounds like your energy is running low around {primary_topic}. "
                    "I want to acknowledge that tiredness without pushing you to feel different right away."
                )
            elif response_mode == "grounding_soft":
                empathetic_response = (
                    f"It sounds like the pressure around {primary_topic} is landing hard right now. "
                    "You do not need to force yourself to be okay immediately."
                )
            elif response_mode == "validating_gentle":
                empathetic_response = (
                    f"There is a lot of strain in what you shared about {primary_topic}. "
                    "That reaction makes sense and does not need to be dismissed."
                )
            else:
                empathetic_response = (
                    f"There are a few emotional layers moving together in what you shared about {primary_topic}. "
                    "Nothing about that needs to be simplified too quickly."
                )

            gentle_suggestion = None
            if bool(response_plan["suggestion_allowed"]):
                suggestion_style = str(response_plan["suggestion_style"])
                if suggestion_style == "small_grounding":
                    gentle_suggestion = "If it helps, take one slower exhale before deciding what comes next."
                elif suggestion_style == "small_reflective" and stress_score < 0.6:
                    gentle_suggestion = "If you want, name the heaviest part first and leave the rest for later."
                elif suggestion_style == "gentle_connection":
                    gentle_suggestion = "If it feels safe, sending one honest line to someone you trust is enough."
                elif suggestion_style == "restful_permission":
                    gentle_suggestion = "If you can, give yourself one very small pause without asking more from yourself."
                elif suggestion_style == "savoring":
                    gentle_suggestion = "If you want, stay with the steadier part of this moment a little longer."
            return {
                "empathetic_response": empathetic_response,
                "gentle_suggestion": gentle_suggestion,
            }

        if response_mode == "celebratory_warm":
            if _has_signal(emotion_analysis, "pride_growth"):
                empathetic_response = (
                    f"Mình nghe rõ niềm tự hào của bạn trong chuyện {primary_topic}. "
                    "Điều bạn làm được xứng đáng được công nhận."
                )
            elif _has_signal(emotion_analysis, "gratitude_warmth"):
                empathetic_response = (
                    f"Có một sự ấm lại rất rõ trong điều bạn vừa kể về {primary_topic}. "
                    "Cảm giác biết ơn đó đáng để giữ lại thêm một chút."
                )
            elif _has_signal(emotion_analysis, "relief_release"):
                empathetic_response = (
                    f"Nghe như bạn vừa có thể thở ra nhẹ hơn quanh chuyện {primary_topic}. "
                    "Khoảnh khắc dịu xuống này là điều có thật."
                )
            elif _has_signal(emotion_analysis, "calm_steady"):
                empathetic_response = (
                    f"Mình nghe thấy một nhịp bình yên hơn trong điều bạn vừa chia sẻ về {primary_topic}. "
                    "Sự ổn lại này rất đáng trân trọng."
                )
            else:
                empathetic_response = (
                    f"Mình nghe thấy một điểm sáng thật rõ trong điều bạn vừa chia sẻ về {primary_topic}. "
                    "Khoảnh khắc này xứng đáng được ghi nhận."
                )
        elif response_mode == "low_energy_comfort":
            if _has_signal(emotion_analysis, "loneliness_pull"):
                empathetic_response = (
                    f"Có vẻ bạn đã phải ôm phần cô đơn này khá lâu quanh chuyện {primary_topic}. "
                    "Việc bạn nói ra nó lúc này đã là một điều rất đáng quý."
                )
            elif _has_signal(emotion_analysis, "emptiness_numbness"):
                empathetic_response = (
                    f"Nghe như mọi thứ đang hơi rỗng và mờ đi quanh chuyện {primary_topic}. "
                    "Mình muốn ghi nhận sự nặng đó mà không bắt bạn phải gượng lên ngay."
                )
            else:
                empathetic_response = (
                    f"Nghe như năng lượng của bạn đang xuống thấp quanh chuyện {primary_topic}. "
                    "Việc bạn vẫn nói ra điều này đã là đủ cho lúc này."
                )
        elif response_mode == "grounding_soft":
            if acknowledgment_focus == "rising_anxiety" or _has_signal(emotion_analysis, "anxiety_activation"):
                empathetic_response = (
                    f"Nghe như nỗi lo quanh chuyện {primary_topic} đang kéo bạn căng lên khá nhiều. "
                    "Mình ở đây để cùng bạn giữ nhịp lại một chút, không ép bạn phải ổn ngay."
                )
            else:
                empathetic_response = (
                    f"Có vẻ áp lực quanh chuyện {primary_topic} đang dồn lên khá nhiều. "
                    "Mình đang ở đây để ghi nhận sự quá tải đó mà không ép bạn phải ổn ngay."
                )
        elif response_mode == "validating_gentle":
            if _has_signal(emotion_analysis, "anger_friction"):
                empathetic_response = (
                    f"Mình nghe thấy sự bực và căng trong điều bạn vừa kể về {primary_topic}. "
                    "Phản ứng đó có lý do của nó và không cần bị gạt đi quá nhanh."
                )
            else:
                empathetic_response = (
                    f"Mình nghe thấy phần nặng trong điều bạn vừa kể về {primary_topic}. "
                    "Cảm giác đó có lý do để tồn tại và không cần bị gạt đi."
                )
        else:
            if _has_signal(emotion_analysis, "mixed_emotions"):
                empathetic_response = (
                    f"Trong điều bạn vừa chia sẻ về {primary_topic}, mình nghe thấy cả phần sáng lên lẫn phần còn mắc lại. "
                    "Cả hai mặt đó đều đáng được giữ nguyên như chúng đang là."
                )
            elif _has_signal(emotion_analysis, "hope_glimmer"):
                empathetic_response = (
                    f"Nghe như giữa chuyện {primary_topic} vẫn còn một chút hy vọng đang được bạn giữ lại. "
                    "Mình muốn ghi nhận cả phần mong manh lẫn phần đang cố đi tiếp đó."
                )
            elif opening_style == "reflective":
                empathetic_response = (
                    f"Điều bạn vừa chia sẻ về {primary_topic} nghe có nhiều lớp cảm xúc đang đi cùng nhau. "
                    "Mình ghi nhận cả phần rõ ràng lẫn phần còn chưa dễ gọi tên."
                )
            else:
                empathetic_response = (
                    f"Trong điều bạn vừa chia sẻ về {primary_topic}, có nhiều lớp cảm xúc đang đi cùng nhau. "
                    "Mình ghi nhận cả phần rõ ràng lẫn phần còn lẫn lộn đó."
                )

        gentle_suggestion = None
        if bool(response_plan["suggestion_allowed"]):
            suggestion_style = str(response_plan["suggestion_style"])
            if suggestion_style == "small_grounding":
                if _has_signal(emotion_analysis, "anger_friction"):
                    gentle_suggestion = "Nếu thấy hợp, bạn có thể tạm lùi lại một nhịp trước khi phản hồi điều đang làm mình bực."
                else:
                    gentle_suggestion = "Nếu thấy hợp, bạn có thể thử chậm lại một nhịp và chú ý đến hơi thở hoặc cảm giác bàn chân chạm đất."
            elif suggestion_style == "small_reflective" and stress_score < 0.6:
                if _has_signal(emotion_analysis, "mixed_emotions"):
                    gentle_suggestion = "Nếu muốn, bạn có thể thử gọi tên phần nào đang nặng nhất lúc này để mọi thứ bớt lẫn vào nhau."
                else:
                    gentle_suggestion = "Nếu muốn, bạn có thể giữ lại một chi tiết nhỏ đang giúp mình trụ vững hôm nay."
            elif suggestion_style == "gentle_connection":
                gentle_suggestion = "Nếu thấy an toàn và hợp lúc này, nhắn cho một người bạn tin được một câu thật ngắn cũng đã đủ."
            elif suggestion_style == "restful_permission":
                gentle_suggestion = "Nếu có thể, cho mình một khoảng nghỉ rất nhỏ mà không ép bản thân phải làm thêm gì ngay."
            elif suggestion_style == "savoring":
                gentle_suggestion = "Nếu muốn, bạn có thể giữ khoảnh khắc dễ chịu này lâu thêm một chút trước khi chuyển sang việc khác."

        return {
            "empathetic_response": empathetic_response,
            "gentle_suggestion": gentle_suggestion,
        }


class OpenAIResponseGeneratorProvider:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ProviderConfigurationError("Response provider 'openai' requires OPENAI_API_KEY")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderConfigurationError(
                "Response provider 'openai' requires the 'openai' package to be installed"
            ) from exc

        self._client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_request_timeout_seconds,
        )
        self._model = settings.openai_text_model

    def generate(
        self,
        *,
        transcript: str,
        emotion_analysis: dict[str, object],
        topic_tags: list[str],
        response_plan: dict[str, object],
    ) -> dict[str, object]:
        topic_text = ", ".join(topic_tags) if topic_tags else "đời sống hằng ngày"
        prompt = (
            "Return JSON only with keys empathetic_response and gentle_suggestion. "
            "Write in Vietnamese. Keep empathetic_response between 1 and 3 short sentences. "
            "gentle_suggestion should be null or one short sentence. "
            "Be warm, concise, and emotionally aligned. Acknowledge ambiguity when the state looks mixed. "
            "Do not diagnose, do not sound clinical, do not simulate therapy, do not give long advice. "
            f"Emotion analysis: {json.dumps(emotion_analysis, ensure_ascii=False)}. "
            f"Response plan: {json.dumps(response_plan, ensure_ascii=False)}. "
            f"Topics: {topic_text}. Transcript: {transcript}"
        )

        try:
            result = self._client.responses.create(model=self._model, input=prompt)
        except Exception as exc:
            raise ProviderExecutionError(f"OpenAI response generation failed: {exc}") from exc

        output_text = getattr(result, "output_text", None)
        if not output_text:
            raise ProviderExecutionError("OpenAI response generation returned empty text")
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ProviderExecutionError("OpenAI response generation returned invalid JSON") from exc
        empathetic_response = str(payload.get("empathetic_response", "")).strip()
        if not empathetic_response:
            raise ProviderExecutionError("OpenAI response generation returned empty empathetic_response")
        suggestion = payload.get("gentle_suggestion")
        normalized_suggestion = str(suggestion).strip() if isinstance(suggestion, str) and suggestion.strip() else None
        return {
            "empathetic_response": empathetic_response,
            "gentle_suggestion": normalized_suggestion,
        }


class GeminiResponseGeneratorProvider:
    def __init__(self) -> None:
        settings = get_settings()
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

    def generate(
        self,
        *,
        transcript: str,
        emotion_analysis: dict[str, object],
        topic_tags: list[str],
        response_plan: dict[str, object],
    ) -> dict[str, object]:
        topic_text = ", ".join(topic_tags) if topic_tags else "đời sống hằng ngày"
        render_language = str(emotion_analysis.get("language") or get_settings().ai_render_language or "en")
        if render_language == "vi":
            prompt = (
                "Bạn đang viết lời phản hồi hỗ trợ ngắn gọn cho một ứng dụng wellness, không phải chẩn đoán hay trị liệu. "
                "Trả về JSON duy nhất với 2 key: empathetic_response và gentle_suggestion. "
                "Viết bằng tiếng Việt tự nhiên, ấm, ngắn, không lên giọng chuyên gia, không dùng câu sáo rỗng kiểu 'hãy cố lên'. "
                "empathetic_response dài 2 đến 4 câu ngắn. gentle_suggestion là null hoặc 1 câu ngắn. "
                "Không bịa thêm cảm xúc ngoài emotion_analysis. Nếu confidence thấp hoặc trạng thái lẫn lộn, hãy viết thận trọng và ít khẳng định hơn. "
                "Không đưa lời khuyên dài, không chẩn đoán, không nói như therapist. "
                f"Emotion analysis: {json.dumps(emotion_analysis, ensure_ascii=False)}. "
                f"Response plan: {json.dumps(response_plan, ensure_ascii=False)}. "
                f"Topics: {topic_text}. Transcript: {transcript}"
            )
        else:
            few_shots = [
                {
                    "input": "My girlfriend is sick",
                    "output": {
                        "empathetic_response": "It makes sense that your mind is going to her right away. When someone you care about is sick, even a short update can leave a lot of concern sitting in the background.",
                        "gentle_suggestion": "If it helps, one small check-in or one practical act of care may feel steadier than looping alone.",
                        "safety_note": None,
                        "style": "supportive_reflective",
                        "specificity": "medium",
                        "reasoning_note": "Relational concern and health update; acknowledge concern for the other person first.",
                    },
                },
                {
                    "input": "My partner has been sick today and I keep worrying about them.",
                    "output": {
                        "empathetic_response": "It sounds like a lot of your attention is wrapped around someone you love right now. That kind of worry can stay in the background all day, even when you are trying to function normally.",
                        "gentle_suggestion": "If it helps, anchor yourself to one concrete thing you can do for them or with them today.",
                        "safety_note": None,
                        "style": "supportive_reflective",
                        "specificity": "high",
                        "reasoning_note": "Concern-focused response with a relational target.",
                    },
                },
                {
                    "input": "A friend told me I'd be good at this kind of work.",
                    "output": {
                        "empathetic_response": "That kind of recognition can land more deeply than people expect. It makes sense if part of you is still taking in what it means.",
                        "gentle_suggestion": "If you want, hold onto the exact words that felt most believable.",
                        "safety_note": None,
                        "style": "celebratory_warm",
                        "specificity": "medium",
                        "reasoning_note": "Recognition/appreciation; warm but not overblown.",
                    },
                },
                {
                    "input": "I've had deadlines piling up for days.",
                    "output": {
                        "empathetic_response": "That sounds like the kind of pressure that keeps stacking even when you are trying to stay functional. You do not need to minimize it for it to count as a lot.",
                        "gentle_suggestion": "If it helps, choose the next smallest thing rather than the whole pile.",
                        "safety_note": None,
                        "style": "grounding_soft",
                        "specificity": "medium",
                        "reasoning_note": "Deadline pressure; grounding rather than generic comfort.",
                    },
                },
                {
                    "input": "I feel weirdly empty today.",
                    "output": {
                        "empathetic_response": "That kind of emptiness can feel unsettling precisely because it is hard to pin down. I want to acknowledge it without forcing it into a cleaner story too quickly.",
                        "gentle_suggestion": "If you want, describe one small detail of how that emptiness shows up in your body or your day.",
                        "safety_note": None,
                        "style": "low_energy_comfort",
                        "specificity": "medium",
                        "reasoning_note": "Low-energy internal state; quiet acknowledgment fits better than advice.",
                    },
                },
            ]
            prompt = (
                "You are writing a short supportive response for a wellness app, not diagnosis or therapy. "
                "Return JSON only with keys: empathetic_response, gentle_suggestion, safety_note, style, specificity, reasoning_note. "
                "Write natural, warm English. Keep empathetic_response to 2 to 4 short sentences. "
                "gentle_suggestion must be null or one short sentence. safety_note should usually be null in low-risk cases. "
                "Do not invent emotions beyond emotion_analysis. If confidence is low or the state is mixed, stay cautious and avoid overclaiming. "
                "Do not sound clinical, do not write long advice, and do not use generic phrases like 'stay strong'. "
                "Acknowledge concern for another person before shifting to the user's inner state when the render payload suggests a relationship or health update. "
                f"Few-shot examples: {json.dumps(few_shots, ensure_ascii=False)}. "
                f"Emotion analysis: {json.dumps(emotion_analysis, ensure_ascii=False)}. "
                f"Response plan: {json.dumps(response_plan, ensure_ascii=False)}. "
                f"Topics: {topic_text}. Transcript: {transcript}"
            )

        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.7,
            "top_p": 0.9,
        }

        try:
            result = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=generation_config,
            )
        except Exception as exc:
            raise ProviderExecutionError(f"Gemini response generation failed: {exc}") from exc

        output_text = getattr(result, "text", None)
        if not output_text:
            raise ProviderExecutionError("Gemini response generation returned empty text")
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ProviderExecutionError("Gemini response generation returned invalid JSON") from exc

        empathetic_response = str(payload.get("empathetic_response", "")).strip()
        if not empathetic_response:
            raise ProviderExecutionError("Gemini response generation returned empty empathetic_response")
        suggestion = payload.get("gentle_suggestion")
        normalized_suggestion = str(suggestion).strip() if isinstance(suggestion, str) and suggestion.strip() else None
        safety_note_value = payload.get("safety_note")
        normalized_safety_note = (
            str(safety_note_value).strip()
            if isinstance(safety_note_value, str) and safety_note_value.strip()
            else None
        )
        if render_language != "vi":
            style = str(payload.get("style", "")).strip()
            specificity = str(payload.get("specificity", "")).strip()
            reasoning_note = str(payload.get("reasoning_note", "")).strip()
            if style not in {
                "supportive_reflective",
                "grounding_soft",
                "celebratory_warm",
                "low_energy_comfort",
                "safe_support",
                "validating_gentle",
            }:
                raise ProviderExecutionError("Gemini response generation returned invalid style")
            if specificity not in {"low", "medium", "high"}:
                raise ProviderExecutionError("Gemini response generation returned invalid specificity")
            if not reasoning_note:
                raise ProviderExecutionError("Gemini response generation returned empty reasoning_note")
        return {
            "empathetic_response": empathetic_response,
            "gentle_suggestion": normalized_suggestion,
            "safety_note": normalized_safety_note,
            "style": payload.get("style"),
            "specificity": payload.get("specificity"),
            "reasoning_note": payload.get("reasoning_note"),
        }


def get_response_generator_provider(provider_name: str | None = None) -> ResponseGeneratorProvider:
    settings = get_settings()
    selected_provider = provider_name or settings.response_provider

    if selected_provider == "openai":
        return OpenAIResponseGeneratorProvider()
    if selected_provider == "gemini":
        return GeminiResponseGeneratorProvider()
    if settings.use_mock_response or selected_provider == "mock":
        return MockResponseGeneratorProvider()
    raise ProviderConfigurationError(f"Unsupported response provider: {selected_provider}")


def get_response_provider_name(provider_name: str | None = None) -> str:
    settings = get_settings()
    selected_provider = provider_name or settings.response_provider
    if selected_provider == "openai":
        return "openai"
    if selected_provider == "gemini":
        return "gemini"
    if settings.use_mock_response or selected_provider == "mock":
        return "mock"
    return selected_provider


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
) -> dict[str, object]:
    quote = None
    if risk_level in {"high", "medium"}:
        empathetic_response = generate_safe_support_message(risk_level)
        gentle_suggestion = None
    else:
        provider = get_response_generator_provider(provider_override)
        provider_payload = provider.generate(
            transcript=transcript,
            emotion_analysis=emotion_analysis,
            topic_tags=topic_tags,
            response_plan=response_plan,
        )
        empathetic_response = str(provider_payload["empathetic_response"]).strip()
        suggestion_value = provider_payload.get("gentle_suggestion")
        gentle_suggestion = str(suggestion_value).strip() if isinstance(suggestion_value, str) and suggestion_value.strip() else None
        if bool(response_plan["quote_allowed"]):
            quote = select_quote(
                quote_opt_in=quote_opt_in,
                latest_emotion_label=str(emotion_analysis["emotion_label"]),
                latest_risk_level=risk_level,
                user_id=user_id,
            )
    return {
        "empathetic_response": empathetic_response,
        "gentle_suggestion": gentle_suggestion,
        "quote": quote,
        "ai_response": _compose_legacy_response(empathetic_response, gentle_suggestion, quote),
        "provider_name": get_response_provider_name(provider_override),
    }


def generate_supportive_response(
    *,
    transcript: str,
    emotion_analysis: dict[str, object],
    topic_tags: list[str],
    risk_level: str,
    response_plan: dict[str, object],
    user_id: str,
    quote_opt_in: bool = True,
) -> dict[str, object]:
    payload = render_supportive_response(
        transcript=transcript,
        emotion_analysis=emotion_analysis,
        topic_tags=topic_tags,
        risk_level=risk_level,
        response_plan=response_plan,
        user_id=user_id,
        quote_opt_in=quote_opt_in,
    )
    return {
        "empathetic_response": str(payload["empathetic_response"]),
        "gentle_suggestion": payload["gentle_suggestion"],
        "quote": payload["quote"],
        "ai_response": str(payload["ai_response"]),
    }


def generate_empathetic_response(
    transcript: str,
    emotion_label: str,
    topic_tags: list[str],
) -> str:
    provider = get_response_generator_provider()
    payload = provider.generate(
        transcript=transcript,
        emotion_analysis={"emotion_label": emotion_label, "response_mode": "supportive_reflective", "stress_score": 0.0},
        topic_tags=topic_tags,
        response_plan={
            "suggestion_allowed": False,
            "suggestion_style": "none",
            "quote_allowed": False,
        },
    )
    return str(payload["empathetic_response"])
