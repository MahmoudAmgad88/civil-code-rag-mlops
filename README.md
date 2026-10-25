# Egyptian Civil Code RAG

Bilingual Arabic/English FastAPI RAG over a frozen educational subset: Articles 1-160, two promulgation records, 162 corpus records and 268 language-specific search records. Exact lookup, article explanation, semantic retrieval, citation validation and source-note handling are implemented.

Educational use only. The corpus covers PDF pages 1-18 of 170; transcription and current legal status are unverified. Articles 54-80 have a source note rather than original text. This is not legal advice.

## Clean-machine startup

Prerequisites: Git, an internet connection, Docker Engine/Desktop running in Linux-container mode, and Docker Compose with `--wait` support. The primary target is Linux x86_64; Windows uses Docker Desktop/WSL2. macOS Linux-container execution has not been validated. CPU only; no GPU, CUDA, AWS, Qdrant or Langfuse account is required. Allow disk space for the Python/PyTorch image and the multilingual model cache; first-download time and peak RAM depend on the machine and have not been benchmarked.

Clone `https://github.com/MahmoudAmgad88/civil-code-rag-mlops.git`, select the release branch/commit supplied with the submission, and enter its directory. From that directory, the three primary commands are:

```sh
cp .env.example .env
docker compose up --build -d --wait --wait-timeout 180
curl http://127.0.0.1:8000/health
```

`cp` also works in PowerShell. Use `curl.exe` in Windows PowerShell if `curl` is an alias. If `.env` already exists, keep it instead of replacing it. Before startup, optionally put an evaluator-provided `OPENAI_API_KEY` in `.env` to enable generated answers. Leaving it blank enables no-key review.

Expected health response:

```json
{"status":"ok","indexed_document_count":268,"corpus_record_count":162}
```

The image restores and validates the versioned index during build. There is no developer index mount or DVC remote prerequisite. Health checks inspect the corpus/index but never download a model or contact OpenAI. The first semantic request downloads the pinned Hugging Face model into a new named cache volume. Expect that request to be slower; download duration has not been measured. Package/image downloads need internet during build. After setup, health and exact lookup work offline; generation needs internet and OpenAI access.

Only API port 8000 is published, bound to `127.0.0.1`. Optional MLflow uses port 5000.

## Runtime configuration

| Variable | Default / requirement |
|---|---|
| `OPENAI_API_KEY` | Blank is allowed; required for generated answers. Standard OpenAI key supplied by the evaluator. |
| `CIVIL_CODE_RAG_CORPUS_PATH` | `data/processed/articles.jsonl` locally |
| `CIVIL_CODE_RAG_INDEX_DIR` | `data/index` locally |
| `CIVIL_CODE_RAG_EMBEDDING_MODEL` | `intfloat/multilingual-e5-small` |
| `CIVIL_CODE_RAG_LLM_MODEL` | `gpt-4.1-mini`; key must have access to this model |

Local Python reads `.env`; process environment values take priority. Compose reads `.env` and sets the two data paths to their absolute container locations. Keep keys out of Git; `.env` is ignored and excluded from the Docker build context. Do not paste `docker compose config` output when using a real key; use `config --quiet` for validation.

The release index is tied to embedding revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`. Serving rejects another embedding model to prevent incompatible retrieval. A different model requires a separately rebuilt, evaluated and versioned index and an intentional serving configuration change.

## API examples and contract

Interactive schemas: `http://127.0.0.1:8000/docs`.

```sh
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"question":"What does Article 91 say?"}'
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"question":"ما نص المادة ٩١؟"}'
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"question":"Explain Article 91"}'
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"question":"When does an expression of intent take effect?"}'
```

On Windows PowerShell, use `Invoke-RestMethod` with a UTF-8 body to avoid native-command quoting/encoding differences:

```powershell
$body = [Text.Encoding]::UTF8.GetBytes('{"question":"ما نص المادة ٩١؟"}')
Invoke-RestMethod http://127.0.0.1:8000/ask -Method Post -ContentType 'application/json; charset=utf-8' -Body $body
```

Exact-response fields (answer shortened here):

```json
{"route":"exact","language":"en","article_id":"CC-91","cited_article_ids":["CC-91"],"answer":"A declaration of intention ...","source_note":null,"verified_status":"unverified","pdf_pages":[8,9]}
```

This is a schema illustration, not a complete verbatim article. Page metadata comes from the frozen corpus. Exact responses retain the original fields and add `cited_article_ids`. Explanations and semantic responses already expose that citation list. A repealed exact lookup returns `answer: null`, the source note, and an empty citation list; generated explanations of those records also return the source note without calling OpenAI.

| Request | Key/model needed | Behavior |
|---|---|---|
| Health | Neither | 200 + data counts; 503 if local data is unavailable/invalid |
| Exact article in Arabic/English | Neither | Original corpus text or source note |
| Explicit out-of-scope request | Neither | Rejection response |
| Empty/whitespace question | Neither | HTTP 422 |
| Article outside corpus | Neither | HTTP 404 |
| Explain available original text | OpenAI key | Grounded generation, validated citations |
| Semantic question | OpenAI key + CPU embedding model | Language-isolated retrieval and grounded generation |

Without a key, LLM-dependent routes return HTTP 503 with `{"detail":"OPENAI_API_KEY is required for generated answers."}` before model loading. OpenAI failures return a sanitized 503; invalid generated citations return 502. API routes use synchronous handlers, so FastAPI runs blocking model/HTTP work in its thread pool. This MVP is not tuned for concurrent production traffic.

## Local Python setup and tests

