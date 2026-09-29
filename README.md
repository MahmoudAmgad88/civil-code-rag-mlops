# Egyptian Civil Code RAG MVP

A bilingual Arabic/English retrieval-augmented generation MVP over a frozen subset of the Egyptian Civil Code. It supports exact article text, explanations of a named article, semantic questions, explicit scope rejection, source-linked answers, and citation validation.

This is an educational MLOps application, not legal advice. The frozen corpus contains 162 records covering Articles 1–160 plus two promulgation records, from PDF pages 1–18. Articles 54–80 are represented only by a source note where original text is unavailable. The corpus does not establish current legal status, complete coverage, or authoritative transcription.

## Architecture

- `core/`: question routing, language detection, scope and citation rules
- `repositories/`: loads the frozen article corpus once
- `retrieval/`: language-isolated semantic retrieval and source context building
- `generation/`: the stable OpenAI Responses request (`store=False`)
- `services/`: `AskService`, the business-logic entry point
- `api/`: thin FastAPI validation, dependency lifecycle, schemas, and error mapping
- `pipelines/`: reproducible offline parsing, corpus, index, and retrieval-evaluation commands
- `tests/`: isolated unit/API tests plus local frozen-artifact smoke coverage

The API caches the article repository and `AskService`. The embedding model/index and OpenAI client initialize only when their routes require them, then are reused. Importing the app, `/health`, exact lookup, out-of-scope handling, and source-note-only responses require neither model loading nor an OpenAI key.

## Setup and run

Install the base application:

```bash
uv sync
```

Install development and local embedding dependencies:

```bash
uv sync --extra dev --extra embeddings
```

Start the installed package from the repository root:

```bash
uv run --extra embeddings uvicorn civil_code_rag.api.main:app --host 127.0.0.1 --port 8000
```

Check health and ask for exact text:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"question":"What does Article 91 say?"}'
```

Semantic and explanation routes that generate text require `OPENAI_API_KEY`. Keep it in the process environment or a secret manager; never commit it. Runtime paths and model names can be overridden with `CIVIL_CODE_RAG_CORPUS_PATH`, `CIVIL_CODE_RAG_INDEX_DIR`, `CIVIL_CODE_RAG_EMBEDDING_MODEL`, and `CIVIL_CODE_RAG_LLM_MODEL`.

## Tests and quality

Normal automated tests use fakes and make no Hugging Face downloads or OpenAI requests. Local corpus/index artifacts are checked directly.

```bash
uv run --extra dev --extra embeddings python -m pytest tests -q
uv run --extra dev ruff check src tests pipelines eval
```

Target narrower layers when iterating:

```bash
uv run --extra dev python -m pytest tests/test_ask_service.py tests/test_api.py -q
uv run --extra dev python -m pytest tests/test_runtime_integrity.py -q
```

## Offline data and evaluation workflows

Run commands from the repository root, in this order when intentionally rebuilding artifacts:

```bash
uv run python -m pipelines.parse_arabic
uv run python -m pipelines.parse_english
uv run python -m pipelines.pair_articles
uv run python -m pipelines.validate_corpus
uv run python -m pipelines.build_search_records
uv run --extra embeddings python -m pipelines.check_token_lengths
uv run --extra embeddings python -m pipelines.build_embedding_index
uv run python -m pipelines.build_manifest
uv run --extra embeddings python -m pipelines.evaluate_retrieval
```

Do not rebuild the checked-in frozen corpus or embeddings casually: changes should be reviewed as versioned data artifacts. The current index contains 268 records with embedding shape `(268, 384)`.

## MLOps boundary

The package/API boundary, portable configuration, deterministic local artifacts, dependency injection, lifecycle caching, offline pipelines, tests, and health endpoint are ready for later containerization, CI/CD, experiment tracking, serving, and monitoring. Those platform concerns and any RAG-model redesign are intentionally outside this checkpoint.
