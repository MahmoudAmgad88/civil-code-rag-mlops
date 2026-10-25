# Graduation release preparation

Date: 25 October 2026 (Cairo). Branch: `release/graduation-readiness`.

- Added a checksum-validated 415,196-byte frozen index archive so a clone does not depend on a developer's DVC remote or local index mount. Original `data/index.dvc` is preserved.
- Added `dvc.yaml`/`dvc.lock` restoration and validation, including input hashes, vector checks, source IDs, language and record order.
- Expanded `/health` with indexed-document and corpus counts; unavailable/invalid local data returns 503. Health remains independent of OpenAI and embedding model downloads.
- Added exact-route `cited_article_ids` while preserving original response fields. Repealed/source-note responses do not invent original text or generated explanations.
- Added standard `.env` loading, documented all five runtime variables, explicit missing-key 503 behavior before embedding loading, and sanitized upstream errors.
- Pinned the CPU embedding revision; regenerated vectors matched the frozen index exactly during local validation. Different embedding models are rejected for this release index.
- Added non-root CPU Docker Compose serving on localhost:8000, baked-in validated data, an empty-on-first-use model-cache volume, and health checks. Base images are pinned by digest.
- Extended CI with DVC restoration, corpus/index validation, Docker build and bilingual no-key HTTP smoke checks. No registry push was added.
- Replaced setup documentation with a clean-checkout path, examples, local tests, DVC/MLflow commands, shutdown and troubleshooting.

Deterministic validation: 81 tests passed in the existing Windows environment and 81 passed in the ephemeral Linux container with one upstream AnyIO/Starlette deprecation warning. See `CLEAN_MACHINE_VALIDATION.md` for exact commands, container evidence, environment failures and any remaining external-service limitations. Advanced rubric gaps are listed separately in `GRADUATION_GAPS.md`.

Existing user edits to `.gitignore` were retained in the working tree and excluded from release commits. The user-created `.env.example` was expanded as requested. No `.env` contents or credentials were committed. No merge or push to main was performed.

Draft PR: https://github.com/MahmoudAmgad88/civil-code-rag-mlops/pull/4 .

Remote push and PR CI passed on ed27b9d, including Docker/Compose smoke. Links and status snapshots are retained in the validation report.
