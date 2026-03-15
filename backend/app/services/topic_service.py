def tag_topics(transcript: str) -> list[str]:
    normalized = transcript.casefold()

    topic_rules: list[tuple[str, tuple[str, ...]]] = [
        ("công việc/học tập", ("cong viec", "công việc", "deadline", "hoc", "học", "thi", "du an", "dự án")),
        ("gia đình", ("gia dinh", "gia đình", "bo me", "bố mẹ", "cha me", "anh chi em")),
        ("tình cảm", ("yeu", "yêu", "nguoi yeu", "người yêu", "chia tay", "tinh cam", "tình cảm")),
        ("bạn bè", ("ban be", "bạn bè", "ban than", "bạn thân", "dong nghiep", "đồng nghiệp")),
        ("cô đơn", ("co don", "cô đơn", "lac long", "lạc lõng", "khong ai", "không ai")),
        ("sức khỏe", ("met", "mệt", "om", "ốm", "ngu", "ngủ", "suc khoe", "sức khỏe", "dau", "đau")),
        ("tự nghi ngờ", ("tu nghi ngo", "tự nghi ngờ", "khong du gioi", "không đủ giỏi", "tu ti", "tự ti")),
        ("biết ơn/thành tựu", ("biet on", "biết ơn", "thanh tuu", "thành tựu", "tu hao", "tự hào")),
        ("đời sống hằng ngày", ("hom nay", "hôm nay", "hang ngay", "hằng ngày", "sinh hoat", "sinh hoạt")),
    ]

    matches: list[str] = []
    for topic, keywords in topic_rules:
        if any(keyword in normalized for keyword in keywords):
            matches.append(topic)

    if not matches:
        return ["đời sống hằng ngày"]

    return matches[:3]
