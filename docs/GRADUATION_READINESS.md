# Graduation readiness

Assessment: 25 October 2026, Cairo. Overall: **PARTIALLY READY for the full graduation rubric**. The core no-key release path has been validated from a separate clone. Advanced rubric compliance is incomplete; see `GRADUATION_GAPS.md`. Validation continued after the requested noon deadline; no claim is made that this release was delivered before it.

## Initial inspection, before implementation

The starting branch was `docs/peer-review`. User changes were a modified `.gitignore` and an untracked `.env.example`; they were preserved. No AGENTS.md was found by repository file search.

| Area | Initial status | Inspection evidence |
|---|---|---|
| Bilingual exact/explain/semantic routing, source notes, citations | PASS | OOP service/repository/retrieval/generation modules and existing API tests |
| Runtime configuration | PARTIAL | Four prefixed settings existed, but `.env.example` listed only the key and local `.env` was not loaded explicitly |
| Health contract | PARTIAL | Only `{"status":"ok"}`; no indexed-document count |
| CPU Docker | PARTIAL | Locked CPU dependencies; index absent from image and required an external mount |
| Docker Compose | MISSING | No Compose file |
| DVC | PARTIAL | Original index pointer exists; shared configuration has no public remote, local-only remote lives in ignored config; no pipeline |
| Retrieval evaluation / MLflow | PARTIAL | Recall@K/MRR/latency and MLflow logging exist; comparative/Registry evidence not distributed |
| CI | PARTIAL | Locked install, Ruff and pytest existed; no artifact reproduction or Docker smoke |
| Production serving/monitoring/advanced evaluation | MISSING/PARTIAL | FastAPI exists; requested advanced components absent |
| Clean-machine documentation | PARTIAL | Setup depended on local index and Windows-specific mount instructions |

## Release assessment

| Requirement | Status | Evidence | Remaining action |
|---|---|---|---|
| Dedicated branch and preserved history | PASS | `release/graduation-readiness`; draft PR #4; logical commits; original user ignore changes remain unstaged | Review draft PR before merging |
| Required environment variables / no-key behavior | PASS | Five entries in `.env.example`; standard `OPENAI_API_KEY`; actual no-key HTTP checks | Evaluator supplies a valid key for generation |
| Secret hygiene | PASS (bounded inspection) | `.env` ignored/excluded; tracked-file/history pattern scan found no key candidates; safe summary under `docs/evidence` | Pattern scan is not a complete credential/security audit |
| API health + counts | PASS | HTTP 200: 268 indexed documents, 162 corpus records; corrupt/missing data tested as 503 | None for frozen release |
| Empty input / bilingual exact lookup / citations | PASS | 81-test existing Windows suite, 81-test ephemeral Linux suite and bilingual HTTP smoke; additive exact citation field | None for frozen contract |
| Missing key / sanitized upstream errors | PASS | Generated routes return 503 before model load; fake upstream failures tested | Validate evaluator key/model permissions |
| CPU Docker / Compose / non-root execution | PASS | Successful builds, uid 1000, fresh named volume, healthy container and no-key smoke | Other OS/CPU architectures not validated |
| Checkout-independent index distribution | PASS | 415,196-byte Git archive; checksums; separate clone built without original index or DVC config | Git archive approach should be replaced by shared storage if artifact grows |
| DVC restoration and original metadata | PASS | `dvc repro` succeeded; original `data/index.dvc` unchanged; offline archive fallback | Shared remote remains unavailable; not needed by startup |
| Corpus/index integrity | PASS | Corpus validator; restoration checks; mandatory index test; 268 x 384 finite unit vectors | Full PDF extraction cannot be rebuilt without source PDF |
| Locked dependencies | PARTIAL | Existing environment locked sync passed; clean Windows dev install used system certificate store; Docker installed locked CPU dependencies | Fresh native Windows pytest hits OpenSSL_Applink failure; fresh Windows embeddings not installed; use validated Docker path |
| Cached embedding compatibility | PASS | All 268 regenerated vectors matched exactly (maximum absolute difference 0.0) at pinned revision | Hardware/library changes may introduce numerical differences |
| First-run model download | PASS | Separate clone's Linux container downloaded model into fresh cache; reported dimension 384 | Requires internet; timing/peak memory not benchmarked |
| Live semantic generation | PASS | Clean-clone CPU container returned semantic/en, cited CC-91, nonempty answer using the existing key | Evaluator supplies their own valid key; latency/quality beyond this smoke is unmeasured |
| CI graduation checks | PARTIAL | Workflow now restores/validates artifacts, tests and builds/smokes Docker | Remote workflow must run on the final pushed commit |
| README clean-machine commands | PASS | Documented primary Compose startup validated in separate clone; no developer index mount | Follow certificate troubleshooting where applicable |
| Full graduation rubric | PARTIAL | Explicit gap matrix; no fabricated scores, registry state or production claims | Resolve RAGAS, comparisons, serving and monitoring requirements with instructor |

Exact validation commands, successes and failed attempts are recorded in `CLEAN_MACHINE_VALIDATION.md`.
