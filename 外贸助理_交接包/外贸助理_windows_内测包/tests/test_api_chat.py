from __future__ import annotations

from pathlib import Path
import json

from app.api_chat import (
    ApiChatError,
    ApiChatSettings,
    build_local_context,
    classify_http_error,
    default_api_url,
    discover_local_models,
    is_local_provider,
    provider_requires_api_key,
    send_chat_request,
)
from app.capsule_builder import CapsuleBuilder
from app.local_store import LocalKnowledgeStore


def test_default_api_url_contains_supported_providers() -> None:
    assert default_api_url("nvidia").startswith("https://integrate.api.nvidia.com/")
    assert default_api_url("qwen").startswith("https://dashscope.aliyuncs.com/")
    assert default_api_url("doubao").startswith("https://ark.cn-beijing.volces.com/")
    assert default_api_url("google").startswith("https://generativelanguage.googleapis.com/")
    assert default_api_url("local_ollama").startswith("http://127.0.0.1:11434/")
    assert default_api_url("local_openai").startswith("http://127.0.0.1:1234/")
    assert is_local_provider("local_ollama") is True
    assert is_local_provider("local_openai") is True
    assert provider_requires_api_key("local_ollama") is False
    assert provider_requires_api_key("local_openai") is False
    assert provider_requires_api_key("openai") is True


def test_build_local_context_uses_knowledge_base(tmp_path: Path) -> None:
    knowledge_file = tmp_path / "knowledge_base.json"
    store = LocalKnowledgeStore(knowledge_file)
    store.ensure_initialized()
    kb = store.load()
    kb.global_facts.append("Preferred term is FOB Shanghai.")
    store.save(kb)

    builder = CapsuleBuilder(store=store)
    context = build_local_context(
        capsule_builder=builder,
        user_input="Please draft a quick quote for customer A",
        model_name="meta/llama-3.1-70b-instruct",
    )

    assert "[LOCAL_CONTEXT_BEGIN]" not in context.prompt
    assert "Preferred term is FOB Shanghai." in context.prompt
    assert "用户问题" in context.prompt
    assert "Local facts" in context.answer_basis


def test_build_local_context_skips_portfolio_for_greeting_only(tmp_path: Path) -> None:
    knowledge_file = tmp_path / "knowledge_base.json"
    store = LocalKnowledgeStore(knowledge_file)
    store.ensure_initialized()
    kb = store.load()
    kb.doc_facts.extend(
        [
            "[web-llm] PERSONAL DEV PORTFOLIO",
            "[web-llm] 这是我的个人开发网站，用于展示我持续迭代的应用与自动化产品。",
        ]
    )
    store.save(kb)

    builder = CapsuleBuilder(store=store)
    context = build_local_context(
        capsule_builder=builder,
        user_input="你好",
        model_name="meta/llama-3.1-70b-instruct",
    )

    assert "PERSONAL DEV PORTFOLIO" not in context.prompt
    assert "个人开发网站" not in context.prompt


def test_classify_http_error() -> None:
    err401 = classify_http_error(401, "unauthorized")
    err429 = classify_http_error(429, "rate limited")
    err404 = classify_http_error(404, "not found")

    assert isinstance(err401, ApiChatError)
    assert err401.kind == "auth"
    assert err429.kind == "rate_limit"
    assert err404.kind == "not_found"


