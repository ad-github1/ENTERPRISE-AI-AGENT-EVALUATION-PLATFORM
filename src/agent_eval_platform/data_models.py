from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class RetrievedDocument:
    doc_id: str
    title: str
    text: str
    score: float = 1.0


@dataclass(frozen=True, slots=True)
class EvalCase:
    case_id: str
    question: str
    reference_answer: str
    expected_keywords: tuple[str, ...]
    retrieved_docs: tuple[RetrievedDocument, ...]
    agent_answer: str
    latency_ms: float
    cost_usd: float
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CaseMetrics:
    faithfulness: float
    retrieval_relevance: float
    hallucination_risk: float
    latency_ms: float
    cost_usd: float


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
    case_id: str
    question: str
    metrics: CaseMetrics
    passed: bool
    passed_checks: dict[str, bool]
    violations: tuple[str, ...]
    trace_id: str


@dataclass(frozen=True, slots=True)
class AggregateMetrics:
    pass_rate: float
    avg_faithfulness: float
    avg_retrieval_relevance: float
    avg_hallucination_risk: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_cost_usd: float
    total_cost_usd: float


@dataclass(frozen=True, slots=True)
class QualityGateConfig:
    min_case_faithfulness: float = 0.72
    min_case_retrieval_relevance: float = 0.58
    max_case_hallucination_risk: float = 0.38
    max_case_latency_ms: float = 1200.0
    max_case_cost_usd: float = 0.025
    min_pass_rate: float = 0.90
    min_avg_faithfulness: float = 0.78
    min_avg_retrieval_relevance: float = 0.65
    max_avg_hallucination_risk: float = 0.30
    max_p95_latency_ms: float = 900.0
    max_p99_latency_ms: float = 1200.0
    max_avg_cost_usd: float = 0.015


@dataclass(frozen=True, slots=True)
class GateReport:
    passed: bool
    violations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SuiteResult:
    suite_name: str
    variant: str
    generated_at: str
    total_cases: int
    aggregate: AggregateMetrics
    case_results: tuple[CaseEvaluation, ...]
    gate: GateReport


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
