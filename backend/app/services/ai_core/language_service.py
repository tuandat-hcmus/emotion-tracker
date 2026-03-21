from functools import lru_cache
import re


_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_VI_MARKERS = (
    "ă",
    "â",
    "đ",
    "ê",
    "ô",
    "ơ",
    "ư",
    "ấ",
    "ầ",
    "ẩ",
    "ẫ",
    "ậ",
    "ắ",
    "ằ",
    "ẳ",
    "ẵ",
    "ặ",
    "ế",
    "ề",
    "ể",
    "ễ",
    "ệ",
    "ố",
    "ồ",
    "ổ",
    "ỗ",
    "ộ",
    "ớ",
    "ờ",
    "ở",
    "ỡ",
    "ợ",
    "ứ",
    "ừ",
    "ử",
    "ữ",
    "ự",
)
_SUPPORTED_LANGUAGE_CODES = {"en", "vi", "zh"}


@lru_cache(maxsize=1)
def _get_langdetect_detector():
    try:
        from langdetect import detect
    except ImportError:
        return None
    return detect


def normalize_language_code(language: str | None) -> str:
    normalized = (language or "").strip().casefold()
    if normalized.startswith("zh"):
        return "zh"
    if normalized == "vi":
        return "vi"
    if normalized == "en":
        return "en"
    return "en"


def detect_language(text: str) -> str:
    normalized = text.strip().casefold()
    if not normalized:
        return "en"
    if _CJK_RE.search(normalized):
        return "zh"
    if any(marker in normalized for marker in _VI_MARKERS):
        return "vi"

    detector = _get_langdetect_detector()
    if detector is not None:
        try:
            detected = detector(normalized)
        except Exception:
            detected = "en"
        normalized_detected = normalize_language_code(detected)
        if normalized_detected in _SUPPORTED_LANGUAGE_CODES:
            return normalized_detected
    return "en"
