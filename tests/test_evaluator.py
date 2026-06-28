import unittest

from agent_eval_platform.data_models import QualityGateConfig
from agent_eval_platform.evaluator import EvaluationEngine
from agent_eval_platform.synthetic import generate_cases


class EvaluatorTests(unittest.TestCase):
    def test_evaluates_100_plus_cases_with_metrics_and_traces(self) -> None:
        engine = EvaluationEngine(QualityGateConfig(min_pass_rate=0.70))
        result = engine.evaluate_suite(generate_cases(120, seed=5), variant="candidate")

        self.assertEqual(result.total_cases, 120)
        self.assertGreaterEqual(result.aggregate.pass_rate, 0.70)
        self.assertGreater(result.aggregate.avg_faithfulness, 0.70)
        self.assertGreater(result.aggregate.p95_latency_ms, result.aggregate.p50_latency_ms)
        self.assertGreater(len(engine.telemetry.spans), 120)

    def test_gate_reports_violations_for_strict_thresholds(self) -> None:
        engine = EvaluationEngine(QualityGateConfig(min_pass_rate=1.0, max_p95_latency_ms=100.0))
        result = engine.evaluate_suite(generate_cases(20, seed=6), variant="strict")

        self.assertFalse(result.gate.passed)
        self.assertGreater(len(result.gate.violations), 0)


if __name__ == "__main__":
    unittest.main()
