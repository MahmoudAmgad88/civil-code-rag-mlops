"""Verify the stable OpenAI request contract without network calls."""

from types import SimpleNamespace

import pytest

from civil_code_rag.generation.answer_generator import (
    SYSTEM_INSTRUCTIONS,
    AnswerGenerator,
)


class FakeResponses:
    """Capture an OpenAI request without making a network call."""

    def __init__(self):
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(output_text="Fake answer [CC-91].")


@pytest.mark.parametrize(
    ("question", "context"),
    [
        (
            "اشرح المادة ٩١",
            "[SOURCE: CC-91]\nArticle text:\nنص المادة ٩١.",
        ),
        (
            "Explain Article 91",
            "[SOURCE: CC-91]\nArticle text:\nArticle 91 text.",
        ),
    ],
)
def test_generator_request_contract(question, context):
    responses = FakeResponses()
    client = SimpleNamespace(responses=responses)
    generator = AnswerGenerator(
        client=client,
        model_name="gpt-4.1-mini",
    )
    answer = generator.generate(question=question, context=context)

    assert answer == "Fake answer [CC-91]."
    assert responses.last_request["model"] == "gpt-4.1-mini"
    assert responses.last_request["instructions"] == SYSTEM_INSTRUCTIONS
    assert responses.last_request["store"] is False
    assert question in responses.last_request["input"]
    assert context in responses.last_request["input"]
