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


@lru_cache(maxsize=1)
def _get_langdetect_detector():
    try:
        from langdetect import detect
    except ImportError:
        return None
    return detect


def detect_language(text: str) -> str:
    normalized = text.strip().casefold()
    if not normalized:
        return "unknown"
    if _CJK_RE.search(normalized):
        return "zh"
    if any(marker in normalized for marker in _VI_MARKERS):
        return "vi"

    detector = _get_langdetect_detector()
    if detector is not None:
        try:
            detected = detector(normalized)
        except Exception:
            detected = "unknown"
        if detected.startswith("zh"):
            return "zh"
        if detected == "vi":
            return "vi"
        if detected and detected != "unknown":
            return detected
    return "en"
