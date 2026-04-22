from __future__ import annotations

import base64
import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


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
    "pet_products_gallery": {
        "cards": [
            {
                "id": "harness",
                "image": "",
                "cover_label": "",
                "cover_title": "",
                "title": "",
                "summary": "",
                "tag": "",
                "status": "coming_soon",
            },
            {
                "id": "toys",
                "image": "",
                "cover_label": "",
                "cover_title": "",
                "title": "",
                "summary": "",
                "tag": "",
                "status": "coming_soon",
            },
            {
                "id": "leash",
                "image": "",
                "cover_label": "",
                "cover_title": "",
                "title": "",
                "summary": "",
                "tag": "",
                "status": "coming_soon",
            },
            {
                "id": "beds",
                "image": "",
                "cover_label": "",
                "cover_title": "",
                "title": "",
                "summary": "",
                "tag": "",
                "status": "coming_soon",
            },
        ],
    },
    "pet_product_template": {
        "path": "./pet-product-template.html",
        "title": "",
        "intro": "",
        "sections": {
            "story_title": "",
            "story_body": "",
            "spec_title": "",
            "spec_body": "",
            "use_case_title": "",
            "use_case_body": "",
        },
        "seo": {
            "title": "",
            "description": "",
        },
    },
}


class ContentStore:
    def __init__(
        self,
        site_dir: Path,
        default_content: dict[str, Any] | None = None,
        source_html_path: Path | None = None,
        extract_callback: Callable[[str], dict[str, Any]] | None = None,
        sync_callback: Callable[[str, dict[str, Any]], str] | None = None,
    ) -> None:
        self.site_dir = site_dir
        self.default_content = copy.deepcopy(default_content or DEFAULT_CONTENT)
        self.source_html_path = source_html_path
        self.extract_callback = extract_callback
        self.sync_callback = sync_callback
        self.content_dir = site_dir / "content"
        self.content_path = self.content_dir / "site-content.json"
        self.backup_path = self.content_dir / "site-content.backup.json"
        self.meta_path = self.content_dir / "site-content.meta.json"
        self.upload_dir = site_dir / "assets" / "uploads"

    def _merge_content(self, payload: dict[str, Any]) -> dict[str, Any]:
        merged = copy.deepcopy(self.default_content)
        merged["strings"].update(payload.get("strings", {}))
        merged["images"].update(payload.get("images", {}))
        incoming_gallery = payload.get("pet_products_gallery", {})
        incoming_cards = incoming_gallery.get("cards", [])
        base_cards = copy.deepcopy(merged["pet_products_gallery"]["cards"])
        for index, card in enumerate(base_cards):
            if index < len(incoming_cards) and isinstance(incoming_cards[index], dict):
                card.update(incoming_cards[index])
        merged["pet_products_gallery"] = {"cards": base_cards}
        incoming_template = payload.get("pet_product_template", {})
        merged["pet_product_template"].update(
            {key: value for key, value in incoming_template.items() if key != "sections" and key != "seo"}
        )
        merged["pet_product_template"]["sections"].update(incoming_template.get("sections", {}))
        merged["pet_product_template"]["seo"].update(incoming_template.get("seo", {}))
        return merged

    def load(self) -> dict[str, Any]:
        if not self.content_path.exists():
            if self.source_html_path and self.source_html_path.exists() and self.extract_callback:
                extracted = self.extract_callback(self.source_html_path.read_text(encoding="utf-8"))
                return self._merge_content(extracted)
            return copy.deepcopy(self.default_content)
        with self.content_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return self._merge_content(data)

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._merge_content(payload)
        now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

        self.content_dir.mkdir(parents=True, exist_ok=True)
        if self.content_path.exists():
            self.backup_path.write_text(self.content_path.read_text(encoding="utf-8"), encoding="utf-8")
        tmp_path = self.content_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(self.content_path)
        if self.source_html_path and self.sync_callback:
            html = self.source_html_path.read_text(encoding="utf-8")
            updated_html = self.sync_callback(html, data)
            self.source_html_path.write_text(updated_html, encoding="utf-8")
        self._write_meta(now, "content_saved", "内容已保存")
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

    def publish(self) -> dict[str, Any]:
        updated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        self._write_meta(updated_at, "content_published", "内容已发布")
        return self.load_meta()

    def _write_meta(self, updated_at: str, event: str, label: str) -> None:
        meta = self.load_meta()
        history = list(meta.get("history", []))
        history.insert(
            0,
            {
                "timestamp": updated_at,
                "event": event,
                "label": label,
            },
        )
        payload = {
            "updated_at": updated_at,
            "history": history[:12],
        }
        self.content_dir.mkdir(parents=True, exist_ok=True)
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
