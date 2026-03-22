import logging
from uuid import uuid4
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings
from app.services.provider_errors import ProviderConfigurationError, ProviderExecutionError

logger = logging.getLogger(__name__)


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
    provider_name = get_stt_provider_name()
    logger.info(
        "stt.transcribe_start provider=%s audio_file=%s",
        provider_name,
        Path(audio_path).name,
    )
    transcript, confidence = provider.transcribe(audio_path)
    logger.info(
        "stt.transcribe_complete provider=%s audio_file=%s transcript_chars=%s confidence=%s",
        provider_name,
        Path(audio_path).name,
        len(transcript),
        confidence,
    )
    return transcript, confidence


def build_partial_transcript(chunks: list[bytes]) -> str | None:
    if not chunks:
        return None
    provider_name = get_stt_provider_name()
    total_bytes = sum(len(chunk) for chunk in chunks)
    if provider_name == "mock":
        return f"Listening... {len(chunks)} chunks received."
    return f"Receiving audio... {total_bytes} bytes buffered."


def persist_stream_audio(
    chunks: list[bytes],
    uploads_dir: str,
    extension: str = ".webm",
) -> str:
    if not chunks:
        raise ProviderExecutionError("No audio chunks were received")
    suffix = extension if extension.startswith(".") else f".{extension}"
    audio_dir = Path(uploads_dir) / "conversations"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{uuid4()}{suffix}"
    audio_path.write_bytes(b"".join(chunks))
    return str(audio_path)


def transcribe_stream_audio(
    chunks: list[bytes],
    uploads_dir: str,
    extension: str = ".webm",
    text_fallback: str | None = None,
) -> tuple[str, float, str]:
    audio_path = persist_stream_audio(chunks, uploads_dir=uploads_dir, extension=extension)
    if text_fallback:
        logger.info("stt.stream_final_fallback audio_file=%s", Path(audio_path).name)
        return text_fallback.strip(), 1.0, audio_path
    transcript, confidence = transcribe_audio(audio_path)
    return transcript, confidence, audio_path
