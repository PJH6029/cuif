from __future__ import annotations

import argparse
import json
import sys

from .agent_runners import DEFAULT_AGENT, DEFAULT_PROMPT_TEMPLATE, run_agent_on_bundle, run_and_evaluate_bundle
from .bundles import evaluate_bundle_outputs, export_task_bundle, stage_bundle_turn
from .runner import evaluate_run, regenerate_report, run_task
from .schema import ManifestValidationError, load_manifest, validate_manifest
from .scoring import aggregate_results, point_distribution


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
    run.add_argument("--judge-image-url-base", help="public URL base for run-local PNG previews when using openai-oauth VLM judges")
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
    evaluate.add_argument("--judge-image-url-base", help="public URL base for run-local PNG previews when using openai-oauth VLM judges")
    evaluate.add_argument("--refresh-judge-cache", action="store_true")

    export_bundle = sub.add_parser("export-bundle", help="export a task-facing workspace for an external agent")
    export_bundle.add_argument("--task", required=True)
    export_bundle.add_argument("--out", required=True)
    export_bundle.add_argument("--overwrite", action="store_true", help="replace an existing bundle directory")
    export_bundle.add_argument("--include-source-references", action="store_true", help="also expose package artifacts with role=source_reference")

    stage_bundle = sub.add_parser("stage-bundle-turn", help="reveal one turn instruction and newly declared inputs in an external-agent bundle")
    stage_bundle.add_argument("--bundle", required=True, help="bundle root or current/ workspace")
    stage_bundle.add_argument("--turn", required=True, help="turn id to reveal")

    evaluate_bundle = sub.add_parser("evaluate-bundle", help="import outputs from an external-agent workspace and evaluate them")
    evaluate_bundle.add_argument("--task", required=True)
    evaluate_bundle.add_argument("--workspace", required=True, help="bundle root or current/ workspace containing outputs/")
    evaluate_bundle.add_argument("--run", required=True, help="repo-side run directory to create/evaluate")
    evaluate_bundle.add_argument("--no-overwrite", action="store_true", help="fail if the run directory already exists")
    evaluate_bundle.add_argument("--skip-judges", action="store_true")
    evaluate_bundle.add_argument("--judge-base-url")
    evaluate_bundle.add_argument("--judge-model")
    evaluate_bundle.add_argument("--judge-api-key-env", default="OPENAI_API_KEY")
    evaluate_bundle.add_argument("--judge-image-url-base", help="public URL base for run-local PNG previews when using openai-oauth VLM judges")
    evaluate_bundle.add_argument("--refresh-judge-cache", action="store_true")

    run_agent = sub.add_parser("run-agent", help="run an agent across all turns of an already exported bundle")
    run_agent.add_argument("--bundle", required=True, help="bundle root or current/ workspace")
    run_agent.add_argument("--agent", default=DEFAULT_AGENT, help="agent runner to use")
    run_agent.add_argument("--agent-bin", help="agent executable override, if supported by the selected agent")
    run_agent.add_argument("--agent-arg", action="append", default=[], help="extra argument passed to the selected agent runner; repeat as needed")
    run_agent.add_argument("--prompt-template", default=DEFAULT_PROMPT_TEMPLATE, help="prompt template; supports {task_id}, {task_title}, {turn_id}, and {output_path}")

    run_and_evaluate = sub.add_parser("run-and-evaluate", help="export a bundle, run an agent across turns, then evaluate outputs")
    run_and_evaluate.add_argument("--task", required=True)
    run_and_evaluate.add_argument("--bundle", required=True, help="bundle root to create")
    run_and_evaluate.add_argument("--run", required=True, help="repo-side run directory to create/evaluate")
    run_and_evaluate.add_argument("--agent", default=DEFAULT_AGENT, help="agent runner to use")
    run_and_evaluate.add_argument("--agent-bin", help="agent executable override, if supported by the selected agent")
    run_and_evaluate.add_argument("--agent-arg", action="append", default=[], help="extra argument passed to the selected agent runner; repeat as needed")
    run_and_evaluate.add_argument("--prompt-template", default=DEFAULT_PROMPT_TEMPLATE, help="prompt template; supports {task_id}, {task_title}, {turn_id}, and {output_path}")
    run_and_evaluate.add_argument("--overwrite-bundle", action="store_true", help="replace an existing bundle directory")
    run_and_evaluate.add_argument("--no-overwrite-run", action="store_true", help="fail if the evaluation run directory already exists")
    run_and_evaluate.add_argument("--include-source-references", action="store_true", help="also expose package artifacts with role=source_reference")
    run_and_evaluate.add_argument("--skip-judges", action="store_true")
    run_and_evaluate.add_argument("--judge-base-url")
    run_and_evaluate.add_argument("--judge-model")
    run_and_evaluate.add_argument("--judge-api-key-env", default="OPENAI_API_KEY")
    run_and_evaluate.add_argument("--judge-image-url-base", help="public URL base for run-local PNG previews when using openai-oauth VLM judges")
    run_and_evaluate.add_argument("--refresh-judge-cache", action="store_true")

    report = sub.add_parser("report", help="print existing report summary")
    report.add_argument("--run", required=True)

    distribution = sub.add_parser("point-distribution", help="summarize manifest point allocation by evaluator and thesis-heavy bucket")
    distribution.add_argument("manifest")
    distribution.add_argument("--threshold", type=float, default=0.60, help="minimum thesis-heavy share after excluded checks are removed")
    distribution.add_argument("--json", action="store_true", help="print machine-readable JSON")
    distribution.add_argument("--fail-below-threshold", action="store_true", help="exit 2 when thesis-heavy share is below threshold")
    distribution.add_argument("--require-live-judges", action="store_true", help="require live judge model/base_url config while loading manifest")
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
                judge_image_url_base=args.judge_image_url_base,
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
                judge_image_url_base=args.judge_image_url_base,
                refresh_judge_cache=args.refresh_judge_cache,
            )
            summary = aggregate_results(result["results"])
            print(f"Report directory: {result['workspace'].run_dir}")
            print(f"Final score: {summary['earned_points']:.2f}/{summary['possible_points']:.2f} ({summary['final_score']:.1%})")
            return 0
        if args.command == "export-bundle":
            result = export_task_bundle(
                args.task,
                args.out,
                overwrite=args.overwrite,
                include_source_references=args.include_source_references,
            )
            print(f"Bundle directory: {result['bundle_dir']}")
            print(f"Agent workspace: {result['current_dir']}")
            print(f"Active turn: {result['metadata']['active_turn']}")
            print("Expected outputs:")
            for output in result["metadata"]["outputs"]:
                print(f"- {output['path']}")
            return 0
        if args.command == "stage-bundle-turn":
            result = stage_bundle_turn(args.bundle, args.turn)
            print(f"Bundle directory: {result['bundle_dir']}")
            print(f"Agent workspace: {result['current_dir']}")
            print(f"Active turn: {result['turn']}")
            if result["copied_inputs"]:
                print("New inputs:")
                for artifact in result["copied_inputs"]:
                    print(f"- {artifact['workspace_path']}")
            else:
                print("New inputs: none")
            return 0
        if args.command == "evaluate-bundle":
            result = evaluate_bundle_outputs(
                args.task,
                args.workspace,
                args.run,
                overwrite=not args.no_overwrite,
                skip_judges=args.skip_judges,
                judge_base_url=args.judge_base_url,
                judge_model=args.judge_model,
                judge_api_key_env=args.judge_api_key_env,
                judge_image_url_base=args.judge_image_url_base,
                refresh_judge_cache=args.refresh_judge_cache,
            )
            summary = result["summary"]
            copied = len(result["imported"]["copied"])
            missing = len(result["imported"]["missing"])
            print(f"Run directory: {result['workspace'].run_dir}")
            print(f"Imported outputs: {copied} copied, {missing} missing")
            print(f"Final score: {summary['earned_points']:.2f}/{summary['possible_points']:.2f} ({summary['final_score']:.1%})")
            return 0
        if args.command == "run-agent":
            result = run_agent_on_bundle(
                args.bundle,
                agent=args.agent,
                agent_bin=args.agent_bin,
                agent_args=args.agent_arg,
                prompt_template=args.prompt_template,
            )
            print(f"Bundle directory: {result['bundle_dir']}")
            print(f"Agent workspace: {result['current_dir']}")
            print(f"Agent logs: {result['log_dir']}")
            print("Completed turns:")
            for turn in result["turns"]:
                print(f"- {turn['turn']}: exit {turn['returncode']}")
            return 0
        if args.command == "run-and-evaluate":
            result = run_and_evaluate_bundle(
                args.task,
                args.bundle,
                args.run,
                agent=args.agent,
                agent_bin=args.agent_bin,
                agent_args=args.agent_arg,
                prompt_template=args.prompt_template,
                overwrite_bundle=args.overwrite_bundle,
                overwrite_run=not args.no_overwrite_run,
                include_source_references=args.include_source_references,
                skip_judges=args.skip_judges,
                judge_base_url=args.judge_base_url,
                judge_model=args.judge_model,
                judge_api_key_env=args.judge_api_key_env,
                judge_image_url_base=args.judge_image_url_base,
                refresh_judge_cache=args.refresh_judge_cache,
            )
            summary = result["summary"]
            print(f"Bundle directory: {result['bundle']['bundle_dir']}")
            print(f"Agent workspace: {result['bundle']['current_dir']}")
            print(f"Run directory: {result['evaluation']['workspace'].run_dir}")
            print(f"Agent logs: {result['log_dir']}")
            print(f"Final score: {summary['earned_points']:.2f}/{summary['possible_points']:.2f} ({summary['final_score']:.1%})")
            return 0
        if args.command == "report":
            report = regenerate_report(args.run)
            print(json.dumps(report["summary"], indent=2, sort_keys=True))
            return 0
        if args.command == "point-distribution":
            manifest = load_manifest(args.manifest, skip_judges=not args.require_live_judges)
            distribution = point_distribution(manifest, threshold=args.threshold)
            if args.json:
                print(json.dumps(distribution, indent=2, sort_keys=True))
            else:
                print(f"Task: {manifest.id}")
                print(f"Thesis-heavy share: {distribution['thesis_heavy_points']:.2f}/{distribution['review_points']:.2f} ({distribution['thesis_heavy_share']:.1%})")
                print(f"Threshold: {distribution['threshold']:.1%}; meets threshold: {distribution['meets_threshold']}")
                print(f"Excluded points: {distribution['excluded_points']:.2f} (boilerplate + diagnostic previews)")
                print("Buckets:")
                for bucket, points in distribution["buckets"].items():
                    print(f"- {bucket}: {points:.2f}")
                print("Evaluators:")
                for evaluator, points in distribution["evaluators"].items():
                    print(f"- {evaluator}: {points:.2f}")
            return 2 if args.fail_below_threshold and not distribution["meets_threshold"] else 0
    except ManifestValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
