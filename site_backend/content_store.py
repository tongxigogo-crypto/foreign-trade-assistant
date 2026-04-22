from __future__ import annotations

import base64
import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CONTENT: dict[str, Any] = {
    "strings": {
        "zh": {
            "brand_name": "",
            "hero_intro": "",
            "hero_bridge": "",
            "hero_summary_title": "",
            "hero_summary_body": "",
            "pet_ip_title": "",
            "pet_ip_body": "",
            "trade_assistant_title": "",
            "trade_assistant_body": "",
            "pet_trade_title": "",
            "pet_trade_body": "",
            "mini_program_title": "",
            "mini_program_body": "",
            "contact_title": "",
            "contact_body": "",
        },
        "en": {
            "brand_name": "",
            "hero_intro": "",
            "hero_bridge": "",
            "hero_summary_title": "",
            "hero_summary_body": "",
            "pet_ip_title": "",
            "pet_ip_body": "",
            "trade_assistant_title": "",
            "trade_assistant_body": "",
            "pet_trade_title": "",
            "pet_trade_body": "",
            "mini_program_title": "",
            "mini_program_body": "",
            "contact_title": "",
            "contact_body": "",
        },
    },
    "images": {
        "home.hero": "",
        "home.trade_assistant": "",
        "home.pet_trade": "",
        "home.mini_program": "",
    },
}


class ContentStore:
    def __init__(self, site_dir: Path) -> None:
        self.site_dir = site_dir
        self.content_dir = site_dir / "content"
        self.content_path = self.content_dir / "site-content.json"
        self.backup_path = self.content_dir / "site-content.backup.json"
        self.meta_path = self.content_dir / "site-content.meta.json"
        self.upload_dir = site_dir / "assets" / "uploads"

    def load(self) -> dict[str, Any]:
        if not self.content_path.exists():
            return copy.deepcopy(DEFAULT_CONTENT)
        with self.content_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        merged = copy.deepcopy(DEFAULT_CONTENT)
        merged["strings"].update(data.get("strings", {}))
        merged["images"].update(data.get("images", {}))
        return merged

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = copy.deepcopy(DEFAULT_CONTENT)
        data["strings"].update(payload.get("strings", {}))
        data["images"].update(payload.get("images", {}))
        now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

        self.content_dir.mkdir(parents=True, exist_ok=True)
        if self.content_path.exists():
            self.backup_path.write_text(self.content_path.read_text(encoding="utf-8"), encoding="utf-8")
        tmp_path = self.content_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(self.content_path)
        self._write_meta(now)
        return data

    def load_meta(self) -> dict[str, Any]:
        if not self.meta_path.exists():
            return {
                "updated_at": None,
                "history": [],
            }
        with self.meta_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return {
            "updated_at": data.get("updated_at"),
            "history": list(data.get("history", [])),
        }

    def _write_meta(self, updated_at: str) -> None:
        meta = self.load_meta()
        history = list(meta.get("history", []))
        history.insert(
            0,
            {
                "timestamp": updated_at,
                "event": "content_saved",
                "label": "内容已保存",
            },
        )
        payload = {
            "updated_at": updated_at,
            "history": history[:12],
        }
        tmp_path = self.meta_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(self.meta_path)

    def save_asset(self, filename: str, content_base64: str) -> str:
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip("-")
        if not safe_name:
            raise ValueError("invalid filename")
        raw = base64.b64decode(content_base64.encode("ascii"), validate=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        target = self.upload_dir / safe_name
        target.write_bytes(raw)
        relative = target.relative_to(self.site_dir).as_posix()
        return f"./{relative}"
