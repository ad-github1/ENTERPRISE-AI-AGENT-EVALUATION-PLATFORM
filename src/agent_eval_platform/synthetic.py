from __future__ import annotations

import random

from agent_eval_platform.data_models import EvalCase, RetrievedDocument


TOPICS = (
    ("Ada Lovelace", "mathematics", "Analytical Engine", "1843", "algorithm notes"),
    ("Marie Curie", "chemistry", "radioactivity", "1911", "Nobel Prize"),
    ("Katherine Johnson", "spaceflight", "orbital mechanics", "1962", "Friendship 7"),
    ("Alan Turing", "computer science", "Turing machine", "1936", "computability"),
    ("Grace Hopper", "programming", "COBOL", "1959", "compiler work"),
    ("Rosalind Franklin", "biology", "DNA diffraction", "1952", "Photo 51"),
    ("Tim Berners-Lee", "web", "World Wide Web", "1989", "HTTP"),
    ("Hedy Lamarr", "communications", "frequency hopping", "1942", "spread spectrum"),
)


def generate_cases(count: int = 120, *, seed: int = 11, noisy: bool = True) -> tuple[EvalCase, ...]:
    rng = random.Random(seed)
    cases: list[EvalCase] = []
    for index in range(count):
        person, domain, contribution, year, keyword = TOPICS[index % len(TOPICS)]
        doc = RetrievedDocument(
            doc_id=f"wiki-{index:04d}-primary",
            title=f"{person} biography",
            text=(
                f"{person} is associated with {domain}. The key contribution was {contribution}, "
                f"documented around {year}. The article highlights {keyword} as important context."
            ),
            score=round(rng.uniform(0.80, 0.99), 3),
        )
        distractor = RetrievedDocument(
            doc_id=f"wiki-{index:04d}-distractor",
            title=f"{domain.title()} overview",
            text=(
                f"This overview discusses {domain}, historical research practices, archives, "
                f"and terminology related to {keyword}."
            ),
            score=round(rng.uniform(0.35, 0.70), 3),
        )
        question = f"What contribution is {person} known for in {domain}?"
        reference = f"{person} is known for {contribution}, with key context around {keyword}."
        answer = reference

        if noisy and index % 9 == 0:
            answer = (
                f"{person} is known for {contribution}, but probably also led a separate "
                "unverified project not in the provided sources."
            )
        elif noisy and index % 13 == 0:
            answer = f"{person} is known for work in {domain}."

        latency_ms = 180 + (index % 17) * 23 + rng.uniform(0, 35)
        if index % 19 == 0:
            latency_ms += 450
        cost_usd = 0.002 + (len(answer.split()) * 0.00009) + rng.uniform(0, 0.0015)

        cases.append(
            EvalCase(
                case_id=f"case-{index:04d}",
                question=question,
                reference_answer=reference,
                expected_keywords=(person, contribution, keyword, year),
                retrieved_docs=(doc, distractor),
                agent_answer=answer,
                latency_ms=round(latency_ms, 3),
                cost_usd=round(cost_usd, 6),
                tags=("wiki", "rag", domain),
                metadata={"synthetic": True, "seed": seed, "index": index},
            )
        )
    return tuple(cases)
