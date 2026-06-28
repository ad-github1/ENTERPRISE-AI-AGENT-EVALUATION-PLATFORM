from __future__ import annotations

from statistics import mean
from typing import Iterable

from agent_eval_platform.checks import score_faithfulness, score_hallucination_risk, score_retrieval_relevance
from agent_eval_platform.data_models import (
    AggregateMetrics,
    CaseEvaluation,
    CaseMetrics,
    EvalCase,
    GateReport,
    QualityGateConfig,
    SuiteResult,
    utc_now_iso,
)
from agent_eval_platform.gates import evaluate_quality_gate
from agent_eval_platform.telemetry import TelemetryRecorder


class EvaluationEngine:
    def __init__(self, gate_config: QualityGateConfig | None = None, telemetry: TelemetryRecorder | None = None) -> None:
        self.gate_config = gate_config or QualityGateConfig()
        self.telemetry = telemetry or TelemetryRecorder()

    def evaluate_case(self, case: EvalCase) -> CaseEvaluation:
        trace_id: str
        with self.telemetry.span("eval.case", case_id=case.case_id, question=case.question) as root:
            trace_id = root.trace_id
            with self.telemetry.span(
                "eval.faithfulness",
                trace_id=trace_id,
                parent_span_id=root.span_id,
                case_id=case.case_id,
            ) as span:
                faithfulness = score_faithfulness(case)
                span.add_event("score", value=faithfulness)

            with self.telemetry.span(
                "eval.retrieval_relevance",
                trace_id=trace_id,
                parent_span_id=root.span_id,
                case_id=case.case_id,
                retrieved_docs=len(case.retrieved_docs),
            ) as span:
                retrieval_relevance = score_retrieval_relevance(case)
                span.add_event("score", value=retrieval_relevance)

            with self.telemetry.span(
                "eval.hallucination_risk",
                trace_id=trace_id,
                parent_span_id=root.span_id,
                case_id=case.case_id,
            ) as span:
                hallucination_risk = score_hallucination_risk(case)
                span.add_event("score", value=hallucination_risk)

            metrics = CaseMetrics(
                faithfulness=faithfulness,
                retrieval_relevance=retrieval_relevance,
                hallucination_risk=hallucination_risk,
                latency_ms=case.latency_ms,
                cost_usd=case.cost_usd,
            )
            passed_checks, violations = self._case_gate(metrics)
            root.add_event("case_result", passed=not violations, violations=len(violations))

        return CaseEvaluation(
            case_id=case.case_id,
            question=case.question,
            metrics=metrics,
            passed=not violations,
            passed_checks=passed_checks,
            violations=tuple(violations),
            trace_id=trace_id,
        )

    def evaluate_suite(
        self,
        cases: Iterable[EvalCase],
        *,
        suite_name: str = "rag-wiki-quality",
        variant: str = "candidate",
    ) -> SuiteResult:
        case_results = tuple(self.evaluate_case(case) for case in cases)
        aggregate = aggregate_metrics(case_results)
        provisional = SuiteResult(
            suite_name=suite_name,
            variant=variant,
            generated_at=utc_now_iso(),
            total_cases=len(case_results),
            aggregate=aggregate,
            case_results=case_results,
            gate=GateReport(passed=True, violations=()),
        )
        gate_decision = evaluate_quality_gate(provisional, self.gate_config)
        return SuiteResult(
            suite_name=provisional.suite_name,
            variant=provisional.variant,
            generated_at=provisional.generated_at,
            total_cases=provisional.total_cases,
            aggregate=provisional.aggregate,
            case_results=provisional.case_results,
            gate=GateReport(passed=gate_decision.passed, violations=gate_decision.violations),
        )

    def _case_gate(self, metrics: CaseMetrics) -> tuple[dict[str, bool], list[str]]:
        config = self.gate_config
        checks = {
            "faithfulness": metrics.faithfulness >= config.min_case_faithfulness,
            "retrieval_relevance": metrics.retrieval_relevance >= config.min_case_retrieval_relevance,
            "hallucination_risk": metrics.hallucination_risk <= config.max_case_hallucination_risk,
            "latency": metrics.latency_ms <= config.max_case_latency_ms,
            "cost": metrics.cost_usd <= config.max_case_cost_usd,
        }
        violations = [name for name, passed in checks.items() if not passed]
        return checks, violations


def aggregate_metrics(results: tuple[CaseEvaluation, ...]) -> AggregateMetrics:
    if not results:
        return AggregateMetrics(
            pass_rate=0.0,
            avg_faithfulness=0.0,
            avg_retrieval_relevance=0.0,
            avg_hallucination_risk=0.0,
            p50_latency_ms=0.0,
            p95_latency_ms=0.0,
            p99_latency_ms=0.0,
            avg_cost_usd=0.0,
            total_cost_usd=0.0,
        )

    latencies = [result.metrics.latency_ms for result in results]
    costs = [result.metrics.cost_usd for result in results]
    return AggregateMetrics(
        pass_rate=sum(1 for result in results if result.passed) / len(results),
        avg_faithfulness=mean(result.metrics.faithfulness for result in results),
        avg_retrieval_relevance=mean(result.metrics.retrieval_relevance for result in results),
        avg_hallucination_risk=mean(result.metrics.hallucination_risk for result in results),
        p50_latency_ms=percentile(latencies, 50),
        p95_latency_ms=percentile(latencies, 95),
        p99_latency_ms=percentile(latencies, 99),
        avg_cost_usd=mean(costs),
        total_cost_usd=sum(costs),
    )


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    if percentile_value <= 0:
        return sorted_values[0]
    if percentile_value >= 100:
        return sorted_values[-1]
    rank = (len(sorted_values) - 1) * (percentile_value / 100)
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
