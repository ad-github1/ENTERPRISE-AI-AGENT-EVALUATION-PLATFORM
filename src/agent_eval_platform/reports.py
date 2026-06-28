from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_eval_platform.data_models import SuiteResult


@dataclass(frozen=True, slots=True)
class RegressionDelta:
    metric: str
    baseline: float
    candidate: float
    delta: float
    improved: bool


def write_markdown_report(result: SuiteResult, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown_report(result), encoding="utf-8")


def render_markdown_report(result: SuiteResult) -> str:
    aggregate = result.aggregate
    lines = [
        f"# Agent Evaluation Report: {result.variant}",
        "",
        f"- Suite: `{result.suite_name}`",
        f"- Generated: `{result.generated_at}`",
        f"- Cases: `{result.total_cases}`",
        f"- Gate: `{'PASS' if result.gate.passed else 'FAIL'}`",
        "",
        "## Aggregate Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Pass rate | {aggregate.pass_rate:.2%} |",
        f"| Avg faithfulness | {aggregate.avg_faithfulness:.3f} |",
        f"| Avg retrieval relevance | {aggregate.avg_retrieval_relevance:.3f} |",
        f"| Avg hallucination risk | {aggregate.avg_hallucination_risk:.3f} |",
        f"| p50 latency | {aggregate.p50_latency_ms:.1f} ms |",
        f"| p95 latency | {aggregate.p95_latency_ms:.1f} ms |",
        f"| p99 latency | {aggregate.p99_latency_ms:.1f} ms |",
        f"| Avg cost | ${aggregate.avg_cost_usd:.5f} |",
        f"| Total cost | ${aggregate.total_cost_usd:.4f} |",
        "",
        "## Gate Violations",
        "",
    ]
    if result.gate.violations:
        lines.extend(f"- {violation}" for violation in result.gate.violations)
    else:
        lines.append("- None")

    failed_cases = [case for case in result.case_results if not case.passed][:20]
    lines.extend(["", "## Failed Cases", ""])
    if not failed_cases:
        lines.append("- None")
    else:
        lines.extend(
            f"- `{case.case_id}`: {', '.join(case.violations)} "
            f"(faithfulness={case.metrics.faithfulness:.3f}, "
            f"retrieval={case.metrics.retrieval_relevance:.3f}, "
            f"hallucination={case.metrics.hallucination_risk:.3f})"
            for case in failed_cases
        )

    return "\n".join(lines) + "\n"


def regression_deltas(baseline: SuiteResult, candidate: SuiteResult) -> tuple[RegressionDelta, ...]:
    return (
        positive_delta("pass_rate", baseline.aggregate.pass_rate, candidate.aggregate.pass_rate),
        positive_delta("avg_faithfulness", baseline.aggregate.avg_faithfulness, candidate.aggregate.avg_faithfulness),
        positive_delta(
            "avg_retrieval_relevance",
            baseline.aggregate.avg_retrieval_relevance,
            candidate.aggregate.avg_retrieval_relevance,
        ),
        negative_delta(
            "avg_hallucination_risk",
            baseline.aggregate.avg_hallucination_risk,
            candidate.aggregate.avg_hallucination_risk,
        ),
        negative_delta("p95_latency_ms", baseline.aggregate.p95_latency_ms, candidate.aggregate.p95_latency_ms),
        negative_delta("p99_latency_ms", baseline.aggregate.p99_latency_ms, candidate.aggregate.p99_latency_ms),
        negative_delta("avg_cost_usd", baseline.aggregate.avg_cost_usd, candidate.aggregate.avg_cost_usd),
    )


def render_regression_report(baseline: SuiteResult, candidate: SuiteResult) -> str:
    deltas = regression_deltas(baseline, candidate)
    lines = [
        f"# Regression Report: {baseline.variant} -> {candidate.variant}",
        "",
        "| Metric | Baseline | Candidate | Delta | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for delta in deltas:
        status = "improved" if delta.improved else "regressed"
        lines.append(
            f"| {delta.metric} | {delta.baseline:.4f} | {delta.candidate:.4f} | "
            f"{delta.delta:+.4f} | {status} |"
        )
    return "\n".join(lines) + "\n"


def write_regression_report(baseline: SuiteResult, candidate: SuiteResult, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_regression_report(baseline, candidate), encoding="utf-8")


def positive_delta(metric: str, baseline: float, candidate: float) -> RegressionDelta:
    return RegressionDelta(metric=metric, baseline=baseline, candidate=candidate, delta=candidate - baseline, improved=candidate >= baseline)


def negative_delta(metric: str, baseline: float, candidate: float) -> RegressionDelta:
    return RegressionDelta(metric=metric, baseline=baseline, candidate=candidate, delta=candidate - baseline, improved=candidate <= baseline)