def test_send_chat_request_passes_history(monkeypatch) -> None:
    captured: list[dict] = []

    class _Resp:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        body = req.data.decode("utf-8")
        captured.append(json.loads(body))
        return _Resp({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("app.api_chat.urlopen", fake_urlopen)

    settings = ApiChatSettings(provider="openai", api_key="k", model="m", api_url="https://example.test/v1/chat/completions")
    reply = send_chat_request(
        settings,
        "current question",
        history=[{"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"}],
    )

    assert reply == "ok"
    messages = captured[0]["messages"]
    assert messages[1] == {"role": "user", "content": "q1"}
    assert messages[2] == {"role": "assistant", "content": "a1"}
    assert messages[-1] == {"role": "user", "content": "current question"}


def test_send_chat_request_web_fallback_when_answer_insufficient(monkeypatch) -> None:
    captured: list[dict] = []

    class _Resp:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    class _HtmlResp:
        def __init__(self, html: str) -> None:
            self._html = html

        def read(self) -> bytes:
            return self._html.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        if req.full_url.startswith("https://duckduckgo.com/"):
            html = """
            <a class="result__a">ACME news</a>
            <a class="result__snippet">latest freight trend</a>
            """
            return _HtmlResp(html)
        body = req.data.decode("utf-8")
        captured.append(json.loads(body))
        if len(captured) == 1:
            return _Resp({"choices": [{"message": {"content": "I don't know based on local data."}}]})
        return _Resp({"choices": [{"message": {"content": "suggestion from web snippets"}}]})

    monkeypatch.setattr("app.api_chat.urlopen", fake_urlopen)

    settings = ApiChatSettings(provider="openai", api_key="k", model="m", api_url="https://example.test/v1/chat/completions")
    reply = send_chat_request(
        settings,
        "please advise",
        allow_web_fallback=True,
        web_search_query="acme freight update",
    )

    assert reply == "suggestion from web snippets"
    assert len(captured) == 2
    assert "Web search snippets" in captured[1]["messages"][-1]["content"]


def test_send_chat_request_includes_preference_instruction(monkeypatch) -> None:
    captured: list[dict] = []

    class _Resp:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        body = req.data.decode("utf-8")
        captured.append(json.loads(body))
        return _Resp({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("app.api_chat.urlopen", fake_urlopen)

    settings = ApiChatSettings(provider="openai", api_key="k", model="m", api_url="https://example.test/v1/chat/completions")
    _ = send_chat_request(settings, "hello", preference_instructions="Preference profile: tone=polite")

    system_content = captured[0]["messages"][0]["content"]
    assert "Preference profile: tone=polite" in system_content


def test_discover_local_models_for_ollama(monkeypatch) -> None:
    class _Resp:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        assert req.full_url.endswith("/api/tags")
        return _Resp({"models": [{"name": "gemma3:4b"}, {"name": "qwen2.5:7b"}]})

    monkeypatch.setattr("app.api_chat.urlopen", fake_urlopen)

    settings = ApiChatSettings(provider="local_ollama", api_key="", model="", api_url="")
    resolved_url, models = discover_local_models(settings)

    assert resolved_url == "http://127.0.0.1:11434/v1/chat/completions"
    assert models == ["gemma3:4b", "qwen2.5:7b"]


def test_discover_local_models_for_openai_compatible(monkeypatch) -> None:
    class _Resp:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        assert req.full_url.endswith("/models")
        return _Resp({"data": [{"id": "gemma-3-12b-it"}, {"id": "qwen2.5-14b-instruct"}]})

    monkeypatch.setattr("app.api_chat.urlopen", fake_urlopen)

    settings = ApiChatSettings(provider="local_openai", api_key="", model="", api_url="")
    resolved_url, models = discover_local_models(settings)

    assert resolved_url == "http://127.0.0.1:1234/v1/chat/completions"
    assert models == ["gemma-3-12b-it", "qwen2.5-14b-instruct"]


def test_send_chat_request_for_local_provider_omits_authorization(monkeypatch) -> None:
    seen_headers: list[dict[str, str]] = []

    class _Resp:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        seen_headers.append(dict(req.header_items()))
        return _Resp({"choices": [{"message": {"content": "local ok"}}]})

    monkeypatch.setattr("app.api_chat.urlopen", fake_urlopen)

    settings = ApiChatSettings(
        provider="local_openai",
        api_key="",
        model="gemma-3-12b-it",
        api_url="http://127.0.0.1:1234/v1/chat/completions",
    )
    reply = send_chat_request(settings, "hello local")

    assert reply == "local ok"
    assert "Authorization" not in seen_headers[0]
