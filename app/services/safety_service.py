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
            "Mình rất lưu ý đến mức độ nghiêm trọng trong điều bạn vừa nói. "
            "Ngay lúc này, hãy ưu tiên ở gần một người bạn tin tưởng hoặc liên hệ dịch vụ hỗ trợ khẩn cấp tại nơi bạn đang ở."
        )
    if risk_level == "medium":
        return (
            "Nghe như bạn đang ở trong một khoảng rất khó khăn. "
            "Nếu có thể, hãy tìm một người đáng tin để ở cùng hoặc lắng nghe bạn trong lúc này."
        )
    return ""
