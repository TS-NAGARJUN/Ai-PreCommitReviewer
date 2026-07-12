import asyncio
import json

import pytest

from app.ai_models import AIModelError, GroqClient
import app.ai_models as ai_models


class DummyResponse:
    def __init__(self, payload=None, status_code=200, text=""):
        self._payload = payload
        self.status_code = status_code
        self.text = text or json.dumps(payload or {})

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ai_models.httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=ai_models.httpx.Request("POST", "https://example.test"),
                response=ai_models.httpx.Response(self.status_code, request=ai_models.httpx.Request("POST", "https://example.test"), text=self.text),
            )


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.last_request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None):
        self.last_request = {"url": url, "headers": headers, "json": json}
        return DummyResponse({"choices": [{"message": {"content": "groq-ok"}}]})


class DummyAsyncClientUnauthorized(DummyAsyncClient):
    async def post(self, url, headers=None, json=None):
        self.last_request = {"url": url, "headers": headers, "json": json}
        return DummyResponse({"error": {"message": "invalid api key"}}, status_code=401, text='{"error": {"message": "invalid api key"}}')


class DummyAsyncClientMalformed(DummyAsyncClient):
    async def post(self, url, headers=None, json=None):
        self.last_request = {"url": url, "headers": headers, "json": json}
        return DummyResponse({"choices": []})


def test_groq_client_uses_openai_chat_completions_payload(monkeypatch):
    client = DummyAsyncClient()

    monkeypatch.setattr(ai_models.httpx, "AsyncClient", lambda *args, **kwargs: client)

    async def run_test():
        groq = GroqClient("secret", model_name="llama-3.3-70b-versatile")
        return await groq.review("hello")

    result = asyncio.run(run_test())

    assert result == "groq-ok"
    assert client.last_request["url"].endswith("/openai/v1/chat/completions")
    assert client.last_request["json"]["model"] == "llama-3.3-70b-versatile"
    assert client.last_request["json"]["messages"] == [{"role": "user", "content": "hello"}]
    assert client.last_request["headers"]["Authorization"] == "Bearer secret"


def test_groq_client_raises_clear_error_for_missing_api_key():
    groq = GroqClient("")

    with pytest.raises(AIModelError, match="Groq API key is missing"):
        asyncio.run(groq.review("hello"))


def test_groq_client_raises_clear_error_for_unauthorized(monkeypatch):
    client = DummyAsyncClientUnauthorized()

    monkeypatch.setattr(ai_models.httpx, "AsyncClient", lambda *args, **kwargs: client)

    groq = GroqClient("invalid")

    with pytest.raises(AIModelError, match="401 Unauthorized"):
        asyncio.run(groq.review("hello"))


def test_groq_client_raises_clear_error_for_malformed_response(monkeypatch):
    client = DummyAsyncClientMalformed()

    monkeypatch.setattr(ai_models.httpx, "AsyncClient", lambda *args, **kwargs: client)

    groq = GroqClient("secret")

    with pytest.raises(AIModelError, match="malformed"):
        asyncio.run(groq.review("hello"))
