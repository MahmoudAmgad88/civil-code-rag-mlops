# Refactoring summary

## Completed

- Made `civil_code_rag.services.AskService` the business entry point for every `/ask` route.
- Moved FastAPI into `civil_code_rag.api` with Pydantic contracts and explicit 404/422/502 error translation.
- Added portable environment-backed settings and cached/lazy runtime dependencies.
- Preserved exact, explain, semantic, unsupported, out-of-scope, repealed-note, citation, language-isolation, OpenAI model/instructions, and `store=False` behavior.
- Replaced tests of compatibility wrappers with package/API contract and frozen-artifact integrity tests.
- Moved reproducible parsing, corpus validation, search-record/index generation, token checks, and retrieval evaluation into `pipelines`.

## Removed

The legacy `scripts/` application, compatibility wrappers, duplicate runtime retrieval/generation code, ad hoc inspection scripts, and one-off smoke/debug commands were removed. Runtime code and tests have no `scripts.*` imports.

## Deferred

- Docker, CI/CD, MLflow, orchestration, Kubernetes, and monitoring belong to the next MLOps stages.
- The upstream Starlette test client currently emits one AnyIO deprecation warning; it is outside application code.
- Legal-status verification, corpus expansion, and RAG algorithm changes remain intentionally out of scope.
