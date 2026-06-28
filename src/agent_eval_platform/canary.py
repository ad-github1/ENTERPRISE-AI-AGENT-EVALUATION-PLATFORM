from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from agent_eval_platform.data_models import QualityGateConfig, SuiteResult
from agent_eval_platform.gates import evaluate_quality_gate


@dataclass(frozen=True, slots=True)
class CanaryConfig:
    service_name: str
    baseline_version: str
    candidate_version: str
    traffic_percent: float
    minimum_eval_cases: int
    promotion_gate: QualityGateConfig


@dataclass(frozen=True, slots=True)
class CanaryDecision:
    action: str
    reasons: tuple[str, ...]
    next_traffic_percent: float


def load_canary_config(path: str | Path) -> CanaryConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return CanaryConfig(
        service_name=payload["service_name"],
        baseline_version=payload["baseline_version"],
        candidate_version=payload["candidate_version"],
        traffic_percent=float(payload["traffic_percent"]),
        minimum_eval_cases=int(payload["minimum_eval_cases"]),
        promotion_gate=QualityGateConfig(**payload.get("promotion_gate", {})),
    )


def decide_canary(result: SuiteResult, config: CanaryConfig) -> CanaryDecision:
    reasons: list[str] = []
    if result.total_cases < config.minimum_eval_cases:
        reasons.append(f"only {result.total_cases} eval cases, need {config.minimum_eval_cases}")

    gate = evaluate_quality_gate(result, config.promotion_gate)
    reasons.extend(gate.violations)

    if reasons:
        return CanaryDecision(action="hold", reasons=tuple(reasons), next_traffic_percent=config.traffic_percent)

    next_traffic = min(100.0, max(config.traffic_percent * 2, 10.0))
    action = "promote" if next_traffic >= 100.0 else "increase_traffic"
    return CanaryDecision(action=action, reasons=("quality gate passed",), next_traffic_percent=next_traffic)
