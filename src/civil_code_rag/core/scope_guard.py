"""Detect explicitly unsupported legal domains in the current MVP."""

import re


OUT_OF_SCOPE_PATTERNS = [
    re.compile(r"قانون\s+العقوبات"),
    re.compile(r"\bpenal\s+code\b", re.IGNORECASE),
]


def is_explicitly_out_of_scope(question: str) -> bool:
    """Return True for the explicitly unsupported domains covered by the MVP."""

    return any(
        pattern.search(question)
        for pattern in OUT_OF_SCOPE_PATTERNS
    )