from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from .config import AppConfig
from .data_migration import LATEST_SCHEMA_VERSION, run_json_schema_migrations
from .version import APP_VERSION


def export_data_bundle(config: AppConfig, bundle_path: Path, *, include_artifacts: bool = True) -> dict:
    data_root = config.data_dir
    data_root.mkdir(parents=True, exist_ok=True)
    _ensure_core_files(config)

    core_paths = [
        config.knowledge_file,
        config.state_board_file,
        config.user_settings_file,
    ]
    include_paths = [path for path in core_paths if path.exists() and path.is_file()]

    if include_artifacts and config.output_dir.exists() and config.output_dir.is_dir():
        include_paths.extend(path for path in config.output_dir.rglob("*") if path.is_file())

    diagnostics_dir = data_root / "diagnostics"
    if diagnostics_dir.exists() and diagnostics_dir.is_dir():
        include_paths.extend(path for path in diagnostics_dir.rglob("*") if path.is_file())

    unique_paths = sorted({path.resolve() for path in include_paths})
    entries = [_relative_data_entry(path, data_root) for path in unique_paths]

    required_entries = {
        _relative_data_entry(config.knowledge_file, data_root),
        _relative_data_entry(config.state_board_file, data_root),
        _relative_data_entry(config.user_settings_file, data_root),
    }
    if not required_entries.issubset(set(entries)):
        missing = sorted(required_entries.difference(set(entries)))
        raise ValueError(f"Core data files missing from export set: {missing}")

    manifest = {
        "format": "trade_assistant_data_bundle_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "app_version": APP_VERSION,
        "schema_version": LATEST_SCHEMA_VERSION,
        "data_root": data_root.name,
        "include_artifacts": bool(include_artifacts),
        "required_entries": sorted(required_entries),
        "entries": entries,
    }

    bundle_path = bundle_path.expanduser().resolve()
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        for source in unique_paths:
            arcname = _relative_data_entry(source, data_root)
            zf.write(source, arcname=arcname)

    return {
        "status": "ok",
        "path": str(bundle_path),
        "entries": len(entries),
        "core_entries": sorted(required_entries),
    }


def import_data_bundle(config: AppConfig, bundle_path: Path) -> dict:
    bundle_path = bundle_path.expanduser().resolve()
    if not bundle_path.exists() or not bundle_path.is_file():
        raise ValueError(f"Bundle file not found: {bundle_path}")

    data_root = config.data_dir
    required_entries = {
        _relative_data_entry(config.knowledge_file, data_root),
        _relative_data_entry(config.state_board_file, data_root),
        _relative_data_entry(config.user_settings_file, data_root),
    }

    with tempfile.TemporaryDirectory(prefix="trade_assistant_bundle_") as tmp:
        tmp_root = Path(tmp)
        bundle_for_read = bundle_path
        if _is_within(bundle_path, data_root):
            copied_bundle = tmp_root / "bundle_copy.zip"
            shutil.copy2(bundle_path, copied_bundle)
            bundle_for_read = copied_bundle

        restore_root = tmp_root / "restore"
        restore_root.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(bundle_for_read, mode="r") as zf:
            names = zf.namelist()
            if "manifest.json" not in names:
                raise ValueError("Bundle is missing manifest.json")
            for name in names:
                _validate_zip_member(name)
            payload = json.loads(zf.read("manifest.json").decode("utf-8"))
            declared_required = set(payload.get("required_entries", [])) if isinstance(payload, dict) else set()
            effective_required = required_entries.union(declared_required)
            if not effective_required.issubset(set(names)):
                missing = sorted(effective_required.difference(set(names)))
                raise ValueError(f"Bundle missing required entries: {missing}")
            zf.extractall(path=restore_root)

        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = data_root.parent / f"{data_root.name}_backup_{ts}"
        if data_root.exists():
            shutil.copytree(data_root, backup_path, dirs_exist_ok=True)

        try:
            if data_root.exists():
                shutil.rmtree(data_root)
            shutil.copytree(restore_root, data_root)
        except OSError:
            if backup_path.exists():
                if data_root.exists():
                    shutil.rmtree(data_root)
                shutil.copytree(backup_path, data_root, dirs_exist_ok=True)
            raise
    migration = run_json_schema_migrations(
        data_dir=config.data_dir,
        knowledge_file_name=config.knowledge_file.name,
        state_board_file_name=config.state_board_file.name,
        user_settings_file_name=config.user_settings_file.name,
    )

    return {
        "status": "ok",
        "path": str(bundle_path),
        "backup_path": str(backup_path),
        "restored_data_dir": str(data_root),
        "migration": migration,
    }


def _ensure_core_files(config: AppConfig) -> None:
    if not config.knowledge_file.exists():
        config.knowledge_file.parent.mkdir(parents=True, exist_ok=True)
        config.knowledge_file.write_text("{}\n", encoding="utf-8")
    if not config.state_board_file.exists():
        config.state_board_file.parent.mkdir(parents=True, exist_ok=True)
        config.state_board_file.write_text("{}\n", encoding="utf-8")
    if not config.user_settings_file.exists():
        config.user_settings_file.parent.mkdir(parents=True, exist_ok=True)
        config.user_settings_file.write_text("{}\n", encoding="utf-8")


def _relative_data_entry(path: Path, data_root: Path) -> str:
    path = path.resolve()
    data_root = data_root.resolve()
    try:
        rel = path.relative_to(data_root)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Path is outside data directory: {path}") from exc
    return rel.as_posix()


def _validate_zip_member(name: str) -> None:
    pure = PurePosixPath(name)
    if pure.is_absolute():
        raise ValueError(f"Unsafe absolute path in bundle: {name}")
    if any(part == ".." for part in pure.parts):
        raise ValueError(f"Unsafe parent reference in bundle: {name}")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False
