"""Build source-linked context from retrieved Civil Code records."""


def build_context(
    results: list[dict],
    article_lookup: dict[str, dict],
    language: str,
) -> str:
    """Return original article texts with source IDs and PDF page references."""

    context_parts = []

    for result in results:
        search_record = result["record"]
        article_id = search_record["article_id"]

        article = article_lookup[article_id]

        if search_record["language"] != language:
            raise ValueError("Retrieved record language mismatch.")

        text_field = (
            "text_ar_original"
            if language == "ar"
            else "text_en_original"
        )

        original_text = article[text_field]

        if not original_text:
            raise ValueError(
                f"No {language} source text for {article_id}"
            )

        source_block = (
            f"[SOURCE: {article_id}]\n"
            f"PDF pages: {article['page_start']}"
            f"-{article['page_end']}\n"
            f"Article text:\n{original_text}"
        )

        context_parts.append(source_block)

    return "\n\n---\n\n".join(context_parts)