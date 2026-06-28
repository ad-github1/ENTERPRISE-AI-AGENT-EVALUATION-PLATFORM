from __future__ import annotations

import re
from collections import Counter

from agent_eval_platform.data_models import EvalCase


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


def score_faithfulness(case: EvalCase) -> float:
    answer_tokens = content_tokens(case.agent_answer)
    if not answer_tokens:
        return 0.0

    context_tokens = set(content_tokens(context_text(case)))
    reference_tokens = set(content_tokens(case.reference_answer))
    supported = sum(1 for token in answer_tokens if token in context_tokens)
    reference_overlap = sum(1 for token in answer_tokens if token in reference_tokens)
    support_ratio = supported / len(answer_tokens)
    reference_ratio = reference_overlap / len(answer_tokens)
    return clamp(0.75 * support_ratio + 0.25 * reference_ratio)


def score_retrieval_relevance(case: EvalCase) -> float:
    query_tokens = set(content_tokens(case.question))
    expected_tokens = set(content_tokens(" ".join(case.expected_keywords)))
    target_tokens = query_tokens | expected_tokens
    if not target_tokens:
        return 0.0

    doc_tokens = set(content_tokens(context_text(case)))
    target_hit_ratio = len(target_tokens & doc_tokens) / len(target_tokens)
    keyword_hit_ratio = len(expected_tokens & doc_tokens) / len(expected_tokens) if expected_tokens else 0.0
    avg_doc_score = sum(max(0.0, min(1.0, doc.score)) for doc in case.retrieved_docs) / max(len(case.retrieved_docs), 1)
    return clamp(0.55 * target_hit_ratio + 0.30 * keyword_hit_ratio + 0.15 * avg_doc_score)


def score_hallucination_risk(case: EvalCase) -> float:
    answer_tokens = content_tokens(case.agent_answer)
    if not answer_tokens:
        return 1.0

    context_tokens = set(content_tokens(context_text(case)))
    unsupported = [token for token in answer_tokens if token not in context_tokens]
    unsupported_ratio = len(unsupported) / len(answer_tokens)
    suspicious_markers = marker_penalty(case.agent_answer)
    proper_noun_penalty = unsupported_entity_penalty(case.agent_answer, context_text(case))
    return clamp(0.70 * unsupported_ratio + suspicious_markers + proper_noun_penalty)


def context_text(case: EvalCase) -> str:
    return " ".join(doc.text for doc in case.retrieved_docs)


def content_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 2]


def marker_penalty(answer: str) -> float:
    lowered = answer.lower()
    markers = (
        "probably",
        "i think",
        "might be",
        "unknown",
        "not in the provided sources",
        "as an ai",
    )
    return min(0.18, 0.06 * sum(1 for marker in markers if marker in lowered))


def unsupported_entity_penalty(answer: str, context: str) -> float:
    answer_entities = Counter(re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b", answer))
    context_entities = set(re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b", context))
    if not answer_entities:
        return 0.0
    unsupported = sum(count for entity, count in answer_entities.items() if entity not in context_entities)
    return min(0.15, 0.03 * unsupported)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))
