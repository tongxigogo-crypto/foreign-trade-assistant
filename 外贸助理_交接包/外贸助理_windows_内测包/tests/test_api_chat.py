from __future__ import annotations

from pathlib import Path

from app.api_chat import (
    ApiChatError,
    build_local_context,
    classify_http_error,
    default_api_url,
)
from app.capsule_builder import CapsuleBuilder
from app.local_store import LocalKnowledgeStore


def test_default_api_url_contains_supported_providers() -> None:
    assert default_api_url("nvidia").startswith("https://integrate.api.nvidia.com/")
    assert default_api_url("qwen").startswith("https://dashscope.aliyuncs.com/")
    assert default_api_url("doubao").startswith("https://ark.cn-beijing.volces.com/")
    assert default_api_url("google").startswith("https://generativelanguage.googleapis.com/")


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

    assert "[LOCAL_CONTEXT_BEGIN]" in context.prompt
    assert "Preferred term is FOB Shanghai." in context.prompt
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
