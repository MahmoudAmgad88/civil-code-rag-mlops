"""Pydantic request and response contracts for the HTTP API."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Question submitted to the RAG application."""

    question: str = Field(min_length=1)


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ExactResponse(BaseModel):
    route: Literal["exact"]
    language: Literal["ar", "en"]
    article_id: str
    answer: str | None
    source_note: str | None
    verified_status: str
    pdf_pages: list[int]


class ExplainResponse(BaseModel):
    route: Literal["explain"]
    intent: Literal["explain"]
    language: Literal["ar", "en"]
    article_id: str
    answer: str | None
    cited_article_ids: list[str]
    message: str | None = None
    source_note: str | None = None
    verified_status: str | None = None
    pdf_pages: list[int] | None = None


class SemanticResponse(BaseModel):
    route: Literal["semantic"]
    intent: Literal["semantic"]
    language: Literal["ar", "en"]
    answer: str
    cited_article_ids: list[str]


class OutOfScopeResponse(BaseModel):
    route: Literal["out_of_scope"]
    language: Literal["ar", "en"]
    answer: str
    article_id: None


AskResponse = Annotated[
    ExactResponse | ExplainResponse | SemanticResponse | OutOfScopeResponse,
    Field(discriminator="route"),
]
