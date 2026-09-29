"""Verify that the new and legacy generators build identical LLM requests."""

from types import SimpleNamespace

import pytest

import scripts.first_llm_call as legacy
from civil_code_rag.generation.answer_generator import AnswerGenerator


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
def test_new_generator_matches_legacy_request(
    monkeypatch,
    question,
    context,
):
    # Give each implementation its own request recorder.
    legacy_responses = FakeResponses()
    new_responses = FakeResponses()

    legacy_client = SimpleNamespace(responses=legacy_responses)
    new_client = SimpleNamespace(responses=new_responses)

    # Satisfy the legacy API-key check using a dummy value.
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Prevent the legacy function from creating a real OpenAI client.
    monkeypatch.setattr(
        legacy,
        "OpenAI",
        lambda: legacy_client,
    )

    legacy_answer = legacy.generate_answer(
        question=question,
        context=context,
    )

    generator = AnswerGenerator(
        client=new_client,
        model_name=legacy.LLM_MODEL,
    )

    new_answer = generator.generate(
        question=question,
        context=context,
    )

    assert new_answer == legacy_answer
    assert new_responses.last_request == legacy_responses.last_request
    assert new_responses.last_request["store"] is False