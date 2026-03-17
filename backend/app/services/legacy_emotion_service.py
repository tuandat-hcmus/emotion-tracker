from app.services.ai_core.canonical_schema import canonicalize_emotion
from app.services.ai_core.language_service import detect_language


def infer_legacy_emotion(text: str) -> dict[str, object]:
    normalized = text.casefold()
    language = detect_language(text)
    keyword_table = {
        "joy": ("vui", "hạnh phúc", "开心", "快乐"),
        "gratitude": ("biết ơn", "感激", "感谢"),
        "pride": ("tự hào", "自豪"),
        "calm": ("bình yên", "平静", "安心"),
        "relief": ("nhẹ nhõm", "释然"),
        "hope": ("hy vọng", "希望"),
        "sadness": ("buồn", "thất vọng", "难过", "伤心"),
        "loneliness": ("cô đơn", "một mình", "孤独", "寂寞"),
        "emptiness": ("trống rỗng", "空虚", "麻木"),
        "anxiety": ("lo lắng", "bất an", "焦虑", "担心"),
        "overwhelm": ("áp lực", "deadline", "压力", "压得"),
        "anger": ("bực", "ức chế", "生气", "愤怒"),
        "exhaustion": ("mệt", "kiệt sức", "疲惫", "很累"),
    }
    dimensions = {
        "joy": (0.7, 0.7, 0.15),
        "gratitude": (0.62, 0.42, 0.12),
        "pride": (0.66, 0.72, 0.18),
        "calm": (0.5, 0.2, 0.08),
        "relief": (0.44, 0.3, 0.16),
        "hope": (0.4, 0.48, 0.22),
        "sadness": (-0.55, 0.24, 0.34),
        "loneliness": (-0.62, 0.16, 0.44),
        "emptiness": (-0.72, 0.08, 0.36),
        "anxiety": (-0.4, 0.7, 0.76),
        "overwhelm": (-0.5, 0.78, 0.86),
        "anger": (-0.58, 0.76, 0.72),
        "exhaustion": (-0.34, 0.12, 0.46),
        "neutral": (0.0, 0.4, 0.18),
    }

    ranked: list[tuple[str, float]] = []
    for emotion, tokens in keyword_table.items():
        score = sum(0.25 for token in tokens if token in normalized)
        if score > 0:
            ranked.append((emotion, min(score, 1.0)))
    if not ranked:
        ranked = [("neutral", 0.35)]

    ranked.sort(key=lambda item: item[1], reverse=True)
    canonical_ranked: dict[str, float] = {}
    for emotion, score in ranked:
        canonical = canonicalize_emotion(emotion)
        canonical_ranked[canonical] = canonical_ranked.get(canonical, 0.0) + score
    ranked = sorted(canonical_ranked.items(), key=lambda item: item[1], reverse=True)
    total = sum(score for _, score in ranked) or 1.0
    valence = round(sum(dimensions.get(emotion, dimensions["neutral"])[0] * score for emotion, score in ranked) / total, 2)
    energy = round(sum(dimensions.get(emotion, dimensions["neutral"])[1] * score for emotion, score in ranked) / total, 2)
    stress = round(sum(dimensions.get(emotion, dimensions["neutral"])[2] * score for emotion, score in ranked) / total, 2)
    return {
        "language": language,
        "primary_emotion": ranked[0][0],
        "secondary_emotions": [emotion for emotion, _ in ranked[1:3]],
        "valence": valence,
        "energy": energy,
        "stress": stress,
        "confidence": round(ranked[0][1], 2),
        "source": "text",
        "raw_model_labels": [emotion for emotion, _ in ranked],
        "provider_name": "legacy_heuristic",
    }
