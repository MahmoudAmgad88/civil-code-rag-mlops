"""Language detection and source-citation validation."""

import re


def detect_language(question: str) -> str:
    """Detect Arabic or English using the existing MVP rule."""

    if re.search(r"[\u0621-\u064A]", question):
        return "ar"

    return "en"


def validate_citations(answer: str, context: str) -> set[str]:
    """Reject citations to source IDs absent from the supplied context."""

    allowed_ids = set(
        re.findall(r"\[SOURCE:\s*((?:CC|PROM)-\d+)\]", context)
    )

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