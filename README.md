# Enterprise AI Agent Evaluation & Deployment Platform

A dependency-light evaluation platform for RAG/wiki-quality AI agents. It scores agent outputs for faithfulness, retrieval relevance, hallucination risk, latency, and cost; produces CI-friendly quality gates; emits regression/canary reports; and exposes the workflow through a lightweight MCP-style stdio tool server.

## What Is Included

- JSONL evaluation case format for RAG/wiki workflows.
- Deterministic checks for:
  - faithfulness to retrieved context and reference answer,
  - retrieval relevance against question and expected keywords,
  - hallucination risk from unsupported answer content,
  - latency and cost thresholds.
- 100+ synthetic case generator.
- CI/CD-style suite-level and case-level quality gates.
- Markdown and JSON evaluation reports.
- Regression report comparing baseline and candidate runs.
- Canary promotion policy with traffic ramp decisions.
- OpenTelemetry-compatible JSONL traces/metrics.
- MCP-style stdio server exposing evaluation tools.

## Quick Start

```bash
git clone https://github.com/ad-github1/ENTERPRISE-AI-AGENT-EVALUATION-PLATFORM.git
cd ENTERPRISE-AI-AGENT-EVALUATION-PLATFORM
PYTHONPATH=src python3 -m agent_eval_platform generate-cases --count 120 --out examples/wiki_eval_cases.jsonl
PYTHONPATH=src python3 -m agent_eval_platform evaluate \
  --cases examples/wiki_eval_cases.jsonl \
  --gate examples/quality_gate.json \
  --variant candidate \
  --json-out reports/eval_result.json \
  --markdown-out reports/eval_report.md \
  --traces-out reports/traces.jsonl
PYTHONPATH=src python3 -m unittest discover -s tests
```
## Testing

```bash
PYTHONPATH=src python3 -m unittest discover -s tests

Current local result:

Ran 5 tests in 0.015s

OK

After installation:

```bash
pip install -e .
agent-eval evaluate --cases examples/wiki_eval_cases.jsonl --gate examples/quality_gate.json
agent-eval-mcp
```

## Case Format

Each JSONL row contains one evaluated agent run:

```json
{
  "case_id": "case-0001",
  "question": "What contribution is Ada Lovelace known for in mathematics?",
  "reference_answer": "Ada Lovelace is known for Analytical Engine notes.",
  "expected_keywords": ["Ada Lovelace", "Analytical Engine"],
  "retrieved_docs": [
    {"doc_id": "wiki-1", "title": "Ada Lovelace", "text": "...", "score": 0.94}
  ],
  "agent_answer": "Ada Lovelace is known for Analytical Engine notes.",
  "latency_ms": 240.5,
  "cost_usd": 0.0031,
  "tags": ["wiki", "rag"]
}
```

## CI Quality Gate

The evaluator exits non-zero when `--fail-on-gate` is used and thresholds fail:

```bash
PYTHONPATH=src python3 -m agent_eval_platform evaluate \
  --cases examples/wiki_eval_cases.jsonl \
  --gate examples/quality_gate.json \
  --fail-on-gate
```

See `.github/workflows/agent-eval.yml` for a GitHub Actions example.

## MCP-Style Tool Server

Run:

```bash
PYTHONPATH=src python3 -m agent_eval_platform.mcp_server
```

Supported JSON-RPC methods:

- `initialize`
- `tools/list`
- `tools/call` with:
  - `run_evaluation_suite`
  - `compare_regression`
  - `decide_canary`

This is intentionally stdio and dependency-free. It follows the MCP tool shape closely enough for local agent integration demos without requiring the MCP Python SDK.

## Canary Workflow

```bash
PYTHONPATH=src python3 -m agent_eval_platform canary \
  --result reports/eval_result.json \
  --config examples/canary_config.json \
  --json-out reports/canary_decision.json
```

The decision is `hold`, `increase_traffic`, or `promote` based on suite quality and minimum case coverage.
