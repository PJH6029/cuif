from __future__ import annotations

import argparse
import json
import sys

from .runner import evaluate_run, regenerate_report, run_task
from .schema import ManifestValidationError, validate_manifest
from .scoring import aggregate_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cuif-eval", description="CUIF PoC office artifact evaluator")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a task manifest")
    validate.add_argument("manifest")
    validate.add_argument("--skip-judges", action="store_true", help="relax live judge config validation")

    run = sub.add_parser("run", help="run adapter, evaluate, and report")
    run.add_argument("--task", required=True)
    run.add_argument("--adapter", default="mock", choices=["mock", "manual", "command"])
    run.add_argument("--out")
    run.add_argument("--invocation-mode", choices=["per_turn", "whole_task"], default="per_turn")
    run.add_argument("--skip-judges", action="store_true")
    run.add_argument("--judge-base-url")
    run.add_argument("--judge-model")
    run.add_argument("--judge-api-key-env", default="OPENAI_API_KEY")
    run.add_argument("--refresh-judge-cache", action="store_true")
    run.add_argument("--mock-outputs-dir", default="mock_outputs", help="fixture directory for mock adapter, relative to task")
    run.add_argument("--command", dest="command_template", help="command template for the command adapter; may use CUIF_* env var names as format keys")

    evaluate = sub.add_parser("evaluate", help="evaluate an existing run directory and generate reports")
    evaluate.add_argument("--task", required=True)
    evaluate.add_argument("--run", required=True)
    evaluate.add_argument("--skip-judges", action="store_true")
    evaluate.add_argument("--judge-base-url")
    evaluate.add_argument("--judge-model")
    evaluate.add_argument("--judge-api-key-env", default="OPENAI_API_KEY")
    evaluate.add_argument("--refresh-judge-cache", action="store_true")

    report = sub.add_parser("report", help="print existing report summary")
    report.add_argument("--run", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            manifest = validate_manifest(args.manifest, skip_judges=args.skip_judges)
            print(f"OK: {manifest.id} ({len(manifest.turns)} turns)")
            return 0
        if args.command == "run":
            result = run_task(
                args.task,
                adapter_name=args.adapter,
                out=args.out,
                invocation_mode=args.invocation_mode,
                skip_judges=args.skip_judges,
                judge_base_url=args.judge_base_url,
                judge_model=args.judge_model,
                judge_api_key_env=args.judge_api_key_env,
                refresh_judge_cache=args.refresh_judge_cache,
                adapter_config={"mock_outputs_dir": args.mock_outputs_dir, "command": args.command_template},
            )
            workspace = result["workspace"]
            summary = aggregate_results(result["results"]) if result["results"] else {"final_score": None}
            print(f"Run directory: {workspace.run_dir}")
            print(f"Adapter status: {result['adapter_result'].status}")
            if result["results"]:
                print(f"Final score: {summary['earned_points']:.2f}/{summary['possible_points']:.2f} ({summary['final_score']:.1%})")
            return 0 if result["adapter_result"].status in {"succeeded", "prepared"} else 2
        if args.command == "evaluate":
            result = evaluate_run(
                args.task,
                args.run,
                skip_judges=args.skip_judges,
                judge_base_url=args.judge_base_url,
                judge_model=args.judge_model,
                judge_api_key_env=args.judge_api_key_env,
                refresh_judge_cache=args.refresh_judge_cache,
            )
            summary = aggregate_results(result["results"])
            print(f"Report directory: {result['workspace'].run_dir}")
            print(f"Final score: {summary['earned_points']:.2f}/{summary['possible_points']:.2f} ({summary['final_score']:.1%})")
            return 0
        if args.command == "report":
            report = regenerate_report(args.run)
            print(json.dumps(report["summary"], indent=2, sort_keys=True))
            return 0
    except ManifestValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
