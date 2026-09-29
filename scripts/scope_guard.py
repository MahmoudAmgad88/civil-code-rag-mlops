"""Compatibility wrapper for the legacy MVP imports."""

from civil_code_rag.core.scope_guard import is_explicitly_out_of_scope

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