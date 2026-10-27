"""Run real HTTP health, auth, metrics and bilingual exact-lookup checks."""

import argparse
import json
import os
import urllib.error
import urllib.request

DEMO_API_KEY = "local-demo-key-change-me"


def request(base_url, path, payload=None, api_key=None, request_id=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    if request_id:
        headers["X-Request-ID"] = request_id
    req = urllib.request.Request(base_url + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            body = response.read().decode("utf-8")
            content_type = response.headers.get("Content-Type", "")
            parsed = json.loads(body) if "json" in content_type else body
            request.last_request_id = response.headers.get("X-Request-ID")
            return response.status, parsed
    except urllib.error.HTTPError as error:
        request.last_request_id = error.headers.get("X-Request-ID")
        return error.code, json.load(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("CIVIL_CODE_RAG_SMOKE_API_KEY", DEMO_API_KEY),
        help="Value sent in X-API-Key (defaults to the .env.example demo key)",
    )
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
    key = args.api_key
    status, result = request(
        args.base_url, "/ask", {"question": "What does Article 91 say?"}
    )
    assert status == 401, (status, result)
    checks.append("missing_api_key_401")
    status, result = request(
        args.base_url,
        "/ask",
        {"question": "What does Article 91 say?"},
        api_key=key,
        request_id="smoke-request-1",
    )
    assert status == 200 and request.last_request_id == "smoke-request-1", (
        status,
        request.last_request_id,
    )
    checks.append("request_id_echo")
    for question, language in [
        ("What does Article 91 say?", "en"),
        (
            "\u0645\u0627 \u0646\u0635 \u0627\u0644\u0645\u0627\u062f\u0629 \u0669\u0661\u061f",
            "ar",
        ),
    ]:
        status, result = request(
            args.base_url, "/ask", {"question": question}, api_key=key
        )
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
        status, result = request(
            args.base_url, "/ask", {"question": question}, api_key=key
        )
        assert status == 422, (status, result)
    checks.append("empty_input_422")
    if args.expect_no_key:
        for question in [
            "Explain Article 91",
            "When does an expression of intent take effect?",
        ]:
            status, result = request(
                args.base_url, "/ask", {"question": question}, api_key=key
            )
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
            api_key=key,
        )
        assert (
            status == 200
            and result["route"] == "semantic"
            and result["cited_article_ids"]
        ), (status, result)
        checks.append("live_semantic_generation")
    status, body = request(args.base_url, "/metrics", api_key=key)
    assert status == 200 and "civil_code_rag_http_requests_total" in body, (
        status,
        body,
    )
    assert 'civil_code_rag_ask_total{outcome="answered",route="exact"}' in body
    checks.append("metrics")
    print(json.dumps({"status": "pass", "checks": checks}))


if __name__ == "__main__":
    main()
