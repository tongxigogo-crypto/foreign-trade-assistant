from __future__ import annotations

import json
import os
import platform
import ssl
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

try:
    import certifi
except ImportError:  # pragma: no cover - optional in dev, bundled in release
    certifi = None

UPDATE_REPO = os.getenv("TRADE_ASSISTANT_UPDATE_REPO", "tongxigogo-crypto/foreign-trade-assistant")
DEFAULT_UPDATE_MANIFEST_URL = os.getenv(
    "TRADE_ASSISTANT_UPDATE_MANIFEST_URL",
    "https://tongxigogo-crypto.github.io/foreign-trade-assistant-site/api/release-manifest.json",
)


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


def _read_partner_policy(root_dir: Path) -> dict[str, Any]:
    policy_path = root_dir / "config" / "partner-policy.json"
    if not policy_path.exists():
        return {}
    try:
        data = json.loads(policy_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _manifest_url(root_dir: Path | None = None) -> str:
    # Env can disable manifest by setting empty string.
    env_url = str(os.getenv("TRADE_ASSISTANT_UPDATE_MANIFEST_URL", DEFAULT_UPDATE_MANIFEST_URL) or "").strip()
    if env_url:
        return env_url
    if root_dir is None:
        return ""
    policy = _read_partner_policy(root_dir)
    url = str(policy.get("update_manifest_url", "") or "").strip()
    return url


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
        current = self.current_version.strip()
        latest = self.latest_version.strip()
        if not current or not latest:
            return False
        try:
            return _version_key(latest) > _version_key(current)
        except Exception:
            return latest != current


def _version_key(version: str) -> tuple[int, int, int, int, int, int, int]:
    """
    Convert tags like:
      - v0.1.1-beta1-build14
      - v0.1.0-build12-winfix15
      - v0.1.2
    into an ordering key. Missing parts default to 0.

    Key order:
      (major, minor, patch, prerelease_rank, beta_num, build_num, winfix_num)

    prerelease_rank: 0 for beta, 1 for stable (stable > beta for same base version).
    """
    raw = str(version or "").strip()
    if raw.startswith("v") or raw.startswith("V"):
        raw = raw[1:]
    parts = [p for p in raw.split("-") if p]
    if not parts:
        raise ValueError("empty version")

    base = parts[0]
    base_nums = base.split(".")
    if len(base_nums) < 3:
        base_nums = (base_nums + ["0", "0", "0"])[:3]
    major, minor, patch = (int(x) for x in base_nums[:3])

    beta_num = 0
    build_num = 0
    winfix_num = 0
    prerelease_rank = 1

    for token in parts[1:]:
        low = token.lower()
        if low.startswith("beta"):
            prerelease_rank = 0
            num = low.removeprefix("beta")
            beta_num = int(num) if num.isdigit() else 0
            continue
        if low.startswith("build"):
            num = low.removeprefix("build")
            build_num = int(num) if num.isdigit() else 0
            continue
        if low.startswith("winfix"):
            num = low.removeprefix("winfix")
            winfix_num = int(num) if num.isdigit() else 0
            continue

    return (major, minor, patch, prerelease_rank, beta_num, build_num, winfix_num)


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
    with _urlopen_with_ssl(req, timeout_sec=timeout_sec) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _fetch_text_url(url: str, *, timeout_sec: int = 8) -> str:
    req = Request(
        url=url,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "TradeAssistant-Updater/1.0",
        },
    )
    with _urlopen_with_ssl(req, timeout_sec=timeout_sec) as resp:  # noqa: S310
        raw = resp.read()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def _pick_manifest_asset(payload: dict[str, Any], target_platform: str) -> tuple[str, str]:
    assets = payload.get("assets", [])
    if not isinstance(assets, list):
        raise RuntimeError("Invalid manifest payload: assets is not a list.")
    suffix = "_windows.zip" if target_platform == "windows" else "_mac.zip"
    platform_tokens = ("windows", "win") if target_platform == "windows" else ("mac", "darwin", "osx")
    for item in assets:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        url = str(item.get("url", ""))
        if name.endswith(suffix) and url:
            return name, url
    for item in assets:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        low = name.lower()
        url = str(item.get("url", ""))
        if not url or not low.endswith(".zip"):
            continue
        if any(token in low for token in platform_tokens):
            return name, url
    raise RuntimeError(f"No manifest asset found for platform: {target_platform}.")


