from __future__ import annotations

import io
import json
from urllib.error import HTTPError
from urllib.request import Request

from app import update_manager


class _FakeResponse:
    def __init__(self, payload: object, status: int = 200) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_pick_asset_accepts_fallback_platform_tokens() -> None:
    payload = {
        "assets": [
            {"name": "InVault_beta_win_x64.zip", "browser_download_url": "https://example.com/win.zip"},
            {"name": "InVault_beta_mac_arm64.zip", "browser_download_url": "https://example.com/mac.zip"},
        ]
    }
    win_name, win_url = update_manager._pick_asset(payload, "windows")
    assert win_name == "InVault_beta_win_x64.zip"
    assert win_url.endswith("win.zip")
    mac_name, mac_url = update_manager._pick_asset(payload, "mac")
    assert mac_name == "InVault_beta_mac_arm64.zip"
    assert mac_url.endswith("mac.zip")


def test_check_latest_update_fallbacks_to_releases_list_when_latest_404(monkeypatch) -> None:
    calls: list[str] = []

    def fake_urlopen(req: Request, timeout: int = 8):  # noqa: ARG001
        url = req.full_url
        calls.append(url)
        if url.endswith("/releases/latest"):
            raise HTTPError(url=url, code=404, msg="Not Found", hdrs=None, fp=io.BytesIO(b'{"message":"Not Found"}'))
        if "/releases?per_page=20" in url:
            payload = [
                {
                    "tag_name": "v0.1.2",
                    "body": "beta",
                    "published_at": "2026-03-26T10:00:00Z",
                    "assets": [
                        {
                            "name": "TA_Beta_v0.1.2_windows.zip",
                            "browser_download_url": "https://example.com/TA_Beta_v0.1.2_windows.zip",
                        }
                    ],
                }
            ]
            return _FakeResponse(payload)
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(update_manager, "urlopen", fake_urlopen)
    monkeypatch.setattr(update_manager, "_candidate_repos", lambda: ["tongxigogo-crypto/foreign-trade-assistant"])
    monkeypatch.setattr(update_manager, "platform_id", lambda: "windows")

    info = update_manager.check_latest_update("v0.1.1")
    assert info.latest_version == "v0.1.2"
    assert info.source_repo == "tongxigogo-crypto/foreign-trade-assistant"
    assert info.asset_name.endswith("_windows.zip")
    assert any(url.endswith("/releases/latest") for url in calls)
    assert any("/releases?per_page=20" in url for url in calls)


def test_is_http_not_found_error_true_for_404() -> None:
    err = HTTPError(
        url="https://api.github.com/repos/a/b/releases/latest",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=io.BytesIO(b"{}"),
    )
    assert update_manager.is_http_not_found_error(err) is True

