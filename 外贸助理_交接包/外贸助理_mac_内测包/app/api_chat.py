from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .capsule_builder import CapsuleBuilder
from .contracts import CapsuleRequest


PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "nvidia": {
        "api_url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "meta/llama-3.1-70b-instruct",
    },
    "openai": {
        "api_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
    },
    "openrouter": {
        "api_url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openai/gpt-4o-mini",
    },
    "deepseek": {
        "api_url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
    },
    "qwen": {
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-plus",
    },
    "doubao": {
        "api_url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        "model": "doubao-1-5-pro-32k-250115",
    },
    "google": {
        "api_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.0-flash",
    },
    "custom": {"api_url": "", "model": ""},
}


@dataclass
class ApiChatSettings:
    provider: str
    api_key: str
    model: str
    api_url: str
    timeout_sec: int = 30


@dataclass
class LocalContext:
    prompt: str
    answer_basis: str


class ApiChatError(RuntimeError):
    def __init__(self, kind: str, message: str, *, status_code: int = 0) -> None:
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code


def default_api_url(provider: str) -> str:
    return PROVIDER_DEFAULTS.get(provider.strip().lower(), PROVIDER_DEFAULTS["custom"]).get("api_url", "")


def default_model(provider: str) -> str:
    return PROVIDER_DEFAULTS.get(provider.strip().lower(), PROVIDER_DEFAULTS["custom"]).get("model", "")


def build_local_context(
    *,
    capsule_builder: CapsuleBuilder,
    user_input: str,
    model_name: str,
    template_lang: str = "zh",
) -> LocalContext:
    capsule = capsule_builder.build(
        CapsuleRequest(
            user_input=user_input.strip(),
            model_name=model_name.strip(),
            template_lang=template_lang,
            template_mode="standard",
        )
    )
    lines: list[str] = ["Local facts selected for this reply:"]
    for item in capsule.facts[:8]:
        lines.append(f"- {item}")
    for item in capsule.constraints[:6]:
        lines.append(f"- {item}")
    if len(lines) == 1:
        lines.append("- No local fact was matched.")
    return LocalContext(prompt=capsule.injected_prompt, answer_basis="\n".join(lines))


def classify_http_error(status_code: int, body: str) -> ApiChatError:
    body_text = body.strip() or f"HTTP {status_code}"
    if status_code in {401, 403}:
        return ApiChatError("auth", body_text, status_code=status_code)
    if status_code == 429:
        return ApiChatError("rate_limit", body_text, status_code=status_code)
    if status_code == 404:
        return ApiChatError("not_found", body_text, status_code=status_code)
    if 400 <= status_code < 500:
        return ApiChatError("bad_request", body_text, status_code=status_code)
    if 500 <= status_code < 600:
        return ApiChatError("server", body_text, status_code=status_code)
    return ApiChatError("unknown", body_text, status_code=status_code)


def send_chat_request(settings: ApiChatSettings, prompt: str) -> str:
    payload = {
        "model": settings.model.strip(),
        "messages": [{"role": "user", "content": prompt}],
    }
    req = Request(
        url=settings.api_url.strip(),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_key.strip()}",
        },
    )
    try:
        with urlopen(req, timeout=max(5, int(settings.timeout_sec))) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="ignore")
    except HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="ignore")
        except OSError:
            body = str(exc)
        raise classify_http_error(int(getattr(exc, "code", 0) or 0), body) from exc
    except (URLError, OSError, TimeoutError) as exc:
        raise ApiChatError("network", str(exc)) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ApiChatError("bad_response", "Invalid JSON response.") from exc

    choices = data.get("choices", [])
    if not isinstance(choices, list) or not choices:
        raise ApiChatError("bad_response", "No choices returned by API.")
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message", {}) if isinstance(first.get("message", {}), dict) else {}
    content = str(message.get("content", "")).strip()
    if not content:
        raise ApiChatError("bad_response", "Empty response content.")
    return content
