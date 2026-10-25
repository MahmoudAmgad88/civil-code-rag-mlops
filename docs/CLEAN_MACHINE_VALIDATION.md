# Clean-machine validation evidence

Date: 25 October 2026 (Cairo). Environment: Windows host, local Python 3.12.9, clean native environment Python 3.12.13, Docker Desktop Linux containers, Docker client 29.3.1, Compose v5.1.1, uv 0.11.7. Container build used Python 3.12.15 and torch 2.14.1+cpu. Validation was completed after noon Cairo; deadline compliance is not claimed.

A separate local clone was created from the release branch. It contained no `.env`, original `data/index`, original virtual environment, original `.dvc/config.local` or Hugging Face model cache. Docker build/package caches were available, so this is checkout-isolated validation, not a claim that every network download was repeated on a pristine operating system.

## Executed checks

Commands below were actually executed. On Windows the initial test commands used the already-installed `.venv` directly to avoid sandbox cache permissions. Paths are shown relative to each checkout.

| Command | Actual result |
|---|---|
| `git branch --show-current`, `git status --short`, `rg --files` | Inspected starting branch, user edits and repository files before implementation |
| `git switch -c release/graduation-readiness` | Created dedicated branch with authorized Git metadata access |
| `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -xq --basetemp=.pytest_tmp` | Baseline: 12 passed; sandbox cache warning and upstream deprecation warning |
| `.\.venv\Scripts\ruff.exe check .` | Final local check: all checks passed |
| `uv --cache-dir outputs/uv-cache sync --locked --extra dev --extra embeddings --offline` | Existing environment: resolved 203 packages, checked 194; no lock change |
| `.\.venv\Scripts\python.exe -m civil_code_rag.release_artifact --output outputs/clean-index` | Fresh destination restored; 268 index / 162 corpus records |
| `.\.venv\Scripts\python.exe -m pipelines.validate_corpus` | All corpus structure checks passed |
| `.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp=outputs/pytest-release-final` | 81 passed, one upstream AnyIO/Starlette deprecation warning, 10.56s reported by pytest |
| `.\.venv\Scripts\python.exe -m dvc repro` with the virtualenv Scripts directory on PATH | Restoration stage succeeded; `dvc.lock` generated/refreshed |
| `.\.venv\Scripts\python.exe -m dvc status` | Restoration stage reports `always changed`, deliberately; original pointer unchanged |
| `docker compose --env-file .env.example config --quiet` | Valid configuration; no expanded secrets printed |
| `docker build -t civil-code-rag:release .` | Successful Linux CPU image build; locked dependencies and artifact restoration succeeded |
| `docker compose -p graduation-release-check -f docker-compose.yml -f outputs/compose-no-key.yml up --build -d --wait --wait-timeout 180` | Built and became healthy with a fresh volume; override set `OPENAI_API_KEY` to blank |
| `.\.venv\Scripts\python.exe -m pipelines.smoke_api --expect-no-key` | Passed health, exact_en, exact_ar, empty_input_422 and missing_key_503 |
| `docker compose -p graduation-release-check -f docker-compose.yml -f outputs/compose-no-key.yml exec -T api python -c ...` | uid 1000; Hugging Face cache entry count 0 after no-key checks |
| `docker image inspect graduation-release-check-api --format '{{.Size}}'` | Docker-reported size: 392,774,420 bytes for that built image; not a peak disk/RAM measurement |
| `docker compose -p graduation-release-check -f docker-compose.yml -f outputs/compose-no-key.yml down` | Validation service/network shut down successfully |
| `git clone --no-hardlinks --branch release/graduation-readiness . outputs/clean-checkout` | Separate clone created from implementation commit `c8bc548` |

The temporary no-key override contained only:

```yaml
services:
  api:
    environment:
      OPENAI_API_KEY: ""
```

## Separate clone

Executed from `outputs/clean-checkout`:

```powershell
uv sync --system-certs --locked --extra dev --python 3.12
Copy-Item -LiteralPath .env.example -Destination .env
docker compose -p graduation-clean-checkout up --build -d --wait --wait-timeout 180
uv run --locked dvc repro
uv run --locked python -m pipelines.validate_corpus
uv run --locked python -m pytest tests -q
uv run --locked ruff check .
```

Locked native dev installation succeeded: 182 packages installed into a fresh environment. Docker build restored the frozen index from Git data and became healthy. DVC restoration and corpus checks succeeded. Bilingual HTTP smoke was then run from the root checkout against this clone's port 8000 and passed all five no-key check groups. Before model download, the new container's model-cache entry count was verified as 0. The clean native Windows pytest process failed as described below; it is not included in the 81-test passing claim.

The clone's first model download was executed as:

```powershell
docker compose -p graduation-clean-checkout exec -T api /app/.venv/bin/python -c "from sentence_transformers import SentenceTransformer; from civil_code_rag.release_artifact import MODEL_NAME,MODEL_REVISION; m=SentenceTransformer(MODEL_NAME,revision=MODEL_REVISION,device='cpu'); print('model_ready',m.get_sentence_embedding_dimension())"
```

It succeeded with `model_ready 384`. Hugging Face emitted an unauthenticated-rate-limit warning; no HF token was required. A method-rename warning from Sentence Transformers does not affect model loading.

## Embedding and secret evidence

