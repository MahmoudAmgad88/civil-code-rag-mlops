"""Detect a few explicitly out-of-scope questions for the MVP."""

import re


OUT_OF_SCOPE_PATTERNS = [
    # Arabic: explicit Egyptian Penal Code requests.
    re.compile(r"قانون\s+العقوبات"),

    # English: explicit Penal Code requests.
    re.compile(r"\bpenal\s+code\b", re.IGNORECASE),
]


def is_explicitly_out_of_scope(question):
    """Return True for a clearly identified unsupported legal domain."""

    return any(
        pattern.search(question)
        for pattern in OUT_OF_SCOPE_PATTERNS
    )


if __name__ == "__main__":

    questions = [
        "ما عقوبة جريمة القتل العمد في قانون العقوبات المصري؟",
        "What is the punishment for murder under the Egyptian Penal Code?",
        "متى ينتج التعبير عن الإرادة أثره القانوني؟",
        "What happens when a contract is rescinded?",
    ]

    for question in questions:
        print(
            f"{is_explicitly_out_of_scope(question)} | {question}"
        )