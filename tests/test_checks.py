import unittest

from agent_eval_platform.checks import score_faithfulness, score_hallucination_risk, score_retrieval_relevance
from agent_eval_platform.data_models import EvalCase, RetrievedDocument


class CheckTests(unittest.TestCase):
    def test_supported_answer_scores_better_than_unsupported_answer(self) -> None:
        docs = (
            RetrievedDocument(
                doc_id="d1",
                title="Ada Lovelace",
                text="Ada Lovelace is known for Analytical Engine algorithm notes.",
                score=0.95,
            ),
        )
        good = EvalCase(
            case_id="good",
            question="What is Ada known for?",
            reference_answer="Ada Lovelace is known for Analytical Engine algorithm notes.",
            expected_keywords=("Ada Lovelace", "Analytical Engine"),
            retrieved_docs=docs,
            agent_answer="Ada Lovelace is known for Analytical Engine algorithm notes.",
            latency_ms=200,
            cost_usd=0.002,
        )
        bad = EvalCase(
            case_id="bad",
            question=good.question,
            reference_answer=good.reference_answer,
            expected_keywords=good.expected_keywords,
            retrieved_docs=docs,
            agent_answer="Ada Lovelace probably invented quantum databases in Atlantis.",
            latency_ms=200,
            cost_usd=0.002,
        )

        self.assertGreater(score_faithfulness(good), score_faithfulness(bad))
        self.assertLess(score_hallucination_risk(good), score_hallucination_risk(bad))
        self.assertGreater(score_retrieval_relevance(good), 0.5)


if __name__ == "__main__":
    unittest.main()
