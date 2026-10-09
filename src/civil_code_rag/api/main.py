"""FastAPI application backed by the package-level AskService."""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from civil_code_rag.api.dependencies import get_ask_service
from civil_code_rag.api.schemas import AskRequest, AskResponse, HealthResponse
from civil_code_rag.services.ask_service import (
    AmbiguousArticleRequestError,
    ArticleNotFoundError,
    ArticleTextUnavailableError,
    AskService,
    CitationValidationError,
)

app = FastAPI(title="Civil Code RAG — Local MVP")


@app.get("/health", response_model=HealthResponse)
def health() -> dict[str, str]:
    """Report that the API process is available without loading RAG resources."""

    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse, response_model_exclude_unset=True)
def ask_endpoint(
    request: AskRequest,
    service: Annotated[AskService, Depends(get_ask_service)],
) -> dict:
    """Validate input, delegate to AskService, and translate application errors."""

    try:
        return service.ask(request.question)
    except ArticleNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except CitationValidationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    except (
        AmbiguousArticleRequestError,
        ArticleTextUnavailableError,
        ValueError,
    ) as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
