from __future__ import annotations

import json
import os
import platform
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

UPDATE_REPO = os.getenv("TRADE_ASSISTANT_UPDATE_REPO", "tongxigogo-crypto/foreign-trade-assistant")


def _normalize_repo_name(repo: str) -> str:
    return str(repo or "").strip().strip("/")


def _candidate_repos() -> list[str]:
    repos: list[str] = []
    primary = _normalize_repo_name(os.getenv("TRADE_ASSISTANT_UPDATE_REPO", UPDATE_REPO))
    if primary:
        repos.append(primary)
    fallback_env = str(os.getenv("TRADE_ASSISTANT_UPDATE_REPO_FALLBACKS", "")).strip()
    if fallback_env:
        for item in fallback_env.split(","):
            norm = _normalize_repo_name(item)
            if norm and norm not in repos:
                repos.append(norm)
    # Safe default fallback to preserve old update behavior if users changed env by mistake.
    if UPDATE_REPO not in repos:
        repos.append(UPDATE_REPO)
    return repos


def _releases_latest_url(repo: str) -> str:
    return f"https://api.github.com/repos/{repo}/releases/latest"


def _releases_list_url(repo: str) -> str:
    return f"https://api.github.com/repos/{repo}/releases?per_page=20"


@dataclass
class UpdateInfo:
    current_version: str
    latest_version: str
    asset_name: str
    download_url: str
    body: str
    published_at: str
    source_repo: str

    @property
    def has_update(self) -> bool:
        return self.latest_version.strip() != self.current_version.strip()


def platform_id() -> str:
    system = platform.system().lower()
    if "windows" in system:
        return "windows"
    if "darwin" in system or "mac" in system:
        return "mac"
    raise RuntimeError(f"Unsupported platform for updater: {system}")


def _fetch_json_url(url: str, *, timeout_sec: int = 8) -> Any:
    req = Request(
        url=url,
        method="GET",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "TradeAssistant-Updater/1.0",
        },
    )
    with urlopen(req, timeout=timeout_sec) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _fetch_latest_release_payload(repo: str, timeout_sec: int = 8) -> dict[str, Any]:
    latest_url = _releases_latest_url(repo)
    try:
        payload = _fetch_json_url(latest_url, timeout_sec=timeout_sec)
        if isinstance(payload, dict):
            return payload
    except HTTPError as exc:
        if int(getattr(exc, "code", 0) or 0) != 404:
            raise
    # Fallback: some repos/tags do not expose `/releases/latest` yet.
    releases_payload = _fetch_json_url(_releases_list_url(repo), timeout_sec=timeout_sec)
    if not isinstance(releases_payload, list):
        raise RuntimeError("Invalid release payload: releases is not a list.")
    for item in releases_payload:
        if not isinstance(item, dict):
            continue
        if str(item.get("tag_name", "")).strip():
            return item
    raise RuntimeError("No usable release found.")


def _pick_asset(payload: dict[str, Any], target_platform: str) -> tuple[str, str]:
    assets = payload.get("assets", [])
    if not isinstance(assets, list):
        raise RuntimeError("Invalid release payload: assets is not a list.")
    suffix = "_windows.zip" if target_platform == "windows" else "_mac.zip"
    platform_tokens = ("windows", "win") if target_platform == "windows" else ("mac", "darwin", "osx")
    for item in assets:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        url = str(item.get("browser_download_url", ""))
        if name.endswith(suffix) and url:
            return name, url
    # Fallback: accept any zip with platform token in filename.
    for item in assets:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        low = name.lower()
        url = str(item.get("browser_download_url", ""))
        if not url or not low.endswith(".zip"):
            continue
        if any(token in low for token in platform_tokens):
            return name, url
    raise RuntimeError(f"No release asset found for platform: {target_platform}.")


def check_latest_update(current_version: str, *, timeout_sec: int = 8) -> UpdateInfo:
    platform_name = platform_id()
    last_err: Exception | None = None
    for repo in _candidate_repos():
        try:
            payload = _fetch_latest_release_payload(repo, timeout_sec=timeout_sec)
            latest = str(payload.get("tag_name", "")).strip()
            if not latest:
                raise RuntimeError(f"Latest release has no tag_name (repo={repo}).")
            asset_name, download_url = _pick_asset(payload, platform_name)
            return UpdateInfo(
                current_version=current_version,
                latest_version=latest,
                asset_name=asset_name,
                download_url=download_url,
                body=str(payload.get("body", "")),
                published_at=str(payload.get("published_at", "")),
                source_repo=repo,
            )
        except Exception as exc:  # pragma: no cover - only final raise is asserted in tests
            last_err = exc
            continue
    if last_err is not None:
        raise last_err
    raise RuntimeError("No update source repo configured.")


def download_zip(update: UpdateInfo, download_dir: Path, *, timeout_sec: int = 120) -> Path:
    download_dir.mkdir(parents=True, exist_ok=True)
    zip_path = download_dir / update.asset_name
    req = Request(
        url=update.download_url,
        method="GET",
        headers={
            "Accept": "application/octet-stream",
            "User-Agent": "TradeAssistant-Updater/1.0",
        },
    )
    with urlopen(req, timeout=timeout_sec) as resp:  # noqa: S310
        data = resp.read()
    zip_path.write_bytes(data)
    return zip_path


def extract_zip(zip_path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target_dir)
    children = [p for p in target_dir.iterdir() if p.is_dir()]
    if len(children) == 1:
        return children[0]
    return target_dir


def find_launcher(extracted_dir: Path) -> Path | None:
    candidates = (
        "启动外贸助理桌面版_windows.bat",
        "Launch_InVault_Windows.bat",
        "启动外贸助理桌面版_mac.command",
        "Launch_InVault_Mac.command",
    )
    for name in candidates:
        p = extracted_dir / name
        if p.exists():
            return p
    return None


def open_path(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
        return
    if platform.system().lower() == "darwin":
        subprocess.Popen(["open", str(path)])
        return
    raise RuntimeError("Open path is only implemented for Windows/macOS.")


def check_and_prepare_update(
    *,
    current_version: str,
    updates_root: Path,
) -> tuple[UpdateInfo, Path | None, Path]:
    info = check_latest_update(current_version)
    if not info.has_update:
        return info, None, updates_root

    tag_folder = info.latest_version.replace("/", "_").replace("\\", "_")
    package_root = updates_root / f"TradeAssistant_{tag_folder}"
    if package_root.exists():
        launcher = find_launcher(package_root)
        return info, launcher, package_root

    zip_path = download_zip(info, updates_root)
    if package_root.exists():
        for child in package_root.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)
    extracted = extract_zip(zip_path, package_root)
    launcher = find_launcher(extracted)
    return info, launcher, extracted


def is_network_error(exc: Exception) -> bool:
    return isinstance(exc, URLError)


def is_http_not_found_error(exc: Exception) -> bool:
    return isinstance(exc, HTTPError) and int(getattr(exc, "code", 0) or 0) == 404

