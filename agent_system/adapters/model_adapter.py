from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_PROFILES: dict[str, dict[str, Any]] = {
    "openai": {"api_url": "https://api.openai.com/v1/chat/completions", "model": "gpt-4o-mini", "timeout_sec": 30},
    "deepseek": {"api_url": "https://api.deepseek.com/chat/completions", "model": "deepseek-chat", "timeout_sec": 30},
    "qwen": {
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-plus",
        "timeout_sec": 30,
    },
    "doubao": {"api_url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions", "model": "doubao-1-5-pro-32k-250115", "timeout_sec": 30},
    "google": {
        "api_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.0-flash",
        "timeout_sec": 30,
    },
    "custom": {"api_url": "", "model": "", "timeout_sec": 30},
}


def get_default_provider_profile(provider: str) -> dict[str, Any]:
    key = str(provider or "custom").strip().lower()
    return dict(_PROFILES.get(key, _PROFILES["custom"]))


@dataclass
class ModelAdapterConfig:
    provider: str
    model: str
    api_url: str
    api_key: str
    timeout_sec: int = 30


class ModelAdapter:
    def __init__(self, config: ModelAdapterConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = {"model": self.config.model.strip(), "messages": messages}
        req = Request(
            url=self.config.api_url.strip(),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key.strip()}",
            },
        )
        try:
            with urlopen(req, timeout=max(5, int(self.config.timeout_sec))) as resp:  # noqa: S310
                raw = resp.read().decode("utf-8", errors="ignore")
        except HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="ignore")
            except OSError:
                body = str(exc)
            raise RuntimeError(f"HTTP {int(getattr(exc, 'code', 0) or 0)}: {body}") from exc
        except (URLError, OSError, TimeoutError) as exc:
            raise RuntimeError(f"network error: {exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("invalid json response") from exc

        choices = data.get("choices", [])
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("no choices in response")
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message", {}) if isinstance(first.get("message", {}), dict) else {}
        content = str(message.get("content", "")).strip()
        if not content:
            raise RuntimeError("empty response content")
        return content