def _check_latest_update_from_manifest(current_version: str, manifest_url: str, *, timeout_sec: int = 8) -> UpdateInfo:
    text = _fetch_text_url(manifest_url, timeout_sec=timeout_sec)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise RuntimeError("Invalid manifest payload: expected object.")

    latest = str(payload.get("version", "")).strip()
    if not latest:
        raise RuntimeError("Invalid manifest payload: missing version.")

    platform_name = platform_id()
    asset_name, url = _pick_manifest_asset(payload, platform_name)
    download_url = urljoin(manifest_url, url)
    return UpdateInfo(
        current_version=current_version,
        latest_version=latest,
        asset_name=asset_name,
        download_url=download_url,
        body=str(payload.get("body", "")),
        published_at=str(payload.get("published_at", "")),
        source_repo=manifest_url,
    )


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
    manifest_url = _manifest_url()
    if manifest_url:
        try:
            return _check_latest_update_from_manifest(current_version, manifest_url, timeout_sec=timeout_sec)
        except Exception:
            # Fallback to GitHub API release checking for legacy channels.
            pass

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
    with _urlopen_with_ssl(req, timeout_sec=timeout_sec) as resp:  # noqa: S310
        data = resp.read()
    zip_path.write_bytes(data)
    return zip_path


def _build_ssl_context() -> ssl.SSLContext:
    """
    Use certifi bundle when available to avoid TLS verification failures in frozen mac app runtimes.
    Falls back to system default cert store.
    """
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def _urlopen_with_ssl(req: Request, *, timeout_sec: int):
    ctx = _build_ssl_context()
    try:
        return urlopen(req, timeout=timeout_sec, context=ctx)  # noqa: S310
    except TypeError:
        # Keep compatibility with mocked urlopen signatures in tests.
        return urlopen(req, timeout=timeout_sec)  # noqa: S310


def extract_zip(zip_path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target_dir)

    # Many Windows release zips contain files at the archive root plus a single folder (e.g. "extension/").
    # In that case, returning the only directory would be wrong; prefer the directory that contains launchers.
    if find_launcher(target_dir) is not None or (target_dir / "InVault.exe").exists():
        return target_dir

    children = [p for p in target_dir.iterdir() if p.is_dir()]
    if len(children) == 1:
        candidate = children[0]
        if find_launcher(candidate) is not None or (candidate / "InVault.exe").exists():
            return candidate
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
    root_dir: Path | None = None,
) -> tuple[UpdateInfo, Path | None, Path]:
    # Allow per-package override through partner-policy.json.
    if root_dir is not None:
        manifest_url = _manifest_url(root_dir)
        if manifest_url:
            try:
                info = _check_latest_update_from_manifest(current_version, manifest_url)
            except Exception:
                info = check_latest_update(current_version)
        else:
            info = check_latest_update(current_version)
    else:
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


def is_windows() -> bool:
    return os.name == "nt" or platform.system().lower().startswith("win")


def resolve_install_dir(fallback_root: Path) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return fallback_root.resolve()


def resolve_update_source_root(prepared_dir: Path) -> Path:
    # Most release zips extract to a directory containing "InVault.exe" at its root.
    if (prepared_dir / "InVault.exe").exists():
        return prepared_dir
    if (prepared_dir / "dist" / "InVault.exe").exists():
        return prepared_dir / "dist"
    for child in prepared_dir.iterdir():
        if not child.is_dir():
            continue
        if (child / "InVault.exe").exists():
            return child
        if (child / "dist" / "InVault.exe").exists():
            return child / "dist"
    return prepared_dir


