from app.core.config import get_settings
from app.services.ai_core.model_registry import selected_audio_model
from app.services.ai_core.schemas import AudioEmotionResult


def infer_audio_emotion(audio_path: str | None) -> AudioEmotionResult | None:
    del audio_path
    settings = get_settings()
    if not settings.enable_audio_emotion:
        return None

    provider_name = settings.audio_emotion_provider.strip().lower()
    if provider_name in {"", "none", "disabled"}:
        return None

    spec = selected_audio_model()
    if spec is None:
        return None
    if spec.runtime_status != "direct_classifier":
        return None

    return None
