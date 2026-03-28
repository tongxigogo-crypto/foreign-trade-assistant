from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .data_migration import ensure_runtime_data_layout, resolve_data_dir


@dataclass
class AppConfig:
    root_dir: Path
    data_dir: Path
    knowledge_file: Path
    output_dir: Path
    state_board_file: Path
    user_settings_file: Path

    @classmethod
    def load(cls, root_dir: Path) -> "AppConfig":
        policy_path = root_dir / "config" / "partner-policy.json"
        data: dict = {}
        if policy_path.exists():
            data = json.loads(policy_path.read_text(encoding="utf-8"))
        declared_data_dir = str(data.get("data_dir", "local_data"))
        data_dir_mode = str(data.get("data_dir_mode", "system"))
        app_name = str(data.get("app_name", "TradeAssistant"))
        data_dir, legacy_data_dir = resolve_data_dir(
            root_dir=root_dir,
            declared_data_dir=declared_data_dir,
            data_dir_mode=data_dir_mode,
            app_name=app_name,
        )
        knowledge_file = data_dir / data.get("knowledge_file", "knowledge_base.json")
        output_dir = data_dir / data.get("output_dir", "artifacts")
        state_board_file = data_dir / data.get("state_board_file", "state_board.json")
        user_settings_file = data_dir / data.get("user_settings_file", "user_settings.json")
        ensure_runtime_data_layout(
            target_data_dir=data_dir,
            legacy_data_dir=legacy_data_dir,
            knowledge_file_name=knowledge_file.name,
            state_board_file_name=state_board_file.name,
            user_settings_file_name=user_settings_file.name,
        )
        return cls(
            root_dir=root_dir,
            data_dir=data_dir,
            knowledge_file=knowledge_file,
            output_dir=output_dir,
            state_board_file=state_board_file,
            user_settings_file=user_settings_file,
        )
