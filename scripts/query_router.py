"""Route Civil Code questions by article reference and user intent."""

import re


ARTICLE_PATTERN = re.compile(
    r"(?:الماد[ةه]|article)\s*([0-9٠-٩۰-۹]+)",
    re.IGNORECASE,
)

DIGIT_MAP = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)

SHOW_TEXT_PATTERN = re.compile(
    r"ما\s+نص"
    r"|اعرض\w*"
    r"|هات"
    r"|اكتب"
    r"|show\b"
    r"|give\s+me"
    r"|what\s+does.+\bsay\b",
    re.IGNORECASE,
)

EXPLAIN_PATTERN = re.compile(
    r"اشرح\w*"
    r"|فسر\w*"
    r"|فهمني"
    r"|شرح"
    r"|وضح\w*"
    r"|explain\b"
    r"|what\s+does.+\bmean\b",
    re.IGNORECASE,
)


def route_question(question):
    """Select show_text, explain, or semantic retrieval."""

    if not question.strip():
        raise ValueError("Question must not be empty.")

    # Find all explicitly mentioned article numbers.
    matches = ARTICLE_PATTERN.findall(question)

    # No article number: use the existing semantic path.
    if not matches:
        return {
            "route": "semantic",
            "intent": "semantic",
            "article_id": None,
        }

    article_numbers = {
        int(digits.translate(DIGIT_MAP))
        for digits in matches
    }

    # Multiple different articles need separate handling.
    if len(article_numbers) != 1:
        return {
            "route": "unsupported",
            "intent": "ambiguous",
            "article_id": None,
        }

    article_number = article_numbers.pop()
    article_id = f"CC-{article_number}"

    wants_text = bool(SHOW_TEXT_PATTERN.search(question))
    wants_explanation = bool(EXPLAIN_PATTERN.search(question))

    if wants_text and not wants_explanation:
        return {
            "route": "exact",
            "intent": "show_text",
            "article_id": article_id,
        }

    if wants_explanation and not wants_text:
        return {
            "route": "explain",
            "intent": "explain",
            "article_id": article_id,
        }

    # Explicit article reference, but unclear intent:
    # do not silently search for a different article.
    return {
        "route": "unsupported",
        "intent": "ambiguous",
        "article_id": article_id,
    }


if __name__ == "__main__":
    questions = [
        "ما نص المادة ٩١؟",
        "اشرحلي المادة ٩١ ببساطة.",
        "What does Article 91 say?",
        "Explain Article 91",
        "متى ينتج التعبير عن الإرادة أثره القانوني؟",
    ]

    for question in questions:
        print(question)
        print(route_question(question))
        print()