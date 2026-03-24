from __future__ import annotations

import json
import os
import platform
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .security_utils import encrypt_sensitive_fields

LATEST_SCHEMA_VERSION = 3


def resolve_data_dir(
    *,
    root_dir: Path,
    declared_data_dir: str,
    data_dir_mode: str | None,
    app_name: str = "TradeAssistant",
) -> tuple[Path, Path | None]:
    env_override = os.getenv("TRADE_ASSISTANT_DATA_DIR", "").strip()
    if env_override:
        target = Path(env_override).expanduser()
        if not target.is_absolute():
            target = (root_dir / target).resolve()
        legacy = _legacy_workspace_data_dir(root_dir=root_dir, declared_data_dir=declared_data_dir, target=target)
        return target, legacy

    declared = Path(str(declared_data_dir or "local_data").strip() or "local_data")
    mode = (data_dir_mode or "").strip().lower()
    if declared.is_absolute():
        target = declared
        legacy = _legacy_workspace_data_dir(root_dir=root_dir, declared_data_dir=declared_data_dir, target=target)
        return target, legacy

    if mode in {"workspace", "relative_to_root"}:
        target = (root_dir / declared).resolve()
        return target, None

    base_root = _system_data_root(app_name=app_name)
    target = (base_root / declared).resolve()
    legacy = _legacy_workspace_data_dir(root_dir=root_dir, declared_data_dir=declared_data_dir, target=target)
    return target, legacy


def ensure_runtime_data_layout(
    *,
    target_data_dir: Path,
    legacy_data_dir: Path | None,
    knowledge_file_name: str,
    state_board_file_name: str,
    user_settings_file_name: str,
) -> dict[str, Any]:
    core_files = [knowledge_file_name, state_board_file_name, user_settings_file_name]
    migration = _migrate_legacy_data_dir_if_needed(
        legacy_data_dir=legacy_data_dir,
        target_data_dir=target_data_dir,
        core_files=core_files,
    )
    target_data_dir.mkdir(parents=True, exist_ok=True)
    _ensure_core_json_file(target_data_dir / knowledge_file_name, default_payload={})
    _ensure_core_json_file(target_data_dir / state_board_file_name, default_payload={})
    _ensure_core_json_file(target_data_dir / user_settings_file_name, default_payload={"schema_version": LATEST_SCHEMA_VERSION})

    schema = run_json_schema_migrations(
        data_dir=target_data_dir,
        knowledge_file_name=knowledge_file_name,
        state_board_file_name=state_board_file_name,
        user_settings_file_name=user_settings_file_name,
    )
    return {"migration": migration, "schema": schema}


def run_json_schema_migrations(
    *,
    data_dir: Path,
    knowledge_file_name: str,
    state_board_file_name: str,
    user_settings_file_name: str,
) -> dict[str, Any]:
    knowledge_path = data_dir / knowledge_file_name
    _state_path = data_dir / state_board_file_name
    settings_path = data_dir / user_settings_file_name

    settings_payload = _read_json_file(settings_path)
    if not isinstance(settings_payload, dict):
        settings_payload = {}
    try:
        version = int(settings_payload.get("schema_version", 1))
    except (TypeError, ValueError):
        version = 1

    updated = False
    knowledge_updated = False
    settings_updated = False
    knowledge_payload: dict[str, Any] | None = None

    if version < 2:
        kb_payload_raw = _read_json_file(knowledge_path)
        if not isinstance(kb_payload_raw, dict):
            kb_payload_raw = {}
        pref = kb_payload_raw.get("preference", {})
        if not isinstance(pref, dict):
            pref = {}
        if not isinstance(pref.get("adaptive_profile"), dict):
            pref["adaptive_profile"] = {}
            knowledge_updated = True
        if not isinstance(pref.get("pricing_rules"), list):
            pref["pricing_rules"] = []
            knowledge_updated = True
        if not isinstance(pref.get("must_include"), list):
            pref["must_include"] = []
            knowledge_updated = True
        if not isinstance(pref.get("forbidden_terms"), list):
            pref["forbidden_terms"] = []
            knowledge_updated = True
        kb_payload_raw["preference"] = pref
        knowledge_payload = kb_payload_raw
        version = 2

    if version < 3:
        if knowledge_payload is None:
            kb_payload_raw = _read_json_file(knowledge_path)
            if not isinstance(kb_payload_raw, dict):
                kb_payload_raw = {}
            knowledge_payload = kb_payload_raw

        encrypted_kb, kb_encrypted = encrypt_sensitive_fields(knowledge_payload, namespace="knowledge_base")
        if kb_encrypted:
            knowledge_payload = encrypted_kb
            knowledge_updated = True

        encrypted_settings, settings_encrypted = encrypt_sensitive_fields(settings_payload, namespace="user_settings")
        if settings_encrypted:
            settings_payload = encrypted_settings
            settings_updated = True
        version = 3

    if knowledge_payload is not None and knowledge_updated:
        _backup_file(knowledge_path)
        _write_json_file(knowledge_path, knowledge_payload)
        updated = True

    if int(settings_payload.get("schema_version", 0) or 0) != version:
        settings_payload["schema_version"] = version
        settings_updated = True

    if settings_updated:
        _backup_file(settings_path)
        _write_json_file(settings_path, settings_payload)
        updated = True

    return {"status": "ok", "schema_version": version, "updated": updated}


