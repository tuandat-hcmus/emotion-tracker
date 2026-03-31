from app.services.ai_core.canonical_schema import canonicalize_emotion
from app.services.ai_core.language_service import detect_language


def infer_legacy_emotion(text: str) -> dict[str, object]:
    normalized = text.casefold()
    language = detect_language(text)
    keyword_table = {
        "joy": (
            # English
            "happy", "happiness", "joyful", "joyous", "great", "wonderful", "fantastic",
            "amazing", "awesome", "feel good", "feeling good", "so good", "really good",
            "excellent", "superb", "elated", "delighted", "thrilled", "cheerful", "glad",
            "excited", "ecstatic", "blessed", "grateful", "thankful", "love", "loved",
            "beautiful", "enjoy", "enjoying", "enjoyed", "laugh", "laughing", "smile",
            "smiling", "bright", "positive", "uplifted", "content", "pleased",
            # Vietnamese
            "vui", "hạnh phúc",
            # Chinese
            "开心", "快乐",
        ),
        "gratitude": (
            # English
            "grateful", "thankful", "appreciate", "appreciation", "blessed", "fortunate",
            "lucky", "thank you", "thanks", "owe",
            # Vietnamese
            "biết ơn",
            # Chinese
            "感激", "感谢",
        ),
        "pride": (
            # English
            "proud", "pride", "accomplished", "achievement", "achieved", "succeeded",
            "success", "confident", "confidence",
            # Vietnamese
            "tự hào",
            # Chinese
            "自豪",
        ),
        "calm": (
            # English
            "calm", "peaceful", "relaxed", "relaxing", "serene", "tranquil", "at peace",
            "at ease", "quiet", "still", "centered", "grounded", "mellow", "chill",
            # Vietnamese
            "bình yên",
            # Chinese
            "平静", "安心",
        ),
        "relief": (
            # English
            "relieved", "relief", "finally", "over now", "glad it's done", "thankfully",
            "phew", "exhale",
            # Vietnamese
            "nhẹ nhõm",
            # Chinese
            "释然",
        ),
        "hope": (
            # English
            "hopeful", "hope", "looking forward", "optimistic", "optimism", "excited about",
            "can't wait", "better tomorrow", "things will get better", "believing",
            # Vietnamese
            "hy vọng",
            # Chinese
            "希望",
        ),
        "sadness": (
            # English
            "sad", "sadness", "unhappy", "down", "depressed", "depression", "crying",
            "cried", "tears", "heartbroken", "broken", "hurt", "devastated", "gloomy",
            "miserable", "upset", "disappointed", "disappointment", "hopeless", "blue",
            "grief", "grieving", "mourn", "mourning", "miss", "missing", "lost",
            # Vietnamese
            "buồn", "thất vọng",
            # Chinese
            "难过", "伤心",
        ),
        "loneliness": (
            # English
            "lonely", "loneliness", "alone", "isolated", "isolation", "no one", "nobody",
            "by myself", "by yourself", "left out", "excluded", "disconnected", "empty inside",
            # Vietnamese
            "cô đơn", "một mình",
            # Chinese
            "孤独", "寂寞",
        ),
        "emptiness": (
            # English
            "empty", "emptiness", "numb", "numbness", "hollow", "void", "meaningless",
            "pointless", "nothing matters", "don't care", "don't feel",
            # Vietnamese
            "trống rỗng",
            # Chinese
            "空虚", "麻木",
        ),
        "anxiety": (
            # English
            "anxious", "anxiety", "nervous", "nervousness", "worried", "worry", "worrying",
            "scared", "fear", "afraid", "panic", "panicking", "uneasy", "restless",
            "overthinking", "overthink", "stressed", "stress", "tense", "tension",
            # Vietnamese
            "lo lắng", "bất an",
            # Chinese
            "焦虑", "担心",
        ),
        "overwhelm": (
            # English
            "overwhelmed", "overwhelm", "too much", "can't handle", "swamped", "drowning",
            "burned out", "burnout", "burnt out", "exhausting", "deadline", "pressure",
            "overloaded", "falling apart",
            # Vietnamese
            "áp lực",
            # Chinese
            "压力", "压得",
        ),
        "anger": (
            # English
            "angry", "anger", "mad", "furious", "frustrated", "frustration", "irritated",
            "irritating", "annoyed", "annoying", "rage", "hate", "hateful", "pissed",
            "fed up", "resentful", "resentment",
            # Vietnamese
            "bực", "ức chế",
            # Chinese
            "生气", "愤怒",
        ),
        "exhaustion": (
            # English
            "tired", "exhausted", "exhaustion", "drained", "worn out", "burned out",
            "no energy", "no motivation", "fatigue", "fatigued", "sleepy", "sleepless",
            "can't sleep", "insomnia",
            # Vietnamese
            "mệt", "kiệt sức",
            # Chinese
            "疲惫", "很累",
        ),
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
        "ranked_emotions": ranked,
        "provider_name": "legacy_heuristic",
    }
