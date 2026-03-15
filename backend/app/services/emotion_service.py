from typing import Any


def _clamp(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


_SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "sadness": [
        "buon",
        "buồn",
        "chan",
        "chán",
        "that vong",
        "thất vọng",
        "khoc",
        "khóc",
    ],
    "emptiness": [
        "trong rong",
        "trống rỗng",
        "te liet",
        "tê liệt",
        "vo cam",
        "vô cảm",
        "khong cam thay gi",
        "không cảm thấy gì",
    ],
    "loneliness": [
        "co don",
        "cô đơn",
        "lac long",
        "lạc lõng",
        "khong ai hieu",
        "không ai hiểu",
        "mot minh",
        "một mình",
    ],
    "anxiety": [
        "lo lang",
        "lo lắng",
        "bat an",
        "bất an",
        "hoang mang",
        "sot ruot",
        "sốt ruột",
    ],
    "overwhelm": [
        "ap luc",
        "áp lực",
        "deadline",
        "stress",
        "cang",
        "căng",
        "qua tai",
        "quá tải",
        "gon",
        "gồng",
        "ngop",
        "ngộp",
        "khong theo kip",
        "không theo kịp",
    ],
    "anger": [
        "tuc",
        "tức",
        "buc",
        "bực",
        "buc boi",
        "bực bội",
        "cáu",
        "phan no",
        "phẫn nộ",
        "uc che",
        "ức chế",
    ],
    "relief": [
        "nhe nhom",
        "nhẹ nhõm",
        "de tho",
        "dễ thở",
        "thoat khoi",
        "thoát khỏi",
        "do hon",
        "đỡ hơn",
    ],
    "hope": [
        "hy vong",
        "hy vọng",
        "con co the",
        "còn có thể",
        "van co cach",
        "vẫn có cách",
        "mong la",
        "mong là",
    ],
    "gratitude": [
        "biet on",
        "biết ơn",
        "cam kich",
        "cảm kích",
        "tran trong",
        "trân trọng",
    ],
    "joy": [
        "vui",
        "hanh phuc",
        "hạnh phúc",
        "phan khoi",
        "phấn khởi",
        "tot",
        "tốt",
    ],
    "pride": [
        "thanh tuu",
        "thành tựu",
        "tu hao",
        "tự hào",
        "lam duoc",
        "làm được",
        "vuot qua",
        "vượt qua",
    ],
    "calm": [
        "binh yen",
        "bình yên",
        "yen tam",
        "yên tâm",
        "on hon",
        "ổn hơn",
        "lang lai",
        "lắng lại",
    ],
    "exhaustion": [
        "met",
        "mệt",
        "kiet suc",
        "kiệt sức",
        "u oai",
        "uể oải",
        "thieu ngu",
        "thiếu ngủ",
        "khong co dong luc",
        "không có động lực",
        "duoi",
        "đuối",
    ],
    "avoidance": [
        "tron tranh",
        "trốn tránh",
        "ne tranh",
        "né tránh",
        "khong muon doi mat",
        "không muốn đối mặt",
        "muon bien mat",
        "muốn biến mất",
        "khong muon lam gi",
        "không muốn làm gì",
    ],
    "connection_need": [
        "can ai do",
        "cần ai đó",
        "muon noi chuyen",
        "muốn nói chuyện",
        "muon duoc lang nghe",
        "muốn được lắng nghe",
        "muon co nguoi o cung",
        "muốn có người ở cùng",
    ],
    "withdrawal": [
        "thu minh",
        "thu mình",
        "im lang",
        "im lặng",
        "khong muon gap ai",
        "không muốn gặp ai",
        "cat dut",
        "cắt đứt",
        "xa lanh",
        "xa lánh",
    ],
    "uncertainty": [
        "hinh nhu",
        "hình như",
        "co le",
        "có lẽ",
        "khong biet",
        "không biết",
        "chac la",
        "chắc là",
        "hơi",
    ],
    "intensity": [
        "rất",
        "quá",
        "cuc ky",
        "cực kỳ",
        "thuc su",
        "thực sự",
    ],
    "contrast": [
        "nhung",
        "nhưng",
        "dù",
        "vẫn",
        "vua",
        "vừa",
    ],
}


def _count_phrase_hits(normalized: str, keywords: list[str]) -> int:
    return sum(normalized.count(keyword) for keyword in keywords)


def _signal_hits(normalized: str) -> dict[str, int]:
    return {name: _count_phrase_hits(normalized, keywords) for name, keywords in _SIGNAL_KEYWORDS.items()}


