"""Run real HTTP health and bilingual exact-lookup checks without an API key."""

import argparse
import json
import urllib.error
import urllib.request


def request(base_url, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url + path, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--expect-no-key", action="store_true")
    parser.add_argument(
        "--live-generation",
        action="store_true",
        help="Make one paid OpenAI semantic request",
    )
    args = parser.parse_args()
    status, health = request(args.base_url, "/health")
    assert status == 200 and health == {
        "status": "ok",
        "indexed_document_count": 268,
        "corpus_record_count": 162,
    }, (status, health)
    checks = ["health"]
    for question, language in [
        ("What does Article 91 say?", "en"),
        (
            "\u0645\u0627 \u0646\u0635 \u0627\u0644\u0645\u0627\u062f\u0629 \u0669\u0661\u061f",
            "ar",
        ),
    ]:
        status, result = request(args.base_url, "/ask", {"question": question})
        assert (
            status == 200
            and result["route"] == "exact"
            and result["language"] == language
        ), (status, result)
        assert result["article_id"] == "CC-91" and result["cited_article_ids"] == [
            "CC-91"
        ]
        assert result["answer"]
        checks.append("exact_" + language)
    for question in ["", "   "]:
        status, result = request(args.base_url, "/ask", {"question": question})
        assert status == 422, (status, result)
    checks.append("empty_input_422")
    if args.expect_no_key:
        for question in [
            "Explain Article 91",
            "When does an expression of intent take effect?",
        ]:
            status, result = request(args.base_url, "/ask", {"question": question})
            assert status == 503 and "OPENAI_API_KEY" in result["detail"], (
                status,
                result,
            )
        checks.append("missing_key_503")
    if args.live_generation:
        status, result = request(
            args.base_url,
            "/ask",
            {"question": "When does an expression of intent take effect?"},
        )
        assert (
            status == 200
            and result["route"] == "semantic"
            and result["cited_article_ids"]
        ), (status, result)
        checks.append("live_semantic_generation")
    print(json.dumps({"status": "pass", "checks": checks}))


if __name__ == "__main__":
    main()
