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
            "hero_subtitle": "",
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
            "hero_subtitle": "",
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
                "entry_mode": "none",
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
                "entry_mode": "none",
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
                "entry_mode": "none",
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
                "entry_mode": "none",
            },
        ],
    },
    "pet_product_template": {
        "path": "./pet-product-template.html",
        "eyebrow": "",
        "title": "",
        "intro": "",
        "status_label": "",
        "cta_label": "",
        "cta_url": "",
        "sections": {
            "story_title": "",
            "story_body": "",
            "spec_title": "",
            "spec_body": "",
            "use_case_title": "",
            "use_case_body": "",
            "care_title": "",
            "care_body": "",
        },
        "specs": [
            {"label": "", "value": ""},
            {"label": "", "value": ""},
            {"label": "", "value": ""},
        ],
        "seo": {
            "title": "",
            "description": "",
            "canonical_path": "",
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
        self.default_content = self._merge_content({})

    def _merge_content(self, payload: dict[str, Any]) -> dict[str, Any]:
        merged = copy.deepcopy(self.default_content)
        merged["strings"].update(payload.get("strings", {}))
        merged["images"].update(payload.get("images", {}))

        incoming_gallery = payload.get("pet_products_gallery", {})
        base_cards = copy.deepcopy(merged["pet_products_gallery"]["cards"])
        legacy_cards = incoming_gallery.get("cards", [])
        merged_gallery: dict[str, Any] = {"cards": copy.deepcopy(base_cards)}
        for lang in ("zh", "en"):
            incoming_cards = incoming_gallery.get(lang, {}).get("cards")
            if incoming_cards is None and lang == "zh":
                incoming_cards = legacy_cards
            lang_cards = copy.deepcopy(base_cards)
            for index, card in enumerate(lang_cards):
                if index < len(incoming_cards or []) and isinstance(incoming_cards[index], dict):
                    card.update(incoming_cards[index])
            merged_gallery[lang] = {"cards": lang_cards}
        merged_gallery["cards"] = copy.deepcopy(merged_gallery["zh"]["cards"])
        merged["pet_products_gallery"] = merged_gallery

        incoming_template = payload.get("pet_product_template", {})
        merged["pet_product_template"].update(
            {key: value for key, value in incoming_template.items() if key not in {"sections", "specs", "seo"}}
        )
        merged["pet_product_template"]["sections"].update(incoming_template.get("sections", {}))

        incoming_specs = incoming_template.get("specs", [])
        base_specs = copy.deepcopy(merged["pet_product_template"]["specs"])
        for index, spec in enumerate(base_specs):
            if index < len(incoming_specs) and isinstance(incoming_specs[index], dict):
                spec.update(incoming_specs[index])
        merged["pet_product_template"]["specs"] = base_specs
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
        self._write_discovery_files(data)
        self._write_meta(now, "content_saved", "content_saved")
        return data

    def load_meta(self) -> dict[str, Any]:
        if not self.meta_path.exists():
            return {"updated_at": None, "history": []}
        with self.meta_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return {"updated_at": data.get("updated_at"), "history": list(data.get("history", []))}

    def publish(self) -> dict[str, Any]:
        updated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        self._write_discovery_files(self.load())
        self._write_meta(updated_at, "content_published", "content_published")
        return self.load_meta()

    def _write_meta(self, updated_at: str, event: str, label: str) -> None:
        meta = self.load_meta()
        history = list(meta.get("history", []))
        history.insert(0, {"timestamp": updated_at, "event": event, "label": label})
        payload = {"updated_at": updated_at, "history": history[:12]}
        self.content_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.meta_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(self.meta_path)

    def _write_discovery_files(self, content: dict[str, Any]) -> None:
        base_url = "https://tongstudio.example.com"
        template_path = str(content.get("pet_product_template", {}).get("path") or "./pet-product-template.html")
        template_url = f"{base_url}/{template_path.lstrip('./')}"
        robots = "\n".join(
            [
                "User-agent: *",
                "Allow: /",
                f"Sitemap: {base_url}/sitemap.xml",
                "",
            ]
        )
        sitemap = "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                "  <url>",
                f"    <loc>{base_url}/</loc>",
                "  </url>",
                "  <url>",
                f"    <loc>{template_url}</loc>",
                "  </url>",
                "</urlset>",
                "",
            ]
        )
        (self.site_dir / "robots.txt").write_text(robots, encoding="utf-8")
        (self.site_dir / "sitemap.xml").write_text(sitemap, encoding="utf-8")

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
