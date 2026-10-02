# 1. Start from a Linux image containing Python 3.12.
FROM python:3.12-slim

# 2. Copy a specific uv version into the image.
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

# 3. Set the application's working directory.
WORKDIR /app

# 4. Configure uv for the container environment.
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_LINK_MODE=copy

# 5. Copy dependency definitions first.
COPY pyproject.toml uv.lock README.md ./

# 6. Install runtime dependencies using the lockfile.
# RUN uv sync --locked --no-dev --no-install-project
# RUN uv sync --locked --no-dev --extra embeddings --no-install-project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra embeddings --no-install-project

# 7. Copy the application and its frozen corpus.
COPY src/ ./src/
COPY data/processed/articles.jsonl ./data/processed/articles.jsonl

# 8. Install our application package.
# RUN uv sync --locked --no-dev
# RUN uv sync --locked --no-dev --extra embeddings
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra embeddings

# 9. Document the application port.
EXPOSE 8000

# 10. Start FastAPI when the container runs.
CMD ["/app/.venv/bin/uvicorn", "civil_code_rag.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]