"""Unit tests for grounded answer generation."""

from types import SimpleNamespace

from civil_code_rag.generation.answer_generator import (
    AnswerGenerator,
)


class FakeResponses:
    """Capture an LLM request and return a controlled response."""

    def __init__(self):
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs

        return SimpleNamespace(
            output_text="الإجابة التجريبية [CC-91]."
        )


def test_generate_passes_question_and_evidence_to_llm():
    fake_responses = FakeResponses()
    fake_client = SimpleNamespace(responses=fake_responses)

    generator = AnswerGenerator(
        client=fake_client,
        model_name="test-model",
    )

    answer = generator.generate(
        question="اشرح المادة ٩١",
        context="[SOURCE: CC-91]\nArticle text:\nنص المادة.",
    )

    request = fake_responses.last_request

    assert answer == "الإجابة التجريبية [CC-91]."

    assert request["model"] == "test-model"
    assert "اشرح المادة ٩١" in request["input"]
    assert "[SOURCE: CC-91]" in request["input"]
    assert "نص المادة." in request["input"]

    assert "Answer using only the provided SOURCE excerpts" in (
        request["instructions"]
    ) or "Answer using only the provided SOURCE excerpts".lower() in (
        request["instructions"].lower()
    )

    assert request["store"] is False


def test_generate_returns_the_client_response_unchanged():
    fake_responses = FakeResponses()
    fake_client = SimpleNamespace(responses=fake_responses)

    generator = AnswerGenerator(
        client=fake_client,
        model_name="test-model",
    )

    answer = generator.generate(
        question="What does Article 91 say?",
        context="[SOURCE: CC-91]\nArticle text:\nExample text.",
    )

    assert answer == "الإجابة التجريبية [CC-91]."