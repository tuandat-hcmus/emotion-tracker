from app.services.ai_core.fusion_service import infer_emotion_signals
from app.services.ai_core.schemas import AudioEmotionResult, TextEmotionResult


def test_vietnamese_text_classification_path(monkeypatch) -> None:
    import app.services.ai_core.text_emotion_service as text_service_module

    monkeypatch.setattr(text_service_module, "detect_language", lambda _text: "vi")
    monkeypatch.setattr(
        text_service_module,
        "_infer_text_emotion_with_model",
        lambda _text, _language: TextEmotionResult(
            language="vi",
            provider_name="visolex/phobert-emotion",
            raw_model_labels=["joy"],
            ranked_emotions=[("joy", 0.91), ("calm", 0.36)],
            confidence=0.91,
            source_metadata={"mode": "test"},
        ),
    )

    result = text_service_module.infer_text_emotion("Hôm nay mình thấy rất vui.")

    assert result.language == "vi"
    assert result.provider_name == "visolex/phobert-emotion"
    assert result.ranked_emotions[0][0] == "joy"


def test_chinese_text_classification_path(monkeypatch) -> None:
    import app.services.ai_core.text_emotion_service as text_service_module

    monkeypatch.setattr(text_service_module, "detect_language", lambda _text: "zh")
    monkeypatch.setattr(
        text_service_module,
        "_infer_text_emotion_with_model",
        lambda _text, _language: TextEmotionResult(
            language="zh",
            provider_name="Johnson8187/Chinese-Emotion",
            raw_model_labels=["焦虑"],
            ranked_emotions=[("anxiety", 0.88), ("overwhelm", 0.33)],
            confidence=0.88,
            source_metadata={"mode": "test"},
        ),
    )

    result = text_service_module.infer_text_emotion("我最近很焦虑。")

    assert result.language == "zh"
    assert result.provider_name == "Johnson8187/Chinese-Emotion"
    assert result.ranked_emotions[0][0] == "anxiety"


def test_fallback_language_path(monkeypatch) -> None:
    import app.services.ai_core.text_emotion_service as text_service_module

    monkeypatch.setattr(text_service_module, "detect_language", lambda _text: "en")
    monkeypatch.setattr(
        text_service_module,
        "_infer_text_emotion_with_model",
        lambda _text, _language: TextEmotionResult(
            language="en",
            provider_name="cardiffnlp/twitter-xlm-roberta-base-sentiment",
            raw_model_labels=["negative"],
            ranked_emotions=[("sadness", 0.67), ("anxiety", 0.24)],
            confidence=0.67,
            source_metadata={"mode": "test"},
        ),
    )

    result = text_service_module.infer_text_emotion("I feel pretty low and tense.")

    assert result.language == "en"
    assert result.provider_name == "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    assert result.ranked_emotions[0][0] == "sadness"


def test_fusion_behavior_when_audio_provider_unavailable(monkeypatch) -> None:
    import app.services.ai_core.fusion_service as fusion_module

    monkeypatch.setattr(
        fusion_module,
        "infer_text_emotion",
        lambda _text: TextEmotionResult(
            language="vi",
            provider_name="visolex/phobert-emotion",
            raw_model_labels=["sadness"],
            ranked_emotions=[("sadness", 0.81), ("loneliness", 0.41)],
            confidence=0.81,
            source_metadata={"mode": "test"},
        ),
    )
    monkeypatch.setattr(fusion_module, "infer_audio_emotion", lambda _audio_path: None)

    result = infer_emotion_signals("Mình buồn và cô đơn.", audio_path="fake.wav")

    assert result.source == "text"
    assert result.primary_emotion == "sadness"
    assert result.provider_name == "visolex/phobert-emotion"
    assert result.source_metadata["audio"] is None


def test_fusion_behavior_with_audio_available(monkeypatch) -> None:
    import app.services.ai_core.fusion_service as fusion_module

    monkeypatch.setattr(
        fusion_module,
        "infer_text_emotion",
        lambda _text: TextEmotionResult(
            language="vi",
            provider_name="visolex/phobert-emotion",
            raw_model_labels=["sadness"],
            ranked_emotions=[("sadness", 0.72), ("loneliness", 0.4)],
            confidence=0.72,
            source_metadata={"mode": "test"},
        ),
    )
    monkeypatch.setattr(
        fusion_module,
        "infer_audio_emotion",
        lambda _audio_path: AudioEmotionResult(
            provider_name="audio-test",
            raw_model_labels=["sad"],
            ranked_emotions=[("exhaustion", 0.55), ("sadness", 0.3)],
            confidence=0.55,
            source_metadata={"mode": "test"},
        ),
    )

    result = infer_emotion_signals("Mình buồn.", audio_path="fake.wav")

    assert result.source == "fused"
    assert result.provider_name == "visolex/phobert-emotion+audio-test"
    assert result.primary_emotion in {"sadness", "exhaustion"}
