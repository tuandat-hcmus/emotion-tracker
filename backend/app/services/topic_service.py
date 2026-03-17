def tag_topics(transcript: str) -> list[str]:
    normalized = transcript.casefold()

    topic_rules: list[tuple[str, tuple[str, ...]]] = [
        ("work/school", ("cong viec", "công việc", "deadline", "hoc", "học", "thi", "du an", "dự án", "work", "school", "class", "exam", "project", "job")),
        ("family", ("gia dinh", "gia đình", "bo me", "bố mẹ", "cha me", "anh chi em", "family", "mom", "dad", "parents", "sister", "brother")),
        ("relationships", ("yeu", "yêu", "nguoi yeu", "người yêu", "chia tay", "tinh cam", "tình cảm", "boyfriend", "girlfriend", "partner", "relationship", "breakup")),
        ("friends", ("ban be", "bạn bè", "ban than", "bạn thân", "dong nghiep", "đồng nghiệp", "friend", "friends", "coworker", "colleague")),
        ("loneliness", ("co don", "cô đơn", "lac long", "lạc lõng", "khong ai", "không ai", "alone", "lonely", "left out", "isolated")),
        ("health", ("met", "mệt", "om", "ốm", "ngu", "ngủ", "suc khoe", "sức khỏe", "dau", "đau", "health", "sick", "tired", "sleep", "ill")),
        ("self-doubt", ("tu nghi ngo", "tự nghi ngờ", "khong du gioi", "không đủ giỏi", "tu ti", "tự ti", "not good enough", "self doubt", "insecure", "imposter")),
        ("gratitude/achievement", ("biet on", "biết ơn", "thanh tuu", "thành tựu", "tu hao", "tự hào", "grateful", "gratitude", "proud", "achievement")),
        ("daily life", ("hom nay", "hôm nay", "hang ngay", "hằng ngày", "sinh hoat", "sinh hoạt", "today", "daily", "routine", "lately")),
    ]

    matches: list[str] = []
    for topic, keywords in topic_rules:
        if any(keyword in normalized for keyword in keywords):
            matches.append(topic)

    if not matches:
        return ["daily life"]

    return matches[:3]