An offline Python check loaded `SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION, device='cpu', local_files_only=True)`, encoded every ordered `passage: ` search record with normalized embeddings and compared the result with the frozen vectors. Maximum absolute difference was **0.0**. Cached-model load, retrieval and vector comparison took 23.038 seconds in the final recorded run; this is not first-install time or a production latency benchmark. English semantic retrieval ranked CC-91 first for the expression-of-intent question. Actual numeric evidence is in `docs/evidence/model-validation.json`.

A bounded pattern scan over tracked files and Git history found no OpenAI/AWS credential candidates, and `.env` was confirmed ignored. Only the boolean/count summary is stored in `docs/evidence/secret-scan-summary.json`; no credential values were printed. This scan is not a comprehensive security audit.

## Failed attempts and limits

- Initial sandboxed Git branch creation and uv cache access failed on filesystem permissions; authorized host execution created the branch and workspace cache/direct-venv commands avoided the uv restriction.
- Initial full pytest attempts hit temporary-directory access errors in the sandbox. Host execution worked. The first complete suite after adding citations had 71 passes and two expected old-contract assertion failures; those assertions were updated, and the final 81-test suite passed.
- An initial DVC stage declared `data/index.dvc` as a dependency, which DVC rejected. That invalid dependency was removed; the original pointer remains intact and the corrected pipeline passed.
- Initial Docker sandbox access reported unavailable engine/buildx lock access. Host-access builds and Compose startup subsequently succeeded. The initial messages do not establish a persistent Docker-engine defect.
- An initial ad-hoc Arabic HTTP smoke used the Windows pipe's default encoding and timed out after the question was corrupted. The committed UTF-8-safe smoke module uses escaped Unicode and passed Arabic exact lookup.
- One container-inspection command had an unmatched parenthesis; the corrected command reported uid 1000 and an empty cache.
- Clean native install with `--offline --extra embeddings` failed because a Windows torch wheel was absent from cache. An online no-key dev install initially failed TLS `UnknownIssuer`; `--system-certs` resolved trust and the locked dev installation succeeded. Native Windows embeddings were not freshly installed; Linux container CPU embeddings were installed and loaded successfully.
- A native-host `pipelines.smoke_api --base-url http://127.0.0.1:8001 --live-generation` timed out. That attempt is not a passing semantic test. A separate container semantic check forwards the existing key only through the child environment and records the resulting route/citation summary below.
- GitHub connector invocation was unavailable. CLI remote access initially failed certificate trust; `git -c http.sslBackend=schannel ls-remote --heads origin main` succeeded without changing global settings. Existing credentials were checked by availability only, without printing them.
- Remote CI, macOS/ARM execution, production concurrency, peak RAM, fresh-network setup duration, RAGAS and advanced monitoring have not been verified.

Final live-check, additional Linux-container tests and Git delivery outcomes are appended below. No absent result should be interpreted as a pass.


## Final live semantic result

The authorized one-off Linux container check completed successfully after the clean clone's first model download. The OpenAI key was read in the parent process from the existing environment/dotenv file and forwarded using Docker's `-e OPENAI_API_KEY` environment forwarding; no key value appeared in arguments, files or output. The check invoked `get_ask_service().ask("When does an expression of intent take effect?")` in the release image with its model-cache volume.

Actual result:

```json
{"route":"semantic","language":"en","cited_article_ids":["CC-91"],"has_answer":true}
```

This exercises the real CPU retriever, local index, context builder, OpenAI generation and citation validation. It is a successful semantic application smoke, not a production load benchmark or RAGAS score. The separate no-key smoke exercises the real HTTP API contract. The earlier native-host HTTP semantic timeout remains a recorded failure.


## Fresh native Windows test limitation

`uv run --locked python -m pytest tests -q` and direct virtualenv pytest invocations exited with code 1 in the fresh Python 3.12.13 environment. Disabling plugin autoload and capture exposed `OPENSSL_Uplink ... no OPENSSL_Applink`. Imports of pytest 9.1.1, NumPy 2.5.3 and FastAPI 0.141.1 succeeded individually. Removing inherited Conda DLL paths did not produce a passing test run. This remains an environment/runtime issue requiring investigation; no clean-native pytest pass is claimed. The existing Python 3.12.9 environment's 81 passing tests and the separate clean-clone Docker HTTP/semantic checks remain valid evidence.


## Linux suite and Git delivery

An ephemeral container based on `graduation-clean-checkout-api` mounted the isolated clone's `tests` and corpus manifest read-only, installed locked dev/embedding extras, then ran:

```sh
uv sync --locked --extra dev --extra embeddings
.venv/bin/python -m pytest tests -q -p no:cacheprovider
```

Actual result: **81 passed, one upstream deprecation warning, 3.90 seconds**. The disposable test container was removed automatically. This verifies deterministic tests on the project's primary Linux runtime despite the separate native Windows OpenSSL failure.

Logical commits were made on the release branch and pushed using Windows certificate trust, without force-pushing or updating main:

```sh
git -c http.sslBackend=schannel push -u origin release/graduation-readiness
```

Draft pull request: https://github.com/MahmoudAmgad88/civil-code-rag-mlops/pull/4 . It was created through GitHub's API because the connector was unavailable; authentication used Git's existing credential in memory. No merge was performed. Remote CI results must be checked on the final commit; local/container results do not imply a remote pass.
