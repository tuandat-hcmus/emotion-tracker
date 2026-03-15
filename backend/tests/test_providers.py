from app.services.response_service import (
    MockResponseGeneratorProvider,
    get_response_generator_provider,
)
from app.services.stt_service import MockSpeechToTextProvider, get_stt_provider


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
