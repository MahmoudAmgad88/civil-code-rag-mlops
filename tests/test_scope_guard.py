"""Unit tests for the scope guard business rule."""

from civil_code_rag.core.scope_guard import (
    is_explicitly_out_of_scope,
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