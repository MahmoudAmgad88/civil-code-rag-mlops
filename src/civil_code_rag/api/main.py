"""FastAPI application backed by the package-level AskService."""

import time
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from civil_code_rag.api.dependencies import ServiceUnavailableError, get_ask_service
from civil_code_rag.api.observability import (
    AUDITED_PATHS,
    METRICS,
    REQUEST_ID_HEADER,
    build_audit_record,
    metric_path,
    question_fingerprint,
    resolve_request_id,
    write_audit,
)
from civil_code_rag.api.schemas import AskRequest, AskResponse, HealthResponse
from civil_code_rag.api.security import require_client
from civil_code_rag.config import get_settings
from civil_code_rag.release_artifact import inspect_health
from civil_code_rag.services.ask_service import (
    AmbiguousArticleRequestError,
    ArticleNotFoundError,
    ArticleTextUnavailableError,
    AskService,
    CitationValidationError,
)

app = FastAPI(title="Civil Code RAG â€” Local MVP")


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    """Attach a request ID, then record metrics and an audit line per request."""

    request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id
    request.state.audit = {}
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
    finally:
        latency = time.perf_counter() - started
        path = metric_path(request.url.path)
        METRICS.observe_request(request.method, path, status_code, latency)
        if path in AUDITED_PATHS:
            settings = get_settings()
            record = build_audit_record(
                request_id=request_id,
                method=request.method,
                path=path,
                status_code=status_code,
                latency_seconds=latency,
                audit=request.state.audit,
                settings=settings,
            )
            if path == "/ask":
                METRICS.observe_ask(record["outcome"], record["route"])
            write_audit(record, settings)


@app.get("/health", response_model=HealthResponse)
def health() -> dict:
    """Report that the API process is available without loading RAG resources."""

    try:
        return inspect_health(get_settings())
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(
            503, "Corpus or retrieval index is unavailable or invalid."
        ) from None


@app.get(
    "/metrics",
    response_class=PlainTextResponse,
    dependencies=[Depends(require_client)],
)
def metrics() -> PlainTextResponse:
    """Expose request, latency and answer-outcome metrics in Prometheus format."""

    return PlainTextResponse(
        METRICS.render(), media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.post(
    "/ask",
    response_model=AskResponse,
    response_model_exclude_unset=True,
    dependencies=[Depends(require_client)],
)
def ask_endpoint(
    request: AskRequest,
    http_request: Request,
    service: Annotated[AskService, Depends(get_ask_service)],
) -> dict:
    """Validate input, delegate to AskService, and translate application errors."""

    audit = http_request.state.audit
    audit["question_sha256"] = question_fingerprint(request.question)
    audit["question_chars"] = len(request.question)
    try:
        result = service.ask(request.question)
    except ServiceUnavailableError as error:
        audit["outcome"] = "service_unavailable"
        raise HTTPException(status_code=503, detail=str(error)) from None
    except ArticleNotFoundError as error:
        audit["outcome"] = "not_found"
        raise HTTPException(status_code=404, detail=str(error)) from None
    except CitationValidationError as error:
        audit["outcome"] = "citation_validation_failed"
        raise HTTPException(status_code=502, detail=str(error)) from None
    except (
        AmbiguousArticleRequestError,
        ArticleTextUnavailableError,
        ValueError,
    ) as error:
        audit["outcome"] = "invalid_request"
        raise HTTPException(status_code=422, detail=str(error)) from None
    route = result.get("route")
    audit["route"] = route
    audit["language"] = result.get("language")
    audit["cited_article_ids"] = result.get("cited_article_ids", [])
    audit["outcome"] = "out_of_scope" if route == "out_of_scope" else "answered"
    return result
