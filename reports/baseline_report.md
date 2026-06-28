# Agent Evaluation Report: baseline

- Suite: `rag-wiki-quality`
- Generated: `2026-06-28T22:23:08.416034+00:00`
- Cases: `120`
- Gate: `PASS`

## Aggregate Metrics

| Metric | Value |
|---|---:|
| Pass rate | 82.50% |
| Avg faithfulness | 0.825 |
| Avg retrieval relevance | 0.836 |
| Avg hallucination risk | 0.153 |
| p50 latency | 397.8 ms |
| p95 latency | 665.2 ms |
| p99 latency | 867.6 ms |
| Avg cost | $0.00400 |
| Total cost | $0.4800 |

## Gate Violations

- None

## Failed Cases

- `case-0000`: faithfulness, hallucination_risk (faithfulness=0.283, retrieval=0.855, hallucination=0.633)
- `case-0009`: faithfulness, hallucination_risk (faithfulness=0.232, retrieval=0.850, hallucination=0.670)
- `case-0013`: faithfulness (faithfulness=0.600, retrieval=0.838, hallucination=0.280)
- `case-0018`: faithfulness, hallucination_risk (faithfulness=0.283, retrieval=0.833, hallucination=0.633)
- `case-0026`: faithfulness (faithfulness=0.600, retrieval=0.829, hallucination=0.280)
- `case-0027`: faithfulness, hallucination_risk (faithfulness=0.283, retrieval=0.824, hallucination=0.633)
- `case-0036`: faithfulness, hallucination_risk (faithfulness=0.232, retrieval=0.837, hallucination=0.670)
- `case-0039`: faithfulness (faithfulness=0.600, retrieval=0.836, hallucination=0.280)
- `case-0045`: faithfulness, hallucination_risk (faithfulness=0.283, retrieval=0.827, hallucination=0.633)
- `case-0054`: faithfulness, hallucination_risk (faithfulness=0.328, retrieval=0.831, hallucination=0.601)
- `case-0063`: faithfulness, hallucination_risk (faithfulness=0.283, retrieval=0.853, hallucination=0.633)
- `case-0065`: faithfulness (faithfulness=0.600, retrieval=0.844, hallucination=0.280)
- `case-0072`: faithfulness, hallucination_risk (faithfulness=0.283, retrieval=0.863, hallucination=0.633)
- `case-0078`: faithfulness (faithfulness=0.650, retrieval=0.839, hallucination=0.280)
- `case-0081`: faithfulness, hallucination_risk (faithfulness=0.232, retrieval=0.818, hallucination=0.670)
- `case-0090`: faithfulness, hallucination_risk (faithfulness=0.283, retrieval=0.829, hallucination=0.633)
- `case-0091`: faithfulness (faithfulness=0.625, retrieval=0.828, hallucination=0.233)
- `case-0099`: faithfulness, hallucination_risk (faithfulness=0.283, retrieval=0.827, hallucination=0.633)
- `case-0104`: faithfulness (faithfulness=0.600, retrieval=0.835, hallucination=0.280)
- `case-0108`: faithfulness, hallucination_risk (faithfulness=0.232, retrieval=0.820, hallucination=0.670)
