
"""Generate the first grounded answer using the OpenAI API."""

import os

from openai import OpenAI
from sentence_transformers import SentenceTransformer

from scripts.build_retrieval_context import (
    ARTICLES_PATH,
    build_context,
    load_article_lookup,
)

from scripts.search_articles import (
    MODEL_NAME,
    load_index,
    search_articles,
)

from civil_code_rag.generation.answer_generator import (
    AnswerGenerator,
    SYSTEM_INSTRUCTIONS,
)


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

LLM_MODEL = "gpt-4.1-mini"

#QUESTION = (
#    "What happens to the parties when a contract is rescinded?"
#)

#LANGUAGE = "en"

QUESTION = "متى ينتج التعبير عن الإرادة أثره القانوني؟"

LANGUAGE = "ar"



# --------------------------------------------------
# 3. Retrieve evidence
# --------------------------------------------------

def retrieve_evidence(question, language):
    """Retrieve relevant articles and build source-linked context."""

    # Load the embeddings that we already saved.
    embeddings, search_records = load_index()

    # Load the local embedding model.
    embedding_model = SentenceTransformer(MODEL_NAME)

    # Retrieve five candidate articles in the question's language.
    results = search_articles(
        question=question,
        language=language,
        model=embedding_model,
        embeddings=embeddings,
        records=search_records,
        top_k=5,
    )

    # Get the original article texts and PDF page references.
    article_lookup = load_article_lookup(ARTICLES_PATH)

    # Build the evidence that will be sent to the LLM.
    context = build_context(
        results=results,
        article_lookup=article_lookup,
        language=language,
    )

    return context


# --------------------------------------------------
# 4. Generate an answer
# --------------------------------------------------

def generate_answer(question: str, context: str) -> str:
    """Generate an answer through the new application component."""

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY is missing. Set it before running."
        )

    client = OpenAI()

    generator = AnswerGenerator(
        client=client,
        model_name=LLM_MODEL,
    )

    return generator.generate(
        question=question,
        context=context,
    )

# --------------------------------------------------
# 5. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    print("Retrieving relevant articles...")

    context = retrieve_evidence(
        question=QUESTION,
        language=LANGUAGE,
    )

    print("Sending evidence to OpenAI API...")

    answer = generate_answer(
        question=QUESTION,
        context=context,
    )

    print("\n" + "=" * 50)
    print("QUESTION")
    print("=" * 50)
    print(QUESTION)

    print("\n" + "=" * 50)
    print("GENERATED ANSWER")
    print("=" * 50)
    print(answer)