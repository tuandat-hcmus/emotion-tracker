def detect_safety_risk(transcript: str) -> dict[str, str | list[str]]:
    normalized = transcript.casefold()

    high_risk_patterns = [
        "muon chet",
        "muốn chết",
        "tu tu",
        "tự tử",
        "ket thuc cuoc song",
        "kết thúc cuộc sống",
        "khong muon song nua",
        "không muốn sống nữa",
        "giet ban than",
        "giết bản thân",
        "want to die",
        "kill myself",
        "end my life",
        "don't want to live anymore",
        "do not want to live anymore",
        "suicide",
    ]
    medium_risk_patterns = [
        "bien mat",
        "biến mất",
        "vo vong",
        "vô vọng",
        "khong con y nghia",
        "không còn ý nghĩa",
        "khong ai can minh",
        "không ai cần mình",
        "muon bo het",
        "muốn bỏ hết",
        "qua tuyet vong",
        "quá tuyệt vọng",
        "disappear",
        "hopeless",
        "nothing matters",
        "no one needs me",
        "give up on everything",
        "too hopeless",
    ]

    high_flags = [pattern for pattern in high_risk_patterns if pattern in normalized]
    if high_flags:
        return {"risk_level": "high", "risk_flags": high_flags}

    medium_flags = [pattern for pattern in medium_risk_patterns if pattern in normalized]
    if medium_flags:
        return {"risk_level": "medium", "risk_flags": medium_flags}

    return {"risk_level": "low", "risk_flags": []}


def generate_safe_support_message(risk_level: str) -> str:
    if risk_level == "high":
        return (
            "I'm taking the seriousness of what you just said seriously. "
            "Right now, please prioritize staying near someone you trust or contacting emergency support where you are."
        )
    if risk_level == "medium":
        return (
            "It sounds like you're in a very difficult place right now. "
            "If you can, please reach out to someone you trust to stay with you or listen right now."
        )
    return ""