def _migrate_legacy_data_dir_if_needed(
    *,
    legacy_data_dir: Path | None,
    target_data_dir: Path,
    core_files: list[str],
) -> dict[str, Any]:
    if legacy_data_dir is None:
        return {"status": "skipped", "reason": "no_legacy_dir"}
    legacy = legacy_data_dir.resolve()
    target = target_data_dir.resolve()
    if legacy == target:
        return {"status": "skipped", "reason": "same_path"}
    if target.exists():
        return {"status": "skipped", "reason": "target_exists"}
    if not legacy.exists() or not legacy.is_dir():
        return {"status": "skipped", "reason": "legacy_missing"}

    target.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    temp_target = _unique_path(target.parent / f"{target.name}.tmp.{ts}")
    shutil.copytree(legacy, temp_target)
    try:
        _verify_temp_copy(temp_target=temp_target, core_files=core_files)
        temp_target.replace(target)
    except Exception:
        if temp_target.exists():
            shutil.rmtree(temp_target, ignore_errors=True)
        raise

    legacy_backup = _unique_path(legacy.parent / f"{legacy.name}_migrated_backup_{ts}")
    legacy.replace(legacy_backup)
    legacy.mkdir(parents=True, exist_ok=True)
    readme = legacy / "MIGRATED_README.txt"
    readme.write_text(
        "\n".join(
            [
                "Trade Assistant data has been migrated.",
                f"New data directory: {target}",
                f"Backup of old directory: {legacy_backup}",
                "Do not edit files in the backup while the app is running.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "status": "migrated",
        "legacy_dir": str(legacy),
        "legacy_backup": str(legacy_backup),
        "target_dir": str(target),
    }


def _legacy_workspace_data_dir(*, root_dir: Path, declared_data_dir: str, target: Path) -> Path | None:
    declared = Path(str(declared_data_dir or "local_data").strip() or "local_data")
    if declared.is_absolute():
        return None
    legacy = (root_dir / declared).resolve()
    if legacy == target.resolve():
        return None
    return legacy


def _system_data_root(*, app_name: str) -> Path:
    env_root = os.getenv("TRADE_ASSISTANT_USER_DATA_ROOT", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve() / app_name
    system_name = platform.system().lower()
    if system_name == "windows":
        appdata = os.getenv("APPDATA", "").strip()
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base / app_name
    if system_name == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    return Path.home() / ".local" / "share" / app_name


def _verify_temp_copy(*, temp_target: Path, core_files: list[str]) -> None:
    for name in core_files:
        source = temp_target / name
        if not source.exists():
            continue
        if source.stat().st_size <= 0:
            raise ValueError(f"core file copied as empty: {source}")
        _read_json_file(source)


def _ensure_core_json_file(path: Path, default_payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    _write_json_file(path, default_payload)


def _read_json_file(path: Path) -> Any:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    return json.loads(text)


def _write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _backup_file(path: Path) -> None:
    if not path.exists():
        return
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    bak = _unique_path(path.with_suffix(path.suffix + f".bak_{ts}"))
    shutil.copy2(path, bak)


def _unique_path(candidate: Path) -> Path:
    if not candidate.exists():
        return candidate
    parent = candidate.parent
    stem = candidate.name
    for idx in range(1, 1000):
        nxt = parent / f"{stem}.{idx}"
        if not nxt.exists():
            return nxt
    raise RuntimeError(f"unable to allocate unique path for: {candidate}")
