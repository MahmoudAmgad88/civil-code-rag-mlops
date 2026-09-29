"""Coordinate the Civil Code question-answering workflow."""

from civil_code_rag.core.query_router import route_question
from civil_code_rag.core.scope_guard import is_explicitly_out_of_scope
from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.retrieval.context_builder import build_context
from civil_code_rag.core.answer_rules import (
    detect_language,
    validate_citations,
)

class AmbiguousArticleRequestError(Exception):
    """The user's article request does not specify one supported intent."""

class ArticleTextUnavailableError(Exception):
    """The requested article has no original text in the requested language."""


class CitationValidationError(Exception):
    """The generated answer cites a source absent from its evidence."""


class ArticleNotFoundError(Exception):
    """The requested article is absent from the available corpus."""


class AskService:
    """Coordinate question routing and application components."""

    def __init__(
        self,
        repository: ArticleRepository,
        retriever,
        generator,
    ) -> None:
        self.repository = repository
        self.retriever = retriever
        self.generator = generator

    def ask(self, question: str) -> dict:
        """Process a question using the supported MVP routes."""

        question = question.strip()

        if not question:
            raise ValueError("Question must not be empty.")

        language = detect_language(question)

        # Reject explicitly unsupported domains before routing or retrieval.
        if is_explicitly_out_of_scope(question):
            message = (
                "السؤال خارج نطاق نسخة القانون المدني المتاحة في هذا المشروع."
                if language == "ar"
                else "This question is outside the available Civil Code corpus."
            )

            return {
                "route": "out_of_scope",
                "language": language,
                "answer": message,
                "article_id": None,
            }

        decision = route_question(question)

        # Retrieve an explicitly requested article without embeddings or LLM.
        if decision["route"] == "exact":
            article = self.repository.get(decision["article_id"])

            if article is None:
                raise ArticleNotFoundError(
                    "Article not found in the available corpus."
                )

            if article["alignment"] == "repealed":
                return {
                    "route": "exact",
                    "language": language,
                    "article_id": article["article_id"],
                    "answer": None,
                    "source_note": article["status_evidence"],
                    "verified_status": article["verified_status"],
                    "pdf_pages": [
                        article["page_start"],
                        article["page_end"],
                    ],
                }

            text_field = (
                "text_ar_original"
                if language == "ar"
                else "text_en_original"
            )

            return {
                "route": "exact",
                "language": language,
                "article_id": article["article_id"],
                "answer": article[text_field],
                "source_note": None,
                "verified_status": article["verified_status"],
                "pdf_pages": [
                    article["page_start"],
                    article["page_end"],
                ],
            }

        if decision["route"] == "unsupported":
            raise AmbiguousArticleRequestError(
                "Article request is ambiguous. "
                "Ask for the article text or its explanation."
            )

        if decision["route"] == "explain":
            article = self.repository.get(decision["article_id"])

            if article is None:
                raise ArticleNotFoundError(
                    "Article not found in the available corpus."
                )

            # A source note is not the original article text.
            # Never ask the LLM to invent an explanation for it.
            if article["alignment"] == "repealed":
                message = (
                    "النص الأصلي للمادة غير متاح في المصدر الحالي. "
                    "توجد ملاحظة في المصدر عن المواد 54–80، "
                    "لكن الحالة القانونية الحالية لم يتم التحقق منها."
                    if language == "ar"
                    else
                    "The original article text is unavailable in this source. "
                    "The source contains a note about Articles 54–80, "
                    "but the current legal status has not been verified."
                )

                return {
                    "route": "explain",
                    "intent": "explain",
                    "language": language,
                    "article_id": article["article_id"],
                    "answer": None,
                    "message": message,
                    "source_note": article["status_evidence"],
                    "verified_status": article["verified_status"],
                    "pdf_pages": [
                        article["page_start"],
                        article["page_end"],
                    ],
                    "cited_article_ids": [],
                }

            text_field = (
                "text_ar_original"
                if language == "ar"
                else "text_en_original"
            )

            if not article[text_field]:
                raise ArticleTextUnavailableError(
                    "The requested article text is unavailable "
                    "in this language in the current corpus."
                )

            # Use the requested article only. No semantic retrieval.
            results = [
                {
                    "record": {
                        "article_id": article["article_id"],
                        "language": language,
                    }
                }
            ]

            context = build_context(
                results=results,
                article_lookup=self.repository.articles,
                language=language,
            )

            answer = self.generator.generate(
                question=question,
                context=context,
            )

            try:
                cited_ids = validate_citations(answer, context)
            except ValueError:
                raise CitationValidationError(
                    "Generated answer failed citation validation."
                ) from None

            return {
                "route": "explain",
                "intent": "explain",
                "language": language,
                "article_id": article["article_id"],
                "answer": answer,
                "cited_article_ids": sorted(cited_ids),
            }


        if decision["route"] == "semantic":
            results = self.retriever.search(
                question=question,
                language=language,
                top_k=5,
            )

            context = build_context(
                results=results,
                article_lookup=self.repository.articles,
                language=language,
            )

            answer = self.generator.generate(
                question=question,
                context=context,
            )

            try:
                cited_ids = validate_citations(answer, context)
            except ValueError:
                raise CitationValidationError(
                    "Generated answer failed citation validation."
                ) from None

            return {
                "route": "semantic",
                "intent": "semantic",
                "language": language,
                "answer": answer,
                "cited_article_ids": sorted(cited_ids),
            }
        # Semantic retrieval will be migrated in the next step.
        raise NotImplementedError(
            f"AskService route not migrated yet: {decision['route']}"
        )