"""Unit tests for the scope guard business rule."""

from civil_code_rag.core.scope_guard import (
    is_explicitly_out_of_scope,
)

from scripts.scope_guard import (
    is_explicitly_out_of_scope as legacy_scope_guard,
)


def test_arabic_penal_code_is_out_of_scope():
    question = "ما عقوبة القتل في قانون العقوبات المصري؟"

    assert is_explicitly_out_of_scope(question) is True


def test_english_penal_code_is_out_of_scope():
    question = "What does the Egyptian Penal Code say?"

    assert is_explicitly_out_of_scope(question) is True


def test_civil_code_question_is_not_explicitly_out_of_scope():
    question = "متى ينتج التعبير عن الإرادة أثره القانوني؟"

    assert is_explicitly_out_of_scope(question) is False


def test_legacy_import_uses_the_same_function():
    assert legacy_scope_guard is is_explicitly_out_of_scope
