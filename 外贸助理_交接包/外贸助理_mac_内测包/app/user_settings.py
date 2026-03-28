from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class UserSettings:
    output_dir: str = ""
    auto_open_dashboard_after_wizard: bool = True
    extension_domain_whitelist: list[str] = field(default_factory=list)
    mail_provider: str = "gmail"
    mail_account: str = ""
    mail_folder: str = "INBOX"
    mail_days: int = 30
    mail_max_messages: int = 200
    mail_password: str = ""
    remember_mail_password: bool = False
    api_provider: str = "nvidia"
    api_key: str = ""
    api_model: str = ""
    api_url: str = ""
    api_timeout_sec: int = 30
    api_use_local_context: bool = True
    error_reporting_enabled: bool = True
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = dict(self.extra)
        payload.update(
            {
                "output_dir": self.output_dir,
                "auto_open_dashboard_after_wizard": self.auto_open_dashboard_after_wizard,
                "extension_domain_whitelist": list(self.extension_domain_whitelist),
                "mail_provider": self.mail_provider,
                "mail_account": self.mail_account,
                "mail_folder": self.mail_folder,
                "mail_days": int(self.mail_days),
                "mail_max_messages": int(self.mail_max_messages),
                "mail_password": self.mail_password if self.remember_mail_password else "",
                "remember_mail_password": bool(self.remember_mail_password),
                "api_provider": self.api_provider,
                "api_key": self.api_key,
                "api_model": self.api_model,
                "api_url": self.api_url,
                "api_timeout_sec": int(self.api_timeout_sec),
                "api_use_local_context": bool(self.api_use_local_context),
                "error_reporting_enabled": bool(self.error_reporting_enabled),
            }
        )
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> "UserSettings":
        output_dir = str(data.get("output_dir", "")).strip()
        auto_open = bool(data.get("auto_open_dashboard_after_wizard", True))
        whitelist_raw = data.get("extension_domain_whitelist", [])
        whitelist: list[str] = []
        if isinstance(whitelist_raw, list):
            whitelist = [str(item).strip() for item in whitelist_raw if str(item).strip()]
        mail_provider = str(data.get("mail_provider", "gmail")).strip().lower() or "gmail"
        if mail_provider not in {"gmail", "outlook"}:
            mail_provider = "gmail"
        mail_account = str(data.get("mail_account", "")).strip()
        mail_folder = str(data.get("mail_folder", "INBOX")).strip() or "INBOX"
        try:
            mail_days = int(data.get("mail_days", 30))
        except (TypeError, ValueError):
            mail_days = 30
        try:
            mail_max_messages = int(data.get("mail_max_messages", 200))
        except (TypeError, ValueError):
            mail_max_messages = 200
        remember_mail_password = bool(data.get("remember_mail_password", False))
        mail_password = str(data.get("mail_password", "")).strip() if remember_mail_password else ""
        api_provider = str(data.get("api_provider", "nvidia")).strip().lower() or "nvidia"
        if api_provider not in {"nvidia", "openai", "openrouter", "deepseek", "qwen", "doubao", "google", "custom"}:
            api_provider = "nvidia"
        api_key = str(data.get("api_key", "")).strip()
        api_model = str(data.get("api_model", "")).strip()
        api_url = str(data.get("api_url", "")).strip()
        try:
            api_timeout_sec = int(data.get("api_timeout_sec", 30))
        except (TypeError, ValueError):
            api_timeout_sec = 30
        api_use_local_context = bool(data.get("api_use_local_context", True))
        error_reporting_enabled = bool(data.get("error_reporting_enabled", True))
        extra = {
            key: value
            for key, value in data.items()
            if key
            not in {
                "output_dir",
                "auto_open_dashboard_after_wizard",
                "extension_domain_whitelist",
                "mail_provider",
                "mail_account",
                "mail_folder",
                "mail_days",
                "mail_max_messages",
                "mail_password",
                "remember_mail_password",
                "api_provider",
                "api_key",
                "api_model",
                "api_url",
                "api_timeout_sec",
                "api_use_local_context",
                "error_reporting_enabled",
            }
        }
        return cls(
            output_dir=output_dir,
            auto_open_dashboard_after_wizard=auto_open,
            extension_domain_whitelist=whitelist,
            mail_provider=mail_provider,
            mail_account=mail_account,
            mail_folder=mail_folder,
            mail_days=max(1, min(mail_days, 3650)),
            mail_max_messages=max(1, min(mail_max_messages, 5000)),
            mail_password=mail_password,
            remember_mail_password=remember_mail_password,
            api_provider=api_provider,
            api_key=api_key,
            api_model=api_model,
            api_url=api_url,
            api_timeout_sec=max(5, min(api_timeout_sec, 180)),
            api_use_local_context=api_use_local_context,
            error_reporting_enabled=error_reporting_enabled,
            extra=extra,
        )


class UserSettingsStore:
    def __init__(self, settings_file: Path) -> None:
        self.settings_file = settings_file

    def load(self) -> UserSettings:
        if not self.settings_file.exists():
            return UserSettings()
        try:
            raw = self.settings_file.read_text(encoding="utf-8")
            data = json.loads(raw) if raw.strip() else {}
            return UserSettings.from_dict(data)
        except (OSError, json.JSONDecodeError):
            return UserSettings()

    def save(self, settings: UserSettings) -> None:
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings_file.write_text(json.dumps(settings.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
