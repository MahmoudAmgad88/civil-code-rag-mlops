# Peer Review Guide — Egyptian Civil Code RAG MLOps Project

## Review Objective

This repository is a learning-focused MLOps implementation around a bilingual Arabic/English Egyptian Civil Code RAG MVP.

The primary goal of this review is to evaluate the **MLOps and software-engineering implementation**, not to redesign the RAG model or improve the legal corpus.

Please assess whether the repository demonstrates a clear, reproducible, testable, maintainable, and production-oriented ML/GenAI workflow.

Please start with `README.md`, which is the main project documentation.

## Current Scope

Implemented areas include:

- package-based architecture and dependency injection
- FastAPI + Pydantic
- reproducible dependencies with `uv`
- unit, API, regression, integration, and integrity tests
- Ruff quality checks
- corpus lineage / manifest validation
- DVC retrieval-index versioning
- local DVC remote and push/pull/restore practice
- MLflow experiment tracking and Model Registry practice
- Docker containerization and CPU-only PyTorch optimization
- Docker Hub / container-registry practice
- runtime secret injection
- GitHub Actions CI
- Git-based delivery workflow

The focus is:

```text
Development → Reproducible Environment → Testing → Artifact Versioning
→ Experiment Tracking → Packaging → API Serving → CI → Versioned Delivery
```

## Review Areas

### 1. Architecture and Code Organization

Inspect `src/civil_code_rag/`. Review separation between API, services, repositories, retrieval, generation, and core; dependency injection; configuration; lazy initialization; maintainability; coupling; and duplication.

### 2. Reproducibility and Dependencies

Inspect `pyproject.toml`, `uv.lock`, Python requirements, optional dependency groups, configuration paths, and corpus manifest/integrity metadata. Assess whether another engineer can reproduce the environment and whether machine-specific assumptions are avoided where practical.

### 3. Testing

Review unit, API contract, integration, regression, and runtime-integrity tests; real-corpus usage; and mocks/fakes around external services.

Normal automated tests intentionally avoid live OpenAI calls so CI remains deterministic, fast, inexpensive, and independent of external API availability. Identify important missing behavior or failure paths.

### 4. DVC Artifact Versioning

Inspect `data/index.dvc`, DVC configuration, Git ignores, and the Git/DVC responsibility split.

The project intentionally uses a **local filesystem DVC remote** to practice:

```text
dvc add → DVC cache → dvc push → local remote → dvc pull → restore
```

The local remote is a learning implementation. A shared/cloud DVC remote is future work and should not by itself block this release. Flag accidental generated/large files tracked by Git or inconsistent DVC usage.

### 5. MLflow

Review the retrieval evaluation workflow and MLflow logging. Tracked information includes `top_k`, embedding model, evaluation dataset, question count, Recall@K, MRR, retrieval latency, Git commit, Git dirty state, and evaluation summary artifact.

The Model Registry exercise covers registration, versions, champion/challenger aliases, promotion, and rollback. Assess experiment-to-code traceability and whether important metadata is missing for this MVP.

### 6. Docker

Inspect `Dockerfile`, `.dockerignore`, dependency installation, CPU-only PyTorch configuration, caching/layers, runtime configuration, external index mount, Hugging Face cache, and runtime secret injection.

An early image was roughly 18.5 GB because unnecessary CUDA/NVIDIA dependencies were installed. The CPU-only configuration reduced the development image to roughly 1.8 GB. Flag release-blocking Docker problems; further hardening/scanning can be future work.

### 7. GitHub Actions CI

Inspect `.github/workflows/ci.yml`: triggers, clean-runner setup, dependency installation, Ruff, pytest, and failure behavior.

The current DVC remote is local to the developer machine, so GitHub Actions cannot `dvc pull` from it. Artifact-dependent integrity checks can therefore skip when the index is unavailable. Assess whether CI remains a meaningful quality gate and whether a fundamentally broken application could incorrectly pass.

### 8. Security and Configuration

Check `OPENAI_API_KEY` handling, `.gitignore`, accidental secrets, hard-coded paths, runtime configuration, OpenAI `store=False`, Pydantic validation, citation validation, and read-only runtime mounts where applicable.

Any exposed secret or serious security issue should be **Critical**. Production secret managers, authentication, rate limiting, and advanced hardening are future concerns unless the current implementation creates an immediate risk.

### 9. Documentation and Developer Experience

Review `README.md` as a new engineer. Check whether the purpose is clear, MLOps tool choices are explained, commands are accurate, limitations are explicit, completed/future work are distinguished, and documentation claims match the repository.

Please explicitly flag any README statement that does not match the implementation.

## Suggested Validation

From the repository root:

```bash
uv sync --locked --extra dev --extra embeddings
uv run --extra dev ruff check .
uv run --extra dev --extra embeddings python -m pytest tests -q
uv run --extra dev dvc status
```

Because the artifact remote is local to the original developer environment, a reviewer cloning the repository should **not** expect `dvc pull` to work unless the remote/artifact is separately shared. The DVC review should therefore focus on implementation, metadata, and versioning design.

## Files to Prioritize

```text
README.md
pyproject.toml
uv.lock
Dockerfile
.dockerignore
.gitignore
data/index.dvc
.github/workflows/ci.yml
pipelines/
src/civil_code_rag/
tests/
```

## Out of Scope for This Release

These known future improvements should not automatically block the current learning release:

- complete extraction of all 170 PDF pages
- major RAG/model redesign
- large-scale RAG evaluation
- W&B integration
- cloud DVC storage
- Kubernetes
- Terraform / Infrastructure as Code
- production monitoring and drift monitoring
- automated retraining/re-indexing
- production secret manager
- advanced security hardening
- production cloud deployment

Please recommend them where useful, but distinguish future improvements from release blockers.

## Severity

**Critical** — should block release: exposed secret, broken core functionality, serious security issue, invalid reproducibility claim, corrupted artifact/versioning workflow, or misleading CI success for a fundamentally broken project.

**Major** — important issue that should preferably be fixed before release: important missing test coverage, significant architecture problem, broken setup instructions, or important Docker/CI issue.

**Minor** — useful improvement that does not block release: documentation clarity, naming, small cleanup, or non-critical test improvement.

**Suggestion** — optional/future enhancement such as cloud migration, monitoring, extra tooling, or further optimization.

## Requested Finding Format

For every finding, please provide:

```text
Area:
Severity: Critical / Major / Minor / Suggestion
File / line:
Finding:
Why it matters:
Recommended change:
```

Please clearly distinguish **Release blocker** vs. **Future improvement**.

## Final Review Verdict

Choose one:

- **Ready for v1.0.0**
- **Ready after minor changes**
- **Not ready — release blockers exist**

Then provide:

1. Top 3 strengths
2. Top 3 issues
3. Changes recommended before `v1.0.0`
4. Improvements that can safely move to the backlog
5. Documentation claims that do not match the implementation

## Review Philosophy

Please review the project against its stated scope rather than against an ideal enterprise platform.

> **Does this repository demonstrate a sound practical MLOps journey for moving a small RAG application from local development toward a reliable production-oriented system?**

Strict feedback is welcome, especially where implementation, documentation, reproducibility, testing, artifact management, Docker, or CI behavior does not match what the repository claims.
