"""Retrieve an article directly by its unique article ID."""

from scripts.build_retrieval_context import (
    ARTICLES_PATH,
    load_article_lookup,
)


def exact_lookup(article_id, article_lookup):
    """Return the requested article without using embeddings."""

    return article_lookup.get(article_id)


def display_article(article, language="ar"):
    """Display the original article text or its source status."""

    if article is None:
        print("Article not found in the available corpus.")
        return

    article_id = article["article_id"]

    print(f"\nArticle: {article_id}")
    print(
        f"PDF pages: "
        f"{article['page_start']}-{article['page_end']}"
    )

    # Repealed articles have no individual article text.
    if article["source_status"] == "repealed_per_source_note":
        print("\nNo original article text is available in this PDF.")
        print("Source note:")
        print(article["status_evidence"])
        print("Current legal status: unverified")
        return

    # Display the original text in the requested language.
    text_field = (
        "text_ar_original"
        if language == "ar"
        else "text_en_original"
    )

    original_text = article[text_field]

    if original_text:
        print("\nArticle text:")
        print(original_text)
    else:
        print(
            f"\nNo {language} article text is available "
            "in this corpus."
        )

    if article["issues"]:
        print(f"\nExtraction issues: {article['issues']}")

    print(f"Current legal status: {article['verified_status']}")


if __name__ == "__main__":

    # Load the article records once.
    article_lookup = load_article_lookup(ARTICLES_PATH)

    # Start with a repealed article.
    #article = exact_lookup("CC-60", article_lookup)
    article = exact_lookup("CC-91", article_lookup)

    display_article(article, language="ar")