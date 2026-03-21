import argparse
import json
from pathlib import Path

from app.services.en_demo_service import build_en_demo_payload_with_debug


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "en_ai_core_demo.md"

DEMO_CASES = [
    {
        "title": "Work stress / deadline",
        "context_tag": "work/school",
        "text": "I've had deadlines piling up for days.",
    },
    {
        "title": "Loved one sick",
        "context_tag": "relationships",
        "text": "My girlfriend is sick",
    },
    {
        "title": "Loneliness / left out",
        "context_tag": "loneliness",
        "text": "I keep feeling left out lately, like everyone already has their people.",
    },
    {
        "title": "Recognition / praise",
        "context_tag": "friendship",
        "text": "A friend told me I'd actually be good at helping people solve problems.",
    },
    {
        "title": "Responsibility / tension",
        "context_tag": "work/school",
        "text": "I let my teammate down and I keep replaying it.",
    },
    {
        "title": "Low energy / emotionally flat",
        "context_tag": "daily life",
        "text": "I feel weirdly empty today.",
    },
]

REGRESSION_CASES = [
    {
        "title": "Deadline stress",
        "text": "I've had deadlines piling up for days.",
        "before": {
            "support": {
                "provider_name": "template_fallback",
                "empathetic_response": "There is a lot of strain here around work. It sounds like part of you is still trying to stay steady.",
            },
            "note": "Representative pre-redesign output from the old abstract English renderer style.",
        },
    },
    {
        "title": "Loved one sick",
        "text": "My girlfriend is sick",
        "before": {
            "support": {
                "provider_name": "template_fallback",
                "empathetic_response": "Your energy sounds really low around relationships. I want to acknowledge that tiredness without pushing you to feel different right away.",
            },
            "note": "Captured pre-fix failure mode from the English demo path.",
        },
    },
    {
        "title": "Loneliness",
        "text": "I keep feeling left out lately, like everyone already has their people.",
        "before": {
            "support": {
                "provider_name": "template",
                "empathetic_response": "There are a few emotional layers moving together here around daily life. Nothing about that needs to be cleaned up too quickly.",
            },
            "note": "Representative pre-redesign loneliness output with generic abstraction.",
        },
    },
    {
        "title": "Recognition / praise",
        "text": "A friend told me I'd actually be good at helping people solve problems.",
        "before": {
            "support": {
                "provider_name": "template",
                "empathetic_response": "There is a real thread of worry here around friends. At the same time, it sounds like part of you is still trying to stay steady.",
            },
            "note": "Representative pre-fix output before recognition-specific rendering was added.",
        },
    },
    {
        "title": "Responsibility / tension",
        "text": "I let my teammate down and I keep replaying it.",
        "before": {
            "support": {
                "provider_name": "template",
                "empathetic_response": "There is a lot of strain in what you described around work. That reaction makes sense and does not need to be dismissed.",
            },
            "note": "Representative pre-redesign output that missed the responsibility tension event.",
        },
    },
    {
        "title": "Low-energy update",
        "text": "I feel weirdly empty today.",
        "before": {
            "support": {
                "provider_name": "template",
                "empathetic_response": "Your energy sounds really low around daily life. I want to acknowledge that tiredness without pushing you to feel different right away.",
            },
            "note": "Representative pre-redesign low-energy output with generic copy.",
        },
    },
]


def _pretty_debug(debug_payload: dict[str, object] | None) -> dict[str, object]:
    if not debug_payload:
        return {}
    return {
        "renderer_selected": debug_payload.get("renderer_selected"),
        "fallback_triggered": debug_payload.get("fallback_triggered"),
        "fallback_reason": debug_payload.get("fallback_reason"),
        "render_payload": debug_payload.get("render_payload"),
        "system_instruction": debug_payload.get("system_instruction"),
        "few_shots": debug_payload.get("few_shots"),
        "raw_renderer_output": debug_payload.get("raw_renderer_output"),
    }


def render_markdown(
    results: list[tuple[dict[str, str], dict[str, object], dict[str, object] | None]],
    regressions: list[tuple[dict[str, object], dict[str, object], dict[str, object] | None]],
) -> str:
    lines = [
        "# English AI Core Demo",
        "",
        "Generated from the live English-first AI core demo service path.",
        "",
        "## Product Rendering Notes",
        "",
        "- The renderer is grounded first in the user's exact text and event, then in structured emotion state.",
        "- Gemini is the preferred renderer for normal low-risk English demo cases.",
        "- Template fallback remains available only for provider failure, schema failure, or explicit safety override.",
        "",
    ]
    for case, payload, debug_payload in results:
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
                "**Debug snapshot**",
                "",
                "```json",
                json.dumps(_pretty_debug(debug_payload), ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    lines.extend(["## Regression Before/After", ""])
    for case, after_payload, debug_payload in regressions:
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
                "**After debug**",
                "",
                "```json",
                json.dumps(_pretty_debug(debug_payload), ensure_ascii=False, indent=2),
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

    results: list[tuple[dict[str, str], dict[str, object], dict[str, object] | None]] = []
    for case in DEMO_CASES:
        payload, debug_payload = build_en_demo_payload_with_debug(
            text=case["text"],
            user_name=None,
            context_tag=case["context_tag"],
        )
        results.append((case, payload.model_dump(), debug_payload))

    regressions: list[tuple[dict[str, object], dict[str, object], dict[str, object] | None]] = []
    for case in REGRESSION_CASES:
        payload, debug_payload = build_en_demo_payload_with_debug(
            text=str(case["text"]),
            user_name=None,
            context_tag=None,
        )
        regressions.append((case, payload.model_dump(), debug_payload))

    if args.format == "json":
        print(
            json.dumps(
                {
                    "demo_cases": [payload for _, payload, _ in results],
                    "regressions": [{"before": case["before"], "after": payload} for case, payload, _ in regressions],
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
