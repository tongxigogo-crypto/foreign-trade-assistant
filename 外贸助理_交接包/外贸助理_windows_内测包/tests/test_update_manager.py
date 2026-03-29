from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
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
    monkeypatch.setenv("TRADE_ASSISTANT_UPDATE_MANIFEST_URL", "")

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


def test_extract_zip_prefers_root_when_launcher_present(tmp_path: Path) -> None:
    zip_path = tmp_path / "TA_Beta_x_windows.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("InVault.exe", b"dummy")
        zf.writestr("Launch_InVault_Windows.bat", "@echo off\r\n")
        zf.writestr("extension/manifest.json", "{}")

    out_dir = tmp_path / "out"
    extracted = update_manager.extract_zip(zip_path, out_dir)
    assert extracted == out_dir
    assert (extracted / "InVault.exe").exists()
    assert (extracted / "Launch_InVault_Windows.bat").exists()


def test_check_latest_update_uses_manifest_when_configured(monkeypatch) -> None:
    def fake_urlopen(req: Request, timeout: int = 8):  # noqa: ARG001
        assert "release-manifest.json" in req.full_url
        payload = {
            "version": "v0.1.2-build99",
            "published_at": "2026-03-29T00:00:00Z",
            "assets": [
                {
                    "name": "TA_Beta_build99_windows.zip",
                    "url": "./assets/downloads/TA_Beta_build99_windows.zip",
                    "build": "build99",
                }
            ],
        }
        return _FakeResponse(payload)

    monkeypatch.setattr(update_manager, "urlopen", fake_urlopen)
    monkeypatch.setattr(update_manager, "platform_id", lambda: "windows")
    monkeypatch.setenv("TRADE_ASSISTANT_UPDATE_MANIFEST_URL", "https://example.com/api/release-manifest.json")

    info = update_manager.check_latest_update("v0.1.1-build1")
    assert info.latest_version == "v0.1.2-build99"
    assert info.asset_name.endswith("_windows.zip")
    assert info.download_url.startswith("https://example.com/")


def test_update_info_has_update_compares_versions() -> None:
    newer = update_manager.UpdateInfo(
        current_version="v0.1.1-beta1-build14",
        latest_version="v0.1.2-beta1-build1",
        asset_name="TA_Beta_build_x_windows.zip",
        download_url="https://example.com/a.zip",
        body="",
        published_at="",
        source_repo="manifest",
    )
    assert newer.has_update is True

    older_build = update_manager.UpdateInfo(
        current_version="v0.1.1-beta1-build14",
        latest_version="v0.1.1-beta1-build11",
        asset_name="TA_Beta_build_x_windows.zip",
        download_url="https://example.com/a.zip",
        body="",
        published_at="",
        source_repo="manifest",
    )
    assert older_build.has_update is False

    stable_beats_beta = update_manager.UpdateInfo(
        current_version="v0.1.1-beta2-build99",
        latest_version="v0.1.1-build1",
        asset_name="TA_Beta_build_x_windows.zip",
        download_url="https://example.com/a.zip",
        body="",
        published_at="",
        source_repo="manifest",
    )
    assert stable_beats_beta.has_update is True

