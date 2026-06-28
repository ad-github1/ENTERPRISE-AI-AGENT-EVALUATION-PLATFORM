import json
import unittest

from agent_eval_platform.canary import CanaryConfig, decide_canary
from agent_eval_platform.data_models import QualityGateConfig
from agent_eval_platform.evaluator import EvaluationEngine
from agent_eval_platform.mcp_server import handle_request
from agent_eval_platform.reports import render_markdown_report, render_regression_report
from agent_eval_platform.synthetic import generate_cases


class ReportsCanaryMcpTests(unittest.TestCase):
    def test_reports_and_canary_decision(self) -> None:
        engine = EvaluationEngine(QualityGateConfig(min_pass_rate=0.70))
        baseline = engine.evaluate_suite(generate_cases(30, seed=1), variant="baseline")
        candidate = engine.evaluate_suite(generate_cases(30, seed=2), variant="candidate")

        markdown = render_markdown_report(candidate)
        regression = render_regression_report(baseline, candidate)

        self.assertIn("Agent Evaluation Report", markdown)
        self.assertIn("Regression Report", regression)

        decision = decide_canary(
            candidate,
            CanaryConfig(
                service_name="wiki-agent",
                baseline_version="v1",
                candidate_version="v2",
                traffic_percent=10,
                minimum_eval_cases=20,
                promotion_gate=QualityGateConfig(min_pass_rate=0.70),
            ),
        )
        self.assertIn(decision.action, {"hold", "increase_traffic", "promote"})

    def test_mcp_lists_tools(self) -> None:
        response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        names = [tool["name"] for tool in response["result"]["tools"]]

        self.assertIn("run_evaluation_suite", names)
        self.assertIn("compare_regression", names)
        self.assertEqual(response["id"], 1)


if __name__ == "__main__":
    unittest.main()