def schedule_windows_inplace_update(
    *,
    update: UpdateInfo,
    prepared_dir: Path,
    install_dir: Path,
    current_pid: int,
    updates_root: Path,
) -> Path:
    """
    Create and spawn a PowerShell updater that waits for the current process to exit,
    then replaces InVault.exe + extension in-place and restarts the app.

    Returns the updater script path.
    """
    if not is_windows():
        raise RuntimeError("In-place updater is only supported on Windows.")

    # Safety: do not attempt in-place replacement unless we are in a packaged install folder.
    if not (install_dir / "InVault.exe").exists():
        raise RuntimeError(f"Install folder does not contain InVault.exe: {install_dir}")

    updates_root.mkdir(parents=True, exist_ok=True)
    safe_tag = update.latest_version.replace("/", "_").replace("\\", "_").replace(":", "_")
    backup_dir = updates_root / f"backup_{safe_tag}"
    source_root = resolve_update_source_root(prepared_dir)
    exe_name = "InVault.exe"
    script_path = updates_root / f"apply_update_{safe_tag}.ps1"

    # Keep the script ASCII-friendly to reduce encoding issues on systems without UTF-8 codepage.
    script = f"""param(
  [string]$InstallDir,
  [string]$SourceDir,
  [int]$Pid,
  [string]$BackupDir
)

$ErrorActionPreference = "Stop"

function Show-Message([string]$title, [string]$message) {{
  try {{
    Add-Type -AssemblyName PresentationFramework | Out-Null
    [System.Windows.MessageBox]::Show($message, $title) | Out-Null
  }} catch {{
    Write-Host "[$title] $message"
  }}
}}

function Copy-IfExists([string]$src, [string]$dst) {{
  if (Test-Path -LiteralPath $src) {{
    Copy-Item -LiteralPath $src -Destination $dst -Force
  }}
}}

function Copy-DirIfExists([string]$src, [string]$dst) {{
  if (Test-Path -LiteralPath $src) {{
    if (Test-Path -LiteralPath $dst) {{
      Remove-Item -LiteralPath $dst -Recurse -Force
    }}
    Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
  }}
}}

try {{
  if ($Pid -gt 0) {{
    try {{
      Wait-Process -Id $Pid -Timeout 90 | Out-Null
    }} catch {{
      # Ignore timeouts; the following copy will fail if still locked.
    }}
  }}

  $install = (Resolve-Path -LiteralPath $InstallDir).Path
  $source = (Resolve-Path -LiteralPath $SourceDir).Path

  New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

  # Backup current files (best-effort).
  Copy-IfExists (Join-Path $install "{exe_name}") (Join-Path $BackupDir "{exe_name}")
  Copy-IfExists (Join-Path $install "Launch_InVault_Windows.bat") (Join-Path $BackupDir "Launch_InVault_Windows.bat")
  Copy-IfExists (Join-Path $install "USER_GUIDE.txt") (Join-Path $BackupDir "USER_GUIDE.txt")
  if (Test-Path -LiteralPath (Join-Path $install "extension")) {{
    Copy-Item -LiteralPath (Join-Path $install "extension") -Destination (Join-Path $BackupDir "extension") -Recurse -Force
  }}

  # Apply update.
  Copy-IfExists (Join-Path $source "{exe_name}") (Join-Path $install "{exe_name}")
  Copy-IfExists (Join-Path $source "Launch_InVault_Windows.bat") (Join-Path $install "Launch_InVault_Windows.bat")
  Copy-IfExists (Join-Path $source "USER_GUIDE.txt") (Join-Path $install "USER_GUIDE.txt")
  Copy-DirIfExists (Join-Path $source "extension") (Join-Path $install "extension")

  Start-Process -FilePath (Join-Path $install "{exe_name}") | Out-Null
}} catch {{
  # Rollback best-effort.
  try {{
    Copy-IfExists (Join-Path $BackupDir "{exe_name}") (Join-Path $InstallDir "{exe_name}")
    Copy-IfExists (Join-Path $BackupDir "Launch_InVault_Windows.bat") (Join-Path $InstallDir "Launch_InVault_Windows.bat")
    Copy-IfExists (Join-Path $BackupDir "USER_GUIDE.txt") (Join-Path $InstallDir "USER_GUIDE.txt")
    Copy-DirIfExists (Join-Path $BackupDir "extension") (Join-Path $InstallDir "extension")
  }} catch {{}}
  Show-Message "Update failed" ("Update failed. Please re-download full package.\\n\\n" + $_.Exception.Message)
  exit 1
}}
"""

    script_path.write_text(script, encoding="utf-8")

    # Spawn updater hidden, then caller should exit quickly.
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-WindowStyle",
        "Hidden",
        "-File",
        str(script_path),
        "-InstallDir",
        str(install_dir),
        "-SourceDir",
        str(source_root),
        "-Pid",
        str(int(current_pid)),
        "-BackupDir",
        str(backup_dir),
    ]
    kwargs: dict[str, object] = {"cwd": str(install_dir)}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    subprocess.Popen(cmd, **kwargs)  # noqa: S603,S607 - local PowerShell invocation
    return script_path

