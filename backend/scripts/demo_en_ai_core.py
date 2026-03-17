import argparse
import json
from pathlib import Path

from app.services.en_demo_service import build_en_demo_payload


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "en_ai_core_demo.md"

DEMO_CASES = [
    {
        "title": "Work stress / deadline",
        "context_tag": "work/school",
        "text": "I have been carrying too many deadlines at once, and my brain has felt packed tight all day.",
    },
    {
        "title": "Loneliness / left behind",
        "context_tag": "loneliness",
        "text": "I keep seeing everyone move forward with their lives, and I feel strangely left behind and hard to reach.",
    },
    {
        "title": "Relief / gratitude",
        "context_tag": "gratitude/achievement",
        "text": "A small kindness landed at exactly the right moment today, and I feel genuinely grateful for it.",
    },
    {
        "title": "Low energy / exhausted mood",
        "context_tag": "health",
        "text": "I am not intensely sad, just deeply tired and low on battery. Everything feels slower than it should.",
    },
    {
        "title": "Mixed emotion / nervous but hopeful",
        "context_tag": "daily life",
        "text": "I start something new tomorrow, so I feel nervous and hopeful at the same time.",
    },
]

REGRESSION_CASES = [
    {
        "title": "Relationship concern / short health update",
        "text": "My girlfriend is sick",
        "before": {
            "emotion": {
                "primary_emotion": "sadness",
                "response_mode": "low_energy_comfort",
                "provider_name": "visolex/phobert-emotion",
            },
            "support": {
                "provider_name": "template_fallback",
                "empathetic_response": "Your energy sounds really low around relationships. I want to acknowledge that tiredness without pushing you to feel different right away.",
            },
            "note": "Captured pre-fix failure mode from the English demo path.",
        },
    },
    {
        "title": "Recognition / appreciation",
        "text": "A friend told me I'd actually be good at helping people solve problems.",
        "before": {
            "emotion": {
                "primary_emotion": "anxiety",
                "response_mode": "supportive_reflective",
                "provider_name": "en_canonical_emotion+heuristic_fallback",
            },
            "support": {
                "provider_name": "template",
                "empathetic_response": "There is a real thread of worry here around friends. At the same time, it sounds like part of you is still trying to stay steady.",
            },
            "note": "Representative pre-fix output before the appreciation utterance-type rule was added.",
        },
    },
]


def render_markdown(
    results: list[tuple[dict[str, str], dict[str, object]]],
    regressions: list[tuple[dict[str, object], dict[str, object]]],
) -> str:
    lines = [
        "# English AI Core Demo",
        "",
        "Generated from the live English-first AI core demo service path.",
        "",
    ]
    for case, payload in results:
        lines.extend(
            [
                f"## {case['title']}",
                "",
                f"**Input**: {case['text']}",
                "",
                f"**Emotion provider path used**: `{payload['emotion']['provider_name']}`",
                f"**Support provider used**: `{payload['support']['provider_name']}`",
                "",
                "**Structured emotion output**",
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
    lines.extend(["## Regression Before/After", ""])
    for case, after_payload in regressions:
        lines.extend(
            [
                f"### {case['title']}",
                "",
                f"**Input**: {case['text']}",
                "",
                f"**Before note**: {case['before']['note']}",
                "",
                "**Before**",
                "",
                "```json",
                json.dumps(case["before"], ensure_ascii=False, indent=2),
                "```",
                "",
                "**After**",
                "",
                "```json",
                json.dumps(after_payload, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the English AI core demo cases.")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    results: list[tuple[dict[str, str], dict[str, object]]] = []
    for case in DEMO_CASES:
        payload = build_en_demo_payload(
            text=case["text"],
            user_name=None,
            context_tag=case["context_tag"],
        )
        results.append((case, payload.model_dump()))

    regressions: list[tuple[dict[str, object], dict[str, object]]] = []
    for case in REGRESSION_CASES:
        payload = build_en_demo_payload(text=str(case["text"]), user_name=None, context_tag=None)
        regressions.append((case, payload.model_dump()))

    if args.format == "json":
        print(
            json.dumps(
                {
                    "demo_cases": [payload for _, payload in results],
                    "regressions": [{"before": case["before"], "after": payload} for case, payload in regressions],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_markdown(results, regressions)
    output_path.write_text(content, encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
