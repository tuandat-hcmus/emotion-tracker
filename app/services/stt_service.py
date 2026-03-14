from pathlib import Path
from typing import Protocol

from app.core.config import get_settings
from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError


class SpeechToTextProvider(Protocol):
    def transcribe(self, audio_path: str) -> tuple[str, float]:
        ...


class MockSpeechToTextProvider:
    def transcribe(self, audio_path: str) -> tuple[str, float]:
        file_name = Path(audio_path).name
        transcript = f"Day check-in from file {file_name}. Hom nay minh thay hoi met nhung van dang co gang."
        return transcript, 0.78


class OpenAISpeechToTextProvider:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ProviderConfigurationError("STT provider 'openai' requires OPENAI_API_KEY")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderConfigurationError(
                "STT provider 'openai' requires the 'openai' package to be installed"
            ) from exc

        self._client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_request_timeout_seconds,
        )
        self._model = settings.openai_audio_model

    def transcribe(self, audio_path: str) -> tuple[str, float]:
        try:
            with open(audio_path, "rb") as audio_file:
                result = self._client.audio.transcriptions.create(
                    model=self._model,
                    file=audio_file,
                )
        except Exception as exc:
            raise ProviderExecutionError(f"OpenAI STT transcription failed: {exc}") from exc

        text = getattr(result, "text", None)
        if not text:
            raise ProviderExecutionError("OpenAI STT transcription returned empty text")
        return text, 0.95


def get_stt_provider() -> SpeechToTextProvider:
    settings = get_settings()

    if settings.stt_provider == "openai":
        return OpenAISpeechToTextProvider()
    if settings.use_mock_stt or settings.stt_provider == "mock":
        return MockSpeechToTextProvider()
    raise ProviderConfigurationError(f"Unsupported STT provider: {settings.stt_provider}")


def get_stt_provider_name(override_transcript: str | None = None) -> str:
    if override_transcript:
        return "override"

    settings = get_settings()
    if settings.stt_provider == "openai":
        return "openai"
    if settings.use_mock_stt or settings.stt_provider == "mock":
        return "mock"
    return settings.stt_provider


def transcribe_audio(audio_path: str) -> tuple[str, float]:
    provider = get_stt_provider()
    return provider.transcribe(audio_path)