def _build_dominant_signals(signal_hits: dict[str, int]) -> list[str]:
    signals_with_strength = [
        ("positive_affect", signal_hits["joy"] + signal_hits["gratitude"] + signal_hits["pride"] + signal_hits["calm"]),
        ("gratitude_warmth", signal_hits["gratitude"]),
        ("pride_growth", signal_hits["pride"]),
        ("relief_release", signal_hits["relief"]),
        ("hope_glimmer", signal_hits["hope"]),
        ("calm_steady", signal_hits["calm"]),
        ("sadness_weight", signal_hits["sadness"]),
        ("emptiness_numbness", signal_hits["emptiness"]),
        ("loneliness_pull", signal_hits["loneliness"]),
        ("stress_pressure", signal_hits["anxiety"] + signal_hits["overwhelm"]),
        ("anxiety_activation", signal_hits["anxiety"]),
        ("overwhelm_load", signal_hits["overwhelm"]),
        ("anger_friction", signal_hits["anger"]),
        ("exhaustion_drag", signal_hits["exhaustion"]),
        ("avoidance_loop", signal_hits["avoidance"]),
        ("connection_need", signal_hits["connection_need"] + signal_hits["withdrawal"]),
        ("uncertainty_hedging", signal_hits["uncertainty"]),
    ]
    ordered = [name for name, strength in signals_with_strength if strength > 0]
    positive_present = signal_hits["joy"] + signal_hits["gratitude"] + signal_hits["pride"] + signal_hits["calm"] + signal_hits["relief"] + signal_hits["hope"] > 0
    negative_present = (
        signal_hits["sadness"]
        + signal_hits["emptiness"]
        + signal_hits["loneliness"]
        + signal_hits["anxiety"]
        + signal_hits["overwhelm"]
        + signal_hits["anger"]
        + signal_hits["exhaustion"]
        > 0
    )
    if signal_hits["contrast"] > 0 and positive_present and negative_present:
        ordered.append("mixed_emotions")
    elif positive_present and negative_present:
        ordered.append("mixed_emotions")
    return ordered or ["subtle_signal"]


def _infer_response_mode(
    *,
    valence_score: float,
    energy_score: float,
    stress_score: float,
    risk_level: str,
    dominant_signals: list[str],
) -> str:
    dominant_signal_set = set(dominant_signals)
    if risk_level == "high":
        return "high_risk_safe"
    if risk_level == "medium" or stress_score >= 0.66 or "overwhelm_load" in dominant_signal_set:
        return "grounding_soft"
    if "mixed_emotions" in dominant_signal_set and (
        "positive_affect" in dominant_signal_set
        or "hope_glimmer" in dominant_signal_set
        or "relief_release" in dominant_signal_set
        or "gratitude_warmth" in dominant_signal_set
        or "pride_growth" in dominant_signal_set
    ):
        return "supportive_reflective"
    if (
        "pride_growth" in dominant_signal_set
        or "gratitude_warmth" in dominant_signal_set
        or "relief_release" in dominant_signal_set
        or "calm_steady" in dominant_signal_set
    ) and valence_score >= 0.22 and stress_score <= 0.34 and "mixed_emotions" not in dominant_signal_set:
        return "celebratory_warm"
    if valence_score >= 0.38 and stress_score <= 0.34 and "mixed_emotions" not in dominant_signal_set:
        return "celebratory_warm"
    if energy_score <= 0.28 and (
        valence_score <= -0.12
        or "loneliness_pull" in dominant_signal_set
        or "emptiness_numbness" in dominant_signal_set
        or "exhaustion_drag" in dominant_signal_set
    ):
        return "low_energy_comfort"
    if "loneliness_pull" in dominant_signal_set and valence_score <= -0.18 and energy_score <= 0.55:
        return "low_energy_comfort"
    if "mixed_emotions" in dominant_signal_set or "uncertainty_hedging" in dominant_signal_set:
        return "supportive_reflective"
    if valence_score <= -0.2 or "anger_friction" in dominant_signal_set:
        return "validating_gentle"
    return "supportive_reflective"


def _infer_emotion_label(
    *,
    valence_score: float,
    energy_score: float,
    stress_score: float,
    risk_level: str,
    dominant_signals: list[str],
) -> str:
    dominant_signal_set = set(dominant_signals)
    if risk_level == "high":
        return "nguy cơ cao"
    if "mixed_emotions" in dominant_signal_set and (
        "positive_affect" in dominant_signal_set or "hope_glimmer" in dominant_signal_set
        or "relief_release" in dominant_signal_set
        or "gratitude_warmth" in dominant_signal_set
        or "pride_growth" in dominant_signal_set
    ):
        return "phức hợp"
    if "emptiness_numbness" in dominant_signal_set and valence_score <= -0.22:
        return "trống rỗng"
    if "loneliness_pull" in dominant_signal_set and energy_score <= 0.48:
        return "cô đơn"
    if "anger_friction" in dominant_signal_set and stress_score >= 0.34:
        return "bực bội"
    if "overwhelm_load" in dominant_signal_set or stress_score >= 0.62:
        return "căng"
    if "relief_release" in dominant_signal_set and valence_score >= 0.2:
        return "nhẹ nhõm"
    if "gratitude_warmth" in dominant_signal_set and valence_score >= 0.24:
        return "biết ơn"
    if "pride_growth" in dominant_signal_set and valence_score >= 0.26:
        return "tự hào"
    if "calm_steady" in dominant_signal_set and stress_score <= 0.28:
        return "bình yên"
    if valence_score >= 0.45 and stress_score <= 0.38:
        return "tươi sáng"
    if energy_score <= 0.28 and valence_score <= -0.12:
        return "chùng xuống"
    if valence_score <= -0.28:
        return "nặng nề"
    return "bình thường"


