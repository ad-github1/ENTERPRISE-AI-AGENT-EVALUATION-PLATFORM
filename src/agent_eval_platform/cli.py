from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from agent_eval_platform.canary import decide_canary, load_canary_config
from agent_eval_platform.evaluator import EvaluationEngine
from agent_eval_platform.io_utils import load_cases, load_gate_config, load_suite_result, write_cases, write_json
from agent_eval_platform.reports import write_markdown_report, write_regression_report
from agent_eval_platform.synthetic import generate_cases


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate RAG/wiki AI agent quality gates.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate-cases", help="Generate synthetic RAG/wiki eval cases.")
    generate.add_argument("--count", type=int, default=120)
    generate.add_argument("--seed", type=int, default=11)
    generate.add_argument("--out", default="examples/wiki_eval_cases.jsonl")

    evaluate = subparsers.add_parser("evaluate", help="Evaluate a case suite and write reports.")
    evaluate.add_argument("--cases", required=True)
    evaluate.add_argument("--gate", default=None)
    evaluate.add_argument("--variant", default="candidate")
    evaluate.add_argument("--suite-name", default="rag-wiki-quality")
    evaluate.add_argument("--json-out", default="reports/eval_result.json")
    evaluate.add_argument("--markdown-out", default="reports/eval_report.md")
    evaluate.add_argument("--traces-out", default="reports/traces.jsonl")
    evaluate.add_argument("--fail-on-gate", action="store_true")

    compare = subparsers.add_parser("compare", help="Generate a regression report.")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--out", default="reports/regression_report.md")

    canary = subparsers.add_parser("canary", help="Evaluate canary promotion policy.")
    canary.add_argument("--result", required=True)
    canary.add_argument("--config", required=True)
    canary.add_argument("--json-out", default="reports/canary_decision.json")

    subparsers.add_parser("serve-mcp", help="Run the stdio MCP-style tool server.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "generate-cases":
        cases = generate_cases(args.count, seed=args.seed)
        write_cases(args.out, cases)
        print(f"wrote {len(cases)} cases to {args.out}")
        return

    if args.command == "evaluate":
        gate = load_gate_config(args.gate)
        engine = EvaluationEngine(gate)
        result = engine.evaluate_suite(load_cases(args.cases), suite_name=args.suite_name, variant=args.variant)
        write_json(args.json_out, result)
        write_markdown_report(result, args.markdown_out)
        engine.telemetry.export_jsonl(args.traces_out)
        print(f"gate={'PASS' if result.gate.passed else 'FAIL'} cases={result.total_cases} pass_rate={result.aggregate.pass_rate:.2%}")
        print(f"json={args.json_out}")
        print(f"report={args.markdown_out}")
        print(f"traces={args.traces_out}")
        if args.fail_on_gate and not result.gate.passed:
            sys.exit(1)
        return

    if args.command == "compare":
        baseline = load_suite_result(args.baseline)
        candidate = load_suite_result(args.candidate)
        write_regression_report(baseline, candidate, args.out)
        print(f"regression report={args.out}")
        return

    if args.command == "canary":
        result = load_suite_result(args.result)
        config = load_canary_config(args.config)
        decision = decide_canary(result, config)
        write_json(args.json_out, asdict(decision))
        print(f"canary action={decision.action} next_traffic={decision.next_traffic_percent:.1f}%")
        if decision.reasons:
            print("reasons=" + "; ".join(decision.reasons))
        return

    if args.command == "serve-mcp":
        from agent_eval_platform.mcp_server import run_server

        run_server()
        return

    raise ValueError(f"unknown command {args.command}")


if __name__ == "__main__":
    main()
