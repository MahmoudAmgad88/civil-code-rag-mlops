FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704
COPY --from=ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a /uv /bin/
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --extra embeddings --no-install-project
COPY README.md ./
COPY src/ ./src/
COPY data/processed/articles.jsonl data/processed/search_records.jsonl ./data/processed/
COPY artifacts/ ./artifacts/
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --extra embeddings \
    && .venv/bin/python -m civil_code_rag.release_artifact \
    && useradd --create-home app \
    && mkdir -p /home/app/.cache/huggingface \
    && chown -R app:app /home/app/.cache
ENV CIVIL_CODE_RAG_CORPUS_PATH=/app/data/processed/articles.jsonl CIVIL_CODE_RAG_INDEX_DIR=/app/data/index HF_HOME=/home/app/.cache/huggingface
USER app
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "civil_code_rag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