def normalize_emotion_analysis(raw: dict[str, Any], risk_level: str) -> dict[str, object]:
    dominant_signals = [str(signal) for signal in raw.get("dominant_signals", [])]
    valence_score = round(float(raw.get("valence_score", 0.0)), 2)
    energy_score = round(float(raw.get("energy_score", 0.0)), 2)
    stress_score = round(float(raw.get("stress_score", 0.0)), 2)
    social_need_score = round(float(raw.get("social_need_score", 0.0)), 2)
    confidence = round(float(raw.get("confidence", 0.35)), 2)
    response_mode = str(
        raw.get(
            "response_mode",
            _infer_response_mode(
                valence_score=valence_score,
                energy_score=energy_score,
                stress_score=stress_score,
                risk_level=risk_level,
                dominant_signals=dominant_signals,
            ),
        )
    )
    label = str(
        raw.get(
            "emotion_label",
            raw.get(
                "label",
                _infer_emotion_label(
                    valence_score=valence_score,
                    energy_score=energy_score,
                    stress_score=stress_score,
                    risk_level=risk_level,
                    dominant_signals=dominant_signals,
                ),
            ),
        )
    )
    return {
        "label": label,
        "emotion_label": label,
        "valence_score": valence_score,
        "energy_score": energy_score,
        "stress_score": stress_score,
        "social_need_score": social_need_score,
        "confidence": confidence,
        "dominant_signals": dominant_signals,
        "response_mode": response_mode,
    }


def analyze_emotion(transcript: str, risk_level: str = "low") -> dict[str, object]:
    normalized = transcript.casefold()
    signal_hits = _signal_hits(normalized)

    positive_hits = (
        signal_hits["joy"]
        + signal_hits["gratitude"]
        + signal_hits["pride"]
        + signal_hits["calm"]
        + signal_hits["relief"]
        + signal_hits["hope"]
    )
    negative_hits = (
        signal_hits["sadness"]
        + signal_hits["emptiness"]
        + signal_hits["loneliness"]
        + signal_hits["anxiety"]
        + signal_hits["overwhelm"]
        + signal_hits["anger"]
        + signal_hits["exhaustion"]
    )

    valence_score = _clamp(
        positive_hits * 0.18
        + signal_hits["relief"] * 0.05
        + signal_hits["hope"] * 0.05
        - signal_hits["sadness"] * 0.16
        - signal_hits["emptiness"] * 0.22
        - signal_hits["loneliness"] * 0.18
        - signal_hits["anxiety"] * 0.1
        - signal_hits["overwhelm"] * 0.13
        - signal_hits["anger"] * 0.14
        - signal_hits["exhaustion"] * 0.12
        - signal_hits["avoidance"] * 0.08
    )
    energy_score = _clamp(
        0.44
        + signal_hits["joy"] * 0.09
        + signal_hits["pride"] * 0.08
        + signal_hits["anxiety"] * 0.04
        + signal_hits["overwhelm"] * 0.05
        + signal_hits["anger"] * 0.04
        - signal_hits["exhaustion"] * 0.22
        - signal_hits["emptiness"] * 0.18
        - signal_hits["avoidance"] * 0.09
        - signal_hits["sadness"] * 0.05,
        0.0,
        1.0,
    )
    stress_score = _clamp(
        signal_hits["anxiety"] * 0.2
        + signal_hits["overwhelm"] * 0.23
        + signal_hits["anger"] * 0.16
        + signal_hits["uncertainty"] * 0.04
        + signal_hits["intensity"] * (0.05 if negative_hits else 0.0)
        + (
            0.15
            if risk_level == "medium"
            else 0.28 if risk_level == "high" else 0.0
        ),
        0.0,
        1.0,
    )
    social_need_score = _clamp(
        signal_hits["loneliness"] * 0.2
        + signal_hits["connection_need"] * 0.24
        + signal_hits["withdrawal"] * 0.17
        + signal_hits["avoidance"] * 0.07
        + signal_hits["sadness"] * 0.04,
        0.0,
        1.0,
    )
    distinct_signal_count = sum(1 for name, value in signal_hits.items() if name not in {"intensity", "contrast"} and value > 0)
    confidence = _clamp(
        0.34
        + distinct_signal_count * 0.07
        + min(signal_hits["intensity"], 2) * 0.03
        - min(signal_hits["uncertainty"], 2) * 0.04,
        0.35,
        0.98,
    )
    dominant_signals = _build_dominant_signals(signal_hits)

    return normalize_emotion_analysis(
        {
            "valence_score": valence_score,
            "energy_score": energy_score,
            "stress_score": stress_score,
            "social_need_score": social_need_score,
            "confidence": confidence,
            "dominant_signals": dominant_signals,
        },
        risk_level=risk_level,
    )
