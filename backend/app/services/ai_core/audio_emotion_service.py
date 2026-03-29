import logging
from functools import lru_cache
from pathlib import Path

from app.services.ai_core.canonical_schema import canonicalize_emotion
from app.services.ai_core.schemas import AudioEmotionResult

logger = logging.getLogger(__name__)

# SpeechBrain IEMOCAP short labels to plain English
_IEMOCAP_MAP = {"ang": "anger", "hap": "joy", "neu": "neutral", "sad": "sadness"}


class MockAudioEmotionProvider:
    def analyze(self, audio_path: str) -> AudioEmotionResult:
        ranked = [("neutral", 0.70), ("sadness", 0.15), ("joy", 0.10), ("anger", 0.05)]
        return AudioEmotionResult(
            provider_name="mock_audio",
            raw_model_labels=["neutral", "sadness", "joy", "anger"],
            ranked_emotions=ranked,
            confidence=0.70,
            source_metadata={"mode": "mock"},
        )


class SpeechBrainAudioEmotionProvider:
    def __init__(self, model_dir: str) -> None:
        self._model_dir = model_dir
        self._classifier = None

    def _load(self):
        if self._classifier is not None:
            return self._classifier
        try:
            from speechbrain.inference.interfaces import foreign_class
            self._classifier = foreign_class(
                source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
                pymodule_file="custom_interface.py",
                classname="CustomEncoderWav2vec2Classifier",
                savedir=self._model_dir,
            )
        except Exception as exc:
            logger.error("audio_emotion.speechbrain_load_error err=%s", exc)
            raise
        return self._classifier

    def analyze(self, audio_path: str) -> AudioEmotionResult:
        classifier = self._load()
        out_prob, score, _index, text_lab = classifier.classify_file(audio_path)
        raw_labels = ["ang", "hap", "neu", "sad"]
        probs = out_prob[0].tolist() if hasattr(out_prob[0], "tolist") else list(out_prob[0])
        canonical_scores: dict[str, float] = {}
        for raw_label, prob in zip(raw_labels, probs):
            canonical = canonicalize_emotion(_IEMOCAP_MAP.get(raw_label, raw_label))
            canonical_scores[canonical] = canonical_scores.get(canonical, 0.0) + float(prob)
        ranked = sorted(canonical_scores.items(), key=lambda x: x[1], reverse=True)
        return AudioEmotionResult(
            provider_name="speechbrain_iemocap",
            raw_model_labels=[label for label, _ in ranked],
            ranked_emotions=ranked,
            confidence=ranked[0][1] if ranked else 0.0,
            source_metadata={"iemocap_label": str(text_lab[0]) if text_lab else ""},
        )


@lru_cache(maxsize=1)
def _get_audio_provider():
    from app.core.config import get_settings
    settings = get_settings()
    if not getattr(settings, "audio_emotion_model_enabled", False):
        return MockAudioEmotionProvider()
    model_dir = getattr(settings, "audio_emotion_model_dir", "models/artifacts/audio_emotion_wav2vec2")
    return SpeechBrainAudioEmotionProvider(model_dir)


def infer_audio_emotion(audio_path: str) -> AudioEmotionResult:
    """Analyze an audio file for emotion using prosody features."""
    provider = _get_audio_provider()
    logger.info("audio_emotion.infer_start audio_file=%s", Path(audio_path).name)
    result = provider.analyze(audio_path)
    logger.info(
        "audio_emotion.infer_complete provider=%s label=%s confidence=%s",
        result.provider_name,
        result.ranked_emotions[0][0] if result.ranked_emotions else "?",
        result.confidence,
    )
    return result
