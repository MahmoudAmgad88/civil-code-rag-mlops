# Graduation rubric gaps

Assessment date: 25 October 2026 (Cairo). Phase A release reliability took priority. No graduation handbook was supplied or found in the tracked repository; this assessment uses the requested checklist and cannot certify instructor-specific compliance.

| Requirement | Status | Evidence | Remaining action |
|---|---|---|---|
| Recall@K and MRR | PASS (implementation) | `pipelines/evaluate_retrieval.py`, `eval/dev_questions.jsonl`; existing language-separated metrics/latency and MLflow logging preserved | Run evaluation against a chosen release and retain results |
| RAGAS faithfulness, answer relevancy, context precision/recall | MISSING | No RAGAS dependency, harness or recorded scores | Add a version-compatible optional evaluation environment, reference answers and authorized judge budget |
| Deterministic retrieval quality CI threshold | MISSING | CI validates artifacts and behavior; it does not gate semantic scores | Establish a measured baseline before choosing a threshold |
| Five meaningful MLflow comparisons | PARTIAL | Existing script logs top_k, model, dataset, count, metrics, Git tags and summary artifacts; current top_k is 6 | Run and retain five meaningful configurations; only top_k is currently varied manually |
| Chunking/embedding configuration comparisons | PARTIAL | Article-level search records and one frozen embedding model; alternative models cannot safely reuse this release index | Implement deliberate index variants before comparing configurations |
| Best-run selection and Model Registry evidence | PARTIAL | Previous README described Registry practice, but historical runs/Registry contents are not distributed with the clone | Export actual run IDs, selection criteria and Registry/alias evidence; do not infer success from narrative |
| FastAPI CPU serving | PASS | Working API, non-root Docker runtime, no-key Compose startup and smoke checks | Remains an MVP; no production concurrency claim |
| BentoML | MISSING | No service/dependency | Confirm whether FastAPI suffices or add a separately tested serving adapter |
| vLLM | BLOCKED (architecture/rubric) | Generator calls hosted OpenAI Responses API; no self-hosted generative weights/GPU deployment | Instructor must approve the architecture alternative or provision and validate a separate compatible model deployment |
| Locust and production latency study | MISSING | No load-test harness/results; retrieval helper measures latency only | Define CPU hardware, concurrency and request mix, then record actual measurements |
| Langfuse | MISSING | No optional tracing integration | Add optional tracing with privacy controls and configuration |
| Prometheus/Grafana | MISSING | No metrics endpoint or dashboard | Add optional monitoring components after release validation |
| Faithfulness monitoring / token usage | MISSING | Citation allow-list checks exist, but no semantic faithfulness metric or token monitoring | Implement separate quality and usage telemetry |
| Drift detection / alerts | MISSING | No baseline distribution or threshold implementation | Define a monitored signal, baseline and justified alert thresholds |
| PII guardrails | PARTIAL | No explicit PII detector/redactor; source grounding and OpenAI `store=False` are implemented | Add measured PII handling; neither existing behavior proves PII protection |
| AWQ 4-bit | BLOCKED (architecture/rubric) | Project runs CPU sentence embeddings and a hosted OpenAI generator; hosted weights are inaccessible | Instructor approval is needed for this architecture; do not describe remote API generation as AWQ or vLLM |
| Full legal corpus / verified legal status | MISSING by MVP scope | Frozen 162 records, Articles 1-160, pages 1-18; status remains unverified | Obtain/validate authoritative sources and broaden coverage as a separate project |
| Shared DVC remote | PARTIAL | Original local remote is not public; offline release archive replaces the startup dependency | Provision shared storage if rubric explicitly requires a remote restore, rather than a reproducible local artifact |

No new monitoring, self-hosted model, RAGAS scores, comparison runs, registry promotions or load-test results were fabricated for this delivery. Optional infrastructure was not added to the mandatory startup path.
