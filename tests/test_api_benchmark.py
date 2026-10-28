import json
import urllib.request

import pytest

import api_benchmark


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_api_completion_uses_chat_completions_and_returns_text(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse({"choices": [{"message": {"content": "hello"}}]})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    result = api_benchmark.api_completion(
        "say hello", "https://example.test/v1/", "demo-model", "not-a-real-secret", 32
    )
    assert result == "hello"
    assert captured["url"] == "https://example.test/v1/chat/completions"
    assert captured["body"]["model"] == "demo-model"
    assert captured["body"]["temperature"] == 0
    assert captured["headers"]["Authorization"] == "Bearer not-a-real-secret"


def test_api_completion_rejects_non_http_base_url():
    with pytest.raises(ValueError, match="http"):
        api_benchmark.api_completion("hello", "file:///tmp", "demo", "key")


def test_api_completion_rejects_unexpected_response_shape(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout: FakeResponse({"choices": []}))
    with pytest.raises(ValueError, match="did not contain"):
        api_benchmark.api_completion("hello", "https://example.test/v1", "demo", "key")


def test_api_completion_rejects_api_key_in_url(monkeypatch):
    with pytest.raises(ValueError, match="query parameters"):
        api_benchmark.api_completion("hello", "https://example.test/v1?api_key=secret", "demo", "key")


def test_api_completion_requires_https_for_remote_hosts():
    with pytest.raises(ValueError, match="HTTPS"):
        api_benchmark.api_completion("hello", "http://api.example.test/v1", "demo", "key")
