import argparse
import json

from app.services.ai_core.model_download import download_models, resolve_model_specs, supported_model_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        choices=["vi-public", "zh-public", "multilingual", "audio", "canonical"],
        help="Download one configured model group",
    )
    parser.add_argument("--all", action="store_true", help="Download all configured groups")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--respect-config", action="store_true", help="Resolve targets from current config")
    parser.add_argument("--list-supported", action="store_true", help="List supported models and runtime status")
    args = parser.parse_args()

    if args.list_supported:
        print(json.dumps(supported_model_rows(), ensure_ascii=False, indent=2))
        return

    selection = "all" if args.all or args.model is None else args.model
    specs = resolve_model_specs(selection, respect_config=args.respect_config)
    print("Model targets:")
    for key, spec in specs:
        print(
            f"- {key}: {spec.model_name} "
            f"(runtime_status={spec.runtime_status}, direct_inference={spec.direct_inference}, family={spec.family})"
        )
    statuses = download_models(specs, retries=args.retries)
    for status in statuses:
        print(
            f"[status] key={status.key} model={status.model_name} completed={status.completed} "
            f"runtime_status={status.runtime_status} snapshot={status.snapshot_path} "
            f"incomplete_files={len(status.incomplete_files)} message={status.message}"
        )


if __name__ == "__main__":
    main()
