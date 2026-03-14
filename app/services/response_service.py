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
        response_mode = str(emotion_analysis["response_mode"])
        stress_score = float(emotion_analysis["stress_score"])
        acknowledgment_focus = str(response_plan.get("acknowledgment_focus", "mixed_state"))
        opening_style = str(response_plan.get("opening_style", "reflective"))

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


def get_response_generator_provider() -> ResponseGeneratorProvider:
    settings = get_settings()

    if settings.response_provider == "openai":
        return OpenAIResponseGeneratorProvider()
    if settings.use_mock_response or settings.response_provider == "mock":
        return MockResponseGeneratorProvider()
    raise ProviderConfigurationError(f"Unsupported response provider: {settings.response_provider}")


def get_response_provider_name() -> str:
    settings = get_settings()
    if settings.response_provider == "openai":
        return "openai"
    if settings.use_mock_response or settings.response_provider == "mock":
        return "mock"
    return settings.response_provider


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
    quote = None
    if risk_level in {"high", "medium"}:
        empathetic_response = generate_safe_support_message(risk_level)
        gentle_suggestion = None
    else:
        provider = get_response_generator_provider()
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
