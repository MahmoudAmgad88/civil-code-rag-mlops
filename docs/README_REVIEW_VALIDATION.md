# README review and validation

Reviewed `README_merged_study_and_delivery.md` against release branch `release/graduation-readiness`, implementation commit `19cdd46`. The reviewed merged source was left unchanged. Its contents now form the expanded `README.md`, with documentation corrections only. No application, dependency, Docker, workflow, corpus or index code was changed. Existing user `.gitignore` edits were left untouched. The review itself left changes uncommitted; the user subsequently authorized committing and merging this documentation with the release.

## Content preserved

- All 28 numbered sections and the Author section, plus all five Mermaid diagrams.
- The educational MLOps flow, architecture explanations, historical DVC/MLflow/Registry/Docker learning journey and lifecycle maps.
- Engineering lessons, future roadmap and first-person interview story were compared with the merged source and are identical after normalizing line endings.
- Historical image sizes, Docker Hub publishing and Registry exercises remain present, with explicit attribution to the author's account rather than new execution evidence.

## Corrections and additions

| Area | Correction | Implementation checked |
|---|---|---|
| Clone/startup | Added explicit release-branch clone and root-directory commands; warned before copying an existing `.env`; identified curl/PowerShell prerequisites | Git branch/remote, `.env.example`, Compose |
| Fresh-machine boundaries | Documented generated `data/index/` and `outputs/`, missing PDF/page-text/model/MLflow artifacts, baked-in index and first model download | Git tree, Dockerfile, artifact helper |
| Health/lazy resources | Health reads and validates local vectors/corpus on every request; only model/client construction is deferred | API main/dependencies and `release_artifact.py` |
| Architecture diagrams | Added explanation evidence/context, source-note bypass, external page-text extraction and corpus-integrity CI stage; retained all five diagrams | AskService, parsers, CI workflow |
| Package paths/tree | Qualified package-relative directories and test filenames; added generated index directory and `dvc.lock` | Actual tracked files and test paths |
| Python target | Distinguished documented Python 3.12 from package declaration `>=3.11`; retained the documented Windows runtime limitation | `pyproject.toml`, existing validation report |
| Runtime configuration | Verified all five variable names/defaults; clarified working-directory dotenv handling, cached settings, Compose path overrides and fixed offline pipeline paths | Settings, dependencies, `.env.example`, Compose |
| Model selection | Documented that a different embedding model requires a serving implementation change, not just an environment override; token-length helper is not revision-pinned | Dependencies, build/search/evaluation/token helper code |
| API contract | Verified health JSON, exact metadata/citations/pages, missing-key errors, empty input, absent articles and repealed source notes; identified shortened answer as illustrative | Schemas, route handlers, repository and request checks |
| Citation/scope claims | Clarified source-ID membership checks, lack of citation-presence/faithfulness enforcement, Arabic-character language detection and explicit scope patterns | Core answer rules/scope guard |
| Local commands | Made dev/embedding extras explicit where needed; required index restoration before pytest; separated running API and smoke terminals | Project extras, mandatory integrity tests, smoke CLI |
| Historical extraction | Parsers require `data/raw_pages/pypdf/page_001.txt` through `page_018.txt`; manifest generation also needs `data/Egyptian Civil Code.pdf`; no tracked page-extraction command exists | Parser/manifest constants and repository search |
| DVC | Explained report ownership versus preserved `data/index.dvc`; documented always-changed stage and lack of shared default remote | `dvc.yaml`, `dvc.lock`, shared DVC configuration |
| MLflow | Added locked extras, restored-index/server prerequisites, hardcoded localhost:5000 tracking URI, top_k=6, no OpenAI-key requirement and actual per-language metrics; Registry has no shipped registration command/export | Evaluation code, project extras |
| Git/history | Kept tag commands as non-executable historical reference; `v1.0.0` already exists; added read-only inspection and current draft PR link | Git tag list, branch remote and public PR |
| Reproducibility table | Semantic `/ask` requires an OpenAI key before model loading; offline retrieval evaluation does not need a key but does need its local environment/model/index/server | LazyRetriever, evaluation script |
| CI claims | Listed actual triggers/stages/version pins and separated CI from historical container publishing/deployment | `.github/workflows/ci.yml` |
| Environment reload | Replaced restart advice with Compose container recreation after `.env` changes; native Uvicorn must be stopped/restarted | Compose `env_file` and cached runtime settings |
| Windows Arabic curl | Documented Git Bash/native curl argument-encoding limitation and verified UTF-8 PowerShell body alternative | Actual HTTP checks described below |
| Markdown structure | Corrected navigation heading depth, adjacent quote spacing, extra blank lines and author line-break syntax | Markdown lint and GitHub-compatible anchor validation |

## Validation executed

Temporary tooling and generated SVGs live under ignored `outputs/readme-review/`; project dependencies were not modified. The structured, secret-free result and complete 42-line command inventory are retained in [readme-review.json](evidence/readme-review.json).

