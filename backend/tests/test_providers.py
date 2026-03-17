from app.services.response_service import (
    MockResponseGeneratorProvider,
    get_response_generator_provider,
)
from app.services.stt_service import MockSpeechToTextProvider, get_stt_provider
from app.services.ai_core.text_emotion_service import infer_text_emotion


def test_mock_stt_provider_selected_by_default(monkeypatch, settings_factory) -> None:
    import app.services.stt_service as stt_service_module

    monkeypatch.setattr(stt_service_module, "get_settings", lambda: settings_factory(stt_provider="mock"))
    provider = get_stt_provider()

    assert isinstance(provider, MockSpeechToTextProvider)


def test_mock_response_provider_selected_by_default(monkeypatch, settings_factory) -> None:
    import app.services.response_service as response_service_module

    monkeypatch.setattr(
        response_service_module,
        "get_settings",
        lambda: settings_factory(response_provider="mock"),
    )
    provider = get_response_generator_provider()

    assert isinstance(provider, MockResponseGeneratorProvider)


def test_text_emotion_falls_back_cleanly_without_transformers(monkeypatch, settings_factory) -> None:
    import app.services.ai_core.text_emotion_service as text_service_module

    monkeypatch.setattr(text_service_module, "get_settings", lambda: settings_factory(enable_text_emotion=True))
    monkeypatch.setattr(
        text_service_module,
        "_infer_text_emotion_with_model",
        lambda _text, _language: (_ for _ in ()).throw(RuntimeError("no model runtime")),
    )

    result = infer_text_emotion("Mình hơi buồn và mệt.")

    assert result.provider_name == "heuristic_fallback"
    assert result.ranked_emotions
