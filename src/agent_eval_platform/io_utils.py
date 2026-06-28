from __future__ import annotations

import json
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from typing import Any, Iterable

from agent_eval_platform.data_models import (
    AggregateMetrics,
    CaseEvaluation,
    CaseMetrics,
    EvalCase,
    GateReport,
    QualityGateConfig,
    RetrievedDocument,
    SuiteResult,
)


def load_cases(path: str | Path) -> tuple[EvalCase, ...]:
    cases: list[EvalCase] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            try:
                cases.append(case_from_dict(payload))
            except Exception as exc:
                raise ValueError(f"invalid eval case at {path}:{line_number}: {exc}") from exc
    return tuple(cases)


def write_cases(path: str | Path, cases: Iterable[EvalCase]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(to_jsonable(case), sort_keys=True) + "\n")


def load_gate_config(path: str | Path | None) -> QualityGateConfig:
    if path is None:
        return QualityGateConfig()
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = {field.name for field in fields(QualityGateConfig)}
    return QualityGateConfig(**{key: value for key, value in payload.items() if key in allowed})


def write_json(path: str | Path, payload: Any) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


def load_suite_result(path: str | Path) -> SuiteResult:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return suite_result_from_dict(payload)


def case_from_dict(payload: dict[str, Any]) -> EvalCase:
    docs = tuple(RetrievedDocument(**doc) for doc in payload.get("retrieved_docs", ()))
    return EvalCase(
        case_id=payload["case_id"],
        question=payload["question"],
        reference_answer=payload["reference_answer"],
        expected_keywords=tuple(payload.get("expected_keywords", ())),
        retrieved_docs=docs,
        agent_answer=payload["agent_answer"],
        latency_ms=float(payload["latency_ms"]),
        cost_usd=float(payload["cost_usd"]),
        tags=tuple(payload.get("tags", ())),
        metadata=dict(payload.get("metadata", {})),
    )


def suite_result_from_dict(payload: dict[str, Any]) -> SuiteResult:
    aggregate = AggregateMetrics(**payload["aggregate"])
    gate = GateReport(
        passed=bool(payload["gate"]["passed"]),
        violations=tuple(payload["gate"].get("violations", ())),
    )
    case_results = tuple(
        CaseEvaluation(
            case_id=item["case_id"],
            question=item["question"],
            metrics=CaseMetrics(**item["metrics"]),
            passed=bool(item["passed"]),
            passed_checks=dict(item["passed_checks"]),
            violations=tuple(item.get("violations", ())),
            trace_id=item["trace_id"],
        )
        for item in payload["case_results"]
    )
    return SuiteResult(
        suite_name=payload["suite_name"],
        variant=payload["variant"],
        generated_at=payload["generated_at"],
        total_cases=int(payload["total_cases"]),
        aggregate=aggregate,
        case_results=case_results,
        gate=gate,
    )


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return value
