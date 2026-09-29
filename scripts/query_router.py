"""Compatibility wrapper for legacy query-router imports."""

from civil_code_rag.core.query_router import route_question

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