| Check | Actual result |
|---|---|
| Markdown lint | Zero issues with markdownlint-cli2 0.24.0 / markdownlint 0.42.0 |
| Links and preservation | 57 heading anchors; 29 preserved numbered/Author section headings; 21 Markdown links checked; all local targets and fragments valid |
| External link/branch | Draft PR #4 returned HTTP 200; release branch exists remotely at the inspected commit |
| Mermaid | Mermaid CLI 12.0.0 / Mermaid 12.2.0 rendered all five diagrams successfully through headless Chrome |
| Command/config inventory | 19 runnable-language fences, 42 command lines, 12 referenced Python module names; source modules exist and parse; five runtime variable names/defaults match implementation |
| Isolated Docker startup | Separate local clone, blank `.env`, no local index or DVC config; image build succeeded and Compose became healthy |
| Cache independence | Fresh validation project's Hugging Face cache had zero entries after no-key checks |
| Actual HTTP smoke | Health, English exact, Arabic exact, empty-input 422 and missing-key 503 checks passed |
| API README examples | Health JSON matches exactly; all exact-response fields except the explicitly abbreviated answer match; all four curl JSON bodies exercised against the real API through TestClient, with generation requests returning expected no-key 503 |
| Shell examples | English curl passed through Git Bash; PowerShell UTF-8 Arabic example returned exact/ar/CC-91; inline Arabic Git Bash/native curl was corrupted and returned no-key 503, so it is explicitly excluded from Windows instructions |
| Artifact restoration | Restored into a fresh directory: 268 indexed documents / 162 corpus records |
| Corpus integrity | All corpus structure checks passed |
| DVC reproduction/status | Stage succeeded; `always changed` status is expected; original pointer preserved |
| CLI options | Artifact/smoke help and MLflow server help passed; documented flags exist |
| Ruff / whitespace | Ruff passed; `git diff --check` passed |
| Cleanup | Temporary Compose container/network shut down; existing user's configuration preserved |

### Tool commands

Installed scratch validators with Windows certificate trust enabled and Puppeteer browser download disabled (existing Chrome was used):

```powershell
$env:NODE_OPTIONS='--use-system-ca'
$env:PUPPETEER_SKIP_DOWNLOAD='true'
npm install --prefix outputs/readme-review/tools --cache outputs/readme-review/npm-cache --no-save --ignore-scripts --fetch-retries=1 --fetch-timeout=20000 mermaid markdown-it github-slugger @mermaid-js/mermaid-cli markdownlint-cli2
node outputs/readme-review/validate-markdown.mjs
.\outputs\readme-review\tools\node_modules\.bin\markdownlint-cli2.cmd --config outputs/readme-review/markdownlint.jsonc README.md
.\outputs\readme-review\tools\node_modules\.bin\mmdc.cmd -p outputs/readme-review/puppeteer.json -i README.md -o outputs/readme-review/diagrams.md
```

The local link checker parses CommonMark with markdown-it 15.0.3 and derives anchors using github-slugger. It compares retained sections and learning passages with the supplied source. Scratch scripts are workspace validation aids, not runtime prerequisites. Lint config disables line-length, bold-label-as-heading and table-alignment style rules; permits `<br>`; checks duplicate headings among siblings. These style allowances preserve the long educational prose/tables, while link/heading/fence/spacing checks remain enabled.

Mermaid Puppeteer config selected `C:/Program Files/Google/Chrome/Application/chrome.exe` with `headless: true`. Initial sandbox rendering failed with spawn EPERM; authorized host execution succeeded. An initial content-preservation check compared Windows CRLF against source LF; normalizing line endings resolved that harness mismatch without deleting content. Initial lint issues were fixed before the final passing result.

### Runtime commands

Created a separate clone with:

```sh
git clone --no-hardlinks --branch release/graduation-readiness . outputs/readme-review/checkout
```

Copied the revised README into it and created its blank `.env` from `.env.example`. Executed there:

```sh
docker compose -p readme-review up --build -d --wait --wait-timeout 180
docker compose -p readme-review config --quiet
docker compose -p readme-review down
```

Executed HTTP and CLI checks from the existing development environment:

```powershell
curl.exe --fail http://127.0.0.1:8000/health
.\.venv\Scripts\python.exe -m pipelines.smoke_api --expect-no-key
.\.venv\Scripts\python.exe -m civil_code_rag.release_artifact --output outputs/readme-review/restored-index
.\.venv\Scripts\python.exe -m pipelines.validate_corpus
.\.venv\Scripts\python.exe -m civil_code_rag.release_artifact --help
.\.venv\Scripts\python.exe -m pipelines.smoke_api --help
uv --cache-dir outputs/uv-cache run --locked --extra dev ruff check .
uv --cache-dir outputs/uv-cache run --locked --extra dev python -m pipelines.smoke_api --expect-no-key
uv --cache-dir outputs/uv-cache run --locked --extra dev mlflow server --help
```

DVC was run as `.\.venv\Scripts\python.exe -m dvc repro` and `status`, with the virtualenv Scripts directory added to PATH so its stage used the same interpreter. Read-only tag commands and the `v1.0.0` existence were inspected; no tag was changed. Remote branch verification used `git -c http.sslBackend=schannel ls-remote --exit-code --heads origin release/graduation-readiness`, preserving TLS verification.

## Deliberately not executed

- Historical PDF/page parsing, corpus/search rewriting, manifest regeneration and embedding rebuilding: require missing source inputs and/or overwrite frozen data. Paths, code and prerequisites were inspected; no success is claimed.
- A new MLflow server/evaluation run or Registry modification: CLI options and evaluation implementation were checked without altering an existing local backend. No new metrics or Registry state is claimed.
- Paid OpenAI requests: no-key errors and deterministic contracts suffice for this documentation review; prior live evidence remains in the release report.
- Tag creation/push, merge, deployment or registry publication: these are historical/conceptual workflows, not documentation validation steps.
- A full pytest rerun: no application code changed; relevant API examples and runtime smoke were checked directly. Previously recorded 81-test results are not represented as a fresh run in this review.
- A pristine operating-system/network benchmark: the separate clone had no developer artifacts but reused available Docker dependency/image caches. No first-install timing or memory guarantee is claimed.
