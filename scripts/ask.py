
"""Ask a question using exact lookup or semantic RAG."""

import re

from scripts.build_retrieval_context import (
    ARTICLES_PATH,
    load_article_lookup,
)
from scripts.exact_lookup import (
    display_article,
    exact_lookup,
)
from scripts.first_llm_call import (
    generate_answer,
    retrieve_evidence,
)
from scripts.query_router import route_question

from scripts.scope_guard import is_explicitly_out_of_scope

def detect_language(question):
    """Detect the question language for our simple Arabic/English MVP."""

    # Arabic letters -> Arabic question.
    if re.search(r"[\u0621-\u064A]", question):
        return "ar"

    # Otherwise, use English for this bilingual MVP.
    return "en"

def validate_citations(answer, context):
    """Reject article citations that are absent from retrieved sources."""

    # Source IDs available in the context sent to the LLM.
    allowed_ids = set(
        re.findall(r"\[SOURCE:\s*((?:CC|PROM)-\d+)\]", context)
    )

    # Article IDs cited in the generated answer.
    cited_ids = set(
        re.findall(r"\[((?:CC|PROM)-\d+)\]", answer)
    )

    unknown_ids = cited_ids - allowed_ids

    if unknown_ids:
        raise ValueError(
            f"Answer cites sources that were not retrieved: "
            f"{sorted(unknown_ids)}"
        )

    return cited_ids

def ask(question):
    """Route one question and display its result."""

    if not question.strip():
        raise ValueError("Question must not be empty.")



    # Reject explicitly unsupported legal domains before retrieval.
    if is_explicitly_out_of_scope(question):

        language = detect_language(question)

        if language == "ar":
            print(
                "السؤال خارج نطاق نسخة القانون المدني "
                "المتاحة في هذا المشروع."
            )
        else:
            print(
                "This question is outside the scope of the "
                "Civil Code corpus available in this project."
            )

        return

    # 1. Decide which retrieval path to use.
    decision = route_question(question)

    # 2. Identify the requested language.
    language = detect_language(question)

    print(f"\nRoute: {decision['route']}")
    print(f"Language: {language}")

    # 3. Handle explicit article-text requests.
    if decision["route"] == "exact":

        article_lookup = load_article_lookup(ARTICLES_PATH)

        article = exact_lookup(
            decision["article_id"],
            article_lookup,
        )

        # Display the requested article without calling the LLM.
        display_article(article, language=language)

        return

    # 4. Handle semantic questions.
    context = retrieve_evidence(
        question=question,
        language=language,
    )

    # Send the retrieved evidence to the OpenAI API.
    answer = generate_answer(
        question=question,
        context=context,
    )

    cited_ids = validate_citations(answer, context)

    print(f"\nCited source IDs: {sorted(cited_ids)}")


    print("\n" + "=" * 50)
    print("GENERATED ANSWER")
    print("=" * 50)
    print(answer)


if __name__ == "__main__":

    # Ask one question each time the script runs.
    user_question = input("Enter your question: ").strip()

    ask(user_question)