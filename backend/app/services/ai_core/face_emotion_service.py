import logging
from functools import lru_cache

from app.services.ai_core.canonical_schema import canonicalize_emotion
from app.services.ai_core.schemas import AudioEmotionResult

logger = logging.getLogger(__name__)


class MockFaceEmotionProvider:
    def analyze(self, image_bytes: bytes) -> AudioEmotionResult | None:
        return None  # simulates no face detected


class DeepFaceFaceEmotionProvider:
    def analyze(self, image_bytes: bytes) -> AudioEmotionResult | None:
        try:
            import cv2
            import numpy as np
            from deepface import DeepFace
        except ImportError as exc:
            logger.error("face_emotion.import_error err=%s", exc)
            return None

        try:
            img_array = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            if img_array is None:
                return None

            result = DeepFace.analyze(
                img_path=img_array,
                actions=["emotion"],
                enforce_detection=True,
                detector_backend="opencv",
                silent=True,
            )
            # deepface returns a list; take the dominant face
            emotions: dict = result[0]["emotion"]
            # deepface gives percentages 0-100; normalize to 0-1 and map to canonical labels
            canonical_scores: dict[str, float] = {}
            for raw_label, pct in emotions.items():
                canonical = canonicalize_emotion(raw_label)
                canonical_scores[canonical] = canonical_scores.get(canonical, 0.0) + float(pct) / 100.0

            ranked = sorted(canonical_scores.items(), key=lambda x: x[1], reverse=True)
            return AudioEmotionResult(
                provider_name="deepface",
                raw_model_labels=[label for label, _ in ranked],
                ranked_emotions=ranked,
                confidence=ranked[0][1] if ranked else 0.0,
                source_metadata={"backend": "deepface/opencv"},
            )

        except ValueError:
            # deepface raises ValueError when no face is detected
            return None
        except Exception:
            logger.exception("face_emotion.deepface_error")
            return None


@lru_cache(maxsize=1)
def _get_face_provider():
    from app.core.config import get_settings
    settings = get_settings()
    if not getattr(settings, "face_emotion_enabled", False):
        return MockFaceEmotionProvider()
    provider_name = getattr(settings, "face_emotion_provider", "mock").lower()
    if provider_name == "deepface":
        return DeepFaceFaceEmotionProvider()
    return MockFaceEmotionProvider()


def infer_face_emotion_from_bytes(image_bytes: bytes) -> AudioEmotionResult | None:
    """Analyze a single JPEG image frame. Returns None if no face is detected."""
    provider = _get_face_provider()
    return provider.analyze(image_bytes)