Install Python 3.12 and uv 0.11.7. Path handling supports Windows/Linux; the existing Python 3.12.9 environment passed tests. A fresh Windows Python 3.12.13 pytest run hit an OpenSSL runtime error, so Docker is the validated clean-machine path. From the checkout, after copying `.env.example` as above:

```sh
uv sync --locked --extra dev --extra embeddings --python 3.12
uv run --locked python -m civil_code_rag.release_artifact
uv run --locked uvicorn civil_code_rag.api.main:app --host 127.0.0.1 --port 8000
```

No key is required for deterministic checks:

```sh
uv run --locked ruff check .
uv run --locked python -m pipelines.validate_corpus
uv run --locked python -m pytest tests -q
uv run --locked python -m pipelines.smoke_api --expect-no-key
```

The last command requires the running no-key API. Omit `--expect-no-key` if using a real key. `--live-generation` makes one paid semantic request and should only be used intentionally. Unit/integration tests mock generation and do not call OpenAI. Model installation is optional for health/exact-only local review: `uv sync --locked --extra dev` is sufficient for those paths and deterministic tests.

## DVC and reproducible release artifacts

The chosen distribution is a 415,196-byte Git-tracked archive, `artifacts/retrieval-index.zip`, with SHA-256 checksums, frozen input hashes and model provenance in `artifacts/retrieval-index.json`. This small MVP artifact avoids external storage credentials. The trade-off is Git history growth if many index versions are committed; larger future corpora should use shared artifact storage.

```sh
uv run --locked dvc repro
uv run --locked dvc status
```

`dvc.yaml` restores the index from the archive, validates checksums, vector normalization, finite values, source IDs, languages, dimensions and record order, and writes `outputs/index-validation.json`. Dependencies are the archive/manifest, frozen corpus/search records, restoration code/settings and lockfile. The original `data/index.dvc` remains intact; the pipeline does not declare duplicate ownership of its output. Its report has `cache: false` and the stage intentionally runs on every reproduction to check missing/corrupt runtime files. `dvc status` therefore reports `always changed` for that stage; this is expected.

No `dvc pull` is needed. The previous local remote in developer-only `.dvc/config.local` is not shared and is not used by this procedure. Restoration refuses to overwrite a different existing index; preserve that index and use `--output` with a new directory for comparison. To test a fresh destination:

```sh
uv run --locked python -m civil_code_rag.release_artifact --output outputs/reviewer-index
```

Git attributes preserve the frozen JSONL CRLF bytes across operating systems so source hashes match. The source PDF is not bundled; reconstructing the original PDF extraction requires that external source and is outside clean-machine startup. The frozen corpus and paired/search records are in Git. To intentionally regenerate vectors rather than restore the exact release bytes, run `uv run --locked python -m pipelines.build_embedding_index` with embedding dependencies installed. CPU numerical differences across library/platform versions may prevent byte-identical regeneration; archive restoration is byte-identical.

## MLflow evidence

Existing evaluation uses `eval/dev_questions.jsonl`, Recall@K, MRR and retrieval latency, with Git revision/dirty status, parameters and summary artifacts logged to MLflow. In one terminal:

```sh
uv run --locked mlflow server --host 127.0.0.1 --port 5000
```

In another:

```sh
uv run --locked python -m pipelines.evaluate_retrieval
```

Open `http://127.0.0.1:5000` and select `civil-code-rag-retrieval`. The current script evaluates `top_k=6`. Historical runs/Registry state are local artifacts and are not included in a clone. No five-run comparison, RAGAS scores, quality threshold or Registry promotion is claimed for this release. See the gap report for rubric items requiring further work.

## CI and shutdown

GitHub Actions installs locked Python/uv dependencies, runs Ruff, reproduces the index, checks the corpus, runs pytest, builds Docker, and performs no-key Compose/API checks. No API secret or registry push is required. A local passing run is not evidence that the remote workflow passed; inspect the PR checks.

```sh
docker compose down
```

This keeps the model cache for future startups. `docker compose down --volumes` also deletes this project's model cache and forces later downloads. Stop local Uvicorn/MLflow with Ctrl+C.

## Troubleshooting

- Docker connection/pipe error: start Docker Desktop or Docker Engine and verify `docker version`. In restricted agent environments Docker may require host access.
- Port 8000 occupied: stop the other API or change the published host port in Compose and your request URL.
- Index checksum failure: check out the release files with Git attributes enabled; do not copy text files through tools that rewrite line endings. Keep a custom index separately.
- HTTP 503 for generation: set a valid `OPENAI_API_KEY` and restart the service; verify model access/quota. Errors intentionally omit private upstream details.
- Model download failure: allow Hugging Face access and disk space; the first semantic request needs internet. Health/exact lookup remain available.
- Native Windows `uv sync` fails with `UnknownIssuer`: retry with `uv sync --system-certs --locked --extra dev --extra embeddings --python 3.12` when your organization trusts its certificate through the Windows certificate store. TLS verification remains enabled.
- Native Windows pytest exits with `OPENSSL_Uplink ... no OPENSSL_Applink`: this occurred with fresh uv Python 3.12.13 on the validation host; use Docker while investigating the local OpenSSL/runtime environment.
- pytest temporary-directory access errors in a sandbox: run tests in a normal shell or an authorized host context. These are environment errors, not passing tests.
- DVC complains about a remote: use `dvc repro` for this release; `dvc pull` targets the original developer remote and is not the reviewer path.

Evidence and known limits: [readiness](docs/GRADUATION_READINESS.md), [clean-machine validation](docs/CLEAN_MACHINE_VALIDATION.md), [graduation gaps](docs/GRADUATION_GAPS.md), [release notes](docs/RELEASE_NOTES.md).
