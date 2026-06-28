from __future__ import annotations

from dataclasses import dataclass

from agent_eval_platform.data_models import QualityGateConfig, SuiteResult


@dataclass(frozen=True, slots=True)
class QualityGateDecision:
    passed: bool
    violations: tuple[str, ...]


def evaluate_quality_gate(result: SuiteResult, config: QualityGateConfig) -> QualityGateDecision:
    aggregate = result.aggregate
    violations: list[str] = []

    if aggregate.pass_rate < config.min_pass_rate:
        violations.append(f"pass_rate {aggregate.pass_rate:.3f} < {config.min_pass_rate:.3f}")
    if aggregate.avg_faithfulness < config.min_avg_faithfulness:
        violations.append(
            f"avg_faithfulness {aggregate.avg_faithfulness:.3f} < {config.min_avg_faithfulness:.3f}"
        )
    if aggregate.avg_retrieval_relevance < config.min_avg_retrieval_relevance:
        violations.append(
            "avg_retrieval_relevance "
            f"{aggregate.avg_retrieval_relevance:.3f} < {config.min_avg_retrieval_relevance:.3f}"
        )
    if aggregate.avg_hallucination_risk > config.max_avg_hallucination_risk:
        violations.append(
            "avg_hallucination_risk "
            f"{aggregate.avg_hallucination_risk:.3f} > {config.max_avg_hallucination_risk:.3f}"
        )
    if aggregate.p95_latency_ms > config.max_p95_latency_ms:
        violations.append(f"p95_latency_ms {aggregate.p95_latency_ms:.1f} > {config.max_p95_latency_ms:.1f}")
    if aggregate.p99_latency_ms > config.max_p99_latency_ms:
        violations.append(f"p99_latency_ms {aggregate.p99_latency_ms:.1f} > {config.max_p99_latency_ms:.1f}")
    if aggregate.avg_cost_usd > config.max_avg_cost_usd:
        violations.append(f"avg_cost_usd {aggregate.avg_cost_usd:.5f} > {config.max_avg_cost_usd:.5f}")

    return QualityGateDecision(passed=not violations, violations=tuple(violations))
