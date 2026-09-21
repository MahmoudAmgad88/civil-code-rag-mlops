"""Local FastAPI interface for the Civil Code RAG MVP."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from scripts.ask import detect_language, validate_citations
from scripts.build_retrieval_context import (
    ARTICLES_PATH,
    load_article_lookup,
)
from scripts.exact_lookup import exact_lookup
from scripts.first_llm_call import (
    generate_answer,
    retrieve_evidence,
)
from scripts.query_router import route_question
from scripts.scope_guard import is_explicitly_out_of_scope


# --------------------------------------------------
# 1. Create the application
# --------------------------------------------------

app = FastAPI(title="Civil Code RAG — Local MVP")


# --------------------------------------------------
# 2. Define the request format
# --------------------------------------------------

class AskRequest(BaseModel):
    """The JSON body expected by POST /ask."""

    question: str = Field(min_length=1)


# --------------------------------------------------
# 3. Health endpoint
# --------------------------------------------------

@app.get("/health")
def health():
    """Check that the API process is running."""

    return {"status": "ok"}


# --------------------------------------------------
# 4. Ask endpoint
# --------------------------------------------------

@app.post("/ask")
def ask_endpoint(request: AskRequest):
    """Route a question to exact lookup or semantic RAG."""

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question must not be empty.",
        )

    language = detect_language(question)

    # Reject the explicit out-of-scope cases covered by our MVP guard.
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

    # ----------------------------------------------
    # Exact lookup: no embedding or LLM call
    # ----------------------------------------------

    if decision["route"] == "exact":
        article_lookup = load_article_lookup(ARTICLES_PATH)

        article = exact_lookup(
            decision["article_id"],
            article_lookup,
        )

        if article is None:
            raise HTTPException(
                status_code=404,
                detail="Article not found in the available corpus.",
            )

        # A repealed record contains a source note,
        # not the original body of the article.
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

    # ----------------------------------------------
    # Ambiguous article requests
    # ----------------------------------------------

    if decision["route"] == "unsupported":
        raise HTTPException(
            status_code=422,
            detail=(
                "Article request is ambiguous. "
                "Ask for the article text or its explanation."
            ),
        )

    # ----------------------------------------------
    # Explain a specifically requested article
    # ----------------------------------------------

    if decision["route"] == "explain":

        article_lookup = load_article_lookup(ARTICLES_PATH)

        article = exact_lookup(
            decision["article_id"],
            article_lookup,
        )

        if article is None:
            raise HTTPException(
                status_code=404,
                detail="Article not found in the available corpus.",
            )

        # The PDF contains a repeal note, not the article's original text.
        # Do not send this record to the LLM for an explanation.
        if article["source_status"] == "repealed_per_source_note":

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

        article_text = article[text_field]

        if not article_text:
            raise HTTPException(
                status_code=422,
                detail=(
                    "The requested article text is unavailable "
                    "in this language in the current corpus."
                ),
            )

        # The user specified an article.
        # Use only that article as evidence.
        context = (
            f"[SOURCE: {article['article_id']}]\n"
            f"PDF pages: {article['page_start']}-{article['page_end']}\n"
            f"Article text:\n{article_text}"
        )

        answer = generate_answer(
            question=question,
            context=context,
        )

        try:
            cited_ids = validate_citations(answer, context)
        except ValueError:
            raise HTTPException(
                status_code=502,
                detail="Generated answer failed citation validation.",
            ) from None

        return {
            "route": "explain",
            "intent": "explain",
            "language": language,
            "article_id": article["article_id"],
            "answer": answer,
            "cited_article_ids": sorted(cited_ids),
        }

    # ----------------------------------------------
    # Semantic RAG: no specific article requested
    # ----------------------------------------------

    context = retrieve_evidence(
        question=question,
        language=language,
    )

    answer = generate_answer(
        question=question,
        context=context,
    )

    try:
        cited_ids = validate_citations(answer, context)
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Generated answer failed citation validation.",
        ) from None

    return {
        "route": "semantic",
        "intent": "semantic",
        "language": language,
        "answer": answer,
        "cited_article_ids": sorted(cited_ids),
    }