# Prepare a reproducible CPU graduation release

A clean checkout previously required a developer-only DVC remote/index mount. This change distributes the small frozen index with checksum validation, adds an offline DVC restoration pipeline, and starts the API through CPU Docker Compose with a fresh cache and optional OpenAI key. It also expands health/citation contracts, documents explicit missing-key errors and extends CI with artifact and container checks.

Validation: 81 deterministic tests passed in the existing Python 3.12.9 environment and 81 passed in an ephemeral Linux container; Ruff and corpus checks passed. A separate clone built and started with a blank key and empty model cache, passed bilingual no-key HTTP checks, downloaded the pinned model and completed an authorized live semantic answer citing CC-91. Fresh native Windows pytest encountered an OpenSSL runtime failure; Docker is the validated clean-checkout path. Additional Linux test evidence and exact commands are recorded in the validation report.

The full graduation rubric is partially ready: RAGAS, five-run comparison/Registry evidence, BentoML/vLLM, monitoring, load testing and AWQ remain explicit gaps. No advanced results are fabricated. See [readiness](GRADUATION_READINESS.md), [validation](CLEAN_MACHINE_VALIDATION.md), [gaps](GRADUATION_GAPS.md) and [release notes](RELEASE_NOTES.md). The documented advanced-rubric gaps remain outside this validated CPU release scope.

Verified CI for ed27b9d: [PR workflow](https://github.com/MahmoudAmgad88/civil-code-rag-mlops/actions/runs/40180736356) and [push workflow](https://github.com/MahmoudAmgad88/civil-code-rag-mlops/actions/runs/40180733060) both passed, including Docker build and Compose/API smoke. The follow-up commit records this evidence only.

The README now preserves the full educational learning journey, interview story, roadmap and all five Mermaid diagrams. Documentation review verified 21 links, 42 command lines, diagram rendering and isolated no-key Docker startup; detailed results are in [README review](README_REVIEW_VALIDATION.md). No application code changed during that review.
