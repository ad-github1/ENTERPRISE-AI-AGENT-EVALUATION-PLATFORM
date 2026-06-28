from __future__ import annotations

import json
import sys
from dataclasses import asdict
from typing import Any, Callable

from agent_eval_platform.canary import decide_canary, load_canary_config
from agent_eval_platform.evaluator import EvaluationEngine
from agent_eval_platform.io_utils import load_cases, load_gate_config, load_suite_result, to_jsonable, write_json
from agent_eval_platform.reports import write_markdown_report, write_regression_report


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


def tool_specs() -> list[dict[str, Any]]:
    return [
        {
            "name": "run_evaluation_suite",
            "description": "Run RAG/wiki agent evaluation cases and emit JSON, Markdown, and telemetry outputs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cases_path": {"type": "string"},
                    "gate_path": {"type": "string"},
                    "variant": {"type": "string"},
                    "json_out": {"type": "string"},
                    "markdown_out": {"type": "string"},
                    "traces_out": {"type": "string"},
                },
                "required": ["cases_path"],
            },
        },
        {
            "name": "compare_regression",
            "description": "Compare baseline and candidate suite JSON files.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "baseline_path": {"type": "string"},
                    "candidate_path": {"type": "string"},
                    "out": {"type": "string"},
                },
                "required": ["baseline_path", "candidate_path"],
            },
        },
        {
            "name": "decide_canary",
            "description": "Apply canary promotion policy to a suite result.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "result_path": {"type": "string"},
                    "config_path": {"type": "string"},
                },
                "required": ["result_path", "config_path"],
            },
        },
    ]


def run_evaluation_suite(args: dict[str, Any]) -> dict[str, Any]:
    gate_path = args.get("gate_path")
    engine = EvaluationEngine(load_gate_config(gate_path))
    result = engine.evaluate_suite(
        load_cases(args["cases_path"]),
        variant=args.get("variant", "candidate"),
    )
    json_out = args.get("json_out", "reports/mcp_eval_result.json")
    markdown_out = args.get("markdown_out", "reports/mcp_eval_report.md")
    traces_out = args.get("traces_out", "reports/mcp_traces.jsonl")
    write_json(json_out, result)
    write_markdown_report(result, markdown_out)
    engine.telemetry.export_jsonl(traces_out)
    return {
        "passed": result.gate.passed,
        "total_cases": result.total_cases,
        "pass_rate": result.aggregate.pass_rate,
        "json_out": json_out,
        "markdown_out": markdown_out,
        "traces_out": traces_out,
    }


def compare_regression(args: dict[str, Any]) -> dict[str, Any]:
    baseline = load_suite_result(args["baseline_path"])
    candidate = load_suite_result(args["candidate_path"])
    out = args.get("out", "reports/mcp_regression_report.md")
    write_regression_report(baseline, candidate, out)
    return {"report": out, "baseline": baseline.variant, "candidate": candidate.variant}


def decide_canary_tool(args: dict[str, Any]) -> dict[str, Any]:
    result = load_suite_result(args["result_path"])
    config = load_canary_config(args["config_path"])
    return asdict(decide_canary(result, config))


TOOLS: dict[str, ToolHandler] = {
    "run_evaluation_suite": run_evaluation_suite,
    "compare_regression": compare_regression,
    "decide_canary": decide_canary_tool,
}


def run_server() -> None:
    for request, framed in iter_requests(sys.stdin.buffer):
        try:
            response = handle_request(request)
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(exc)}}
        write_response(response, framed=framed)


def iter_requests(stream: Any) -> Any:
    while True:
        first = stream.readline()
        if not first:
            return
        stripped = first.strip()
        if not stripped:
            continue

        if stripped.lower().startswith(b"content-length:"):
            length = int(stripped.split(b":", 1)[1].strip())
            while True:
                header = stream.readline()
                if header in {b"\r\n", b"\n", b""}:
                    break
                if header.lower().startswith(b"content-length:"):
                    length = int(header.split(b":", 1)[1].strip())
            body = stream.read(length)
            yield json.loads(body.decode("utf-8")), True
            continue

        yield json.loads(stripped.decode("utf-8")), False


def write_response(response: dict[str, Any], *, framed: bool) -> None:
    payload = json.dumps(response).encode("utf-8")
    if framed:
        sys.stdout.buffer.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii"))
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()
        return
    sys.stdout.write(payload.decode("utf-8") + "\n")
    sys.stdout.flush()


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "agent-eval-platform", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tool_specs()}}

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if name not in TOOLS:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"unknown tool {name}"}}
        result = TOOLS[name](arguments)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"content": [{"type": "text", "text": json.dumps(to_jsonable(result), sort_keys=True)}]},
        }

    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"unknown method {method}"}}


def main() -> None:
    run_server()


if __name__ == "__main__":
    main()
