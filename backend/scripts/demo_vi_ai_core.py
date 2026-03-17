import argparse
import json
from pathlib import Path

from app.services.vi_demo_service import build_vi_demo_payload


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "vi_ai_core_demo.md"

DEMO_CASES = [
    {
        "title": "Work stress / deadline",
        "context_tag": "công việc/học tập",
        "text": "Mấy hôm nay deadline dồn liên tục, đầu mình lúc nào cũng căng và cứ sợ làm không kịp. Mình thấy khó thở nhẹ mỗi khi mở laptop.",
    },
    {
        "title": "Loneliness / left behind",
        "context_tag": "cô đơn",
        "text": "Dạo này nhìn bạn bè ai cũng có nhịp sống riêng, còn mình cứ thấy lạc lõng và hơi bị bỏ lại phía sau. Mình không biết nên tâm sự với ai.",
    },
    {
        "title": "Relief / gratitude",
        "context_tag": "biết ơn/thành tựu",
        "text": "Hôm nay mình nhận được một lời động viên đúng lúc và tự nhiên thấy nhẹ cả người. Mình rất biết ơn vì ít nhất mọi thứ không còn nặng như mấy hôm trước.",
    },
    {
        "title": "Low energy / exhausted mood",
        "context_tag": "sức khỏe",
        "text": "Mình không hẳn buồn dữ dội, chỉ là mệt và cạn pin. Làm gì cũng thấy chậm, đầu óc hơi trống và mình chỉ muốn nằm im một lúc.",
    },
    {
        "title": "Mixed emotion / nervous but hopeful",
        "context_tag": "đời sống hằng ngày",
        "text": "Mai mình bắt đầu một việc mới nên vừa hồi hộp vừa có chút hy vọng. Mình sợ mình không đủ tốt, nhưng cũng thật lòng muốn thử tử tế với bản thân hơn.",
    },
]


def render_markdown(results: list[tuple[dict[str, str], dict[str, object]]]) -> str:
    lines = [
        "# Vietnamese AI Core Demo",
        "",
        "Generated from the live Vietnamese AI core demo service path.",
        "",
    ]
    for case, payload in results:
        lines.extend(
            [
                f"## {case['title']}",
                "",
                f"**Input**: {case['text']}",
                "",
                f"**Provider path used**: `{payload['emotion']['provider_name']}`",
                "",
                "**Normalized emotion output**",
                "",
                "```json",
                json.dumps(payload["emotion"], ensure_ascii=False, indent=2),
                "```",
                "",
                "**Supportive sharing output**",
                "",
                "```json",
                json.dumps(payload["support"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Vietnamese AI core demo cases.")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    results: list[tuple[dict[str, str], dict[str, object]]] = []
    for case in DEMO_CASES:
        payload = build_vi_demo_payload(
            text=case["text"],
            user_name=None,
            context_tag=case["context_tag"],
        )
        results.append((case, payload.model_dump()))

    if args.format == "json":
        print(json.dumps([payload for _, payload in results], ensure_ascii=False, indent=2))
        return

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_markdown(results)
    output_path.write_text(content, encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
