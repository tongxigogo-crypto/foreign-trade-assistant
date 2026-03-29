from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_POLICY = {
    "data_dir": "local_data",
    "knowledge_file": "knowledge_base.json",
    "output_dir": "artifacts",
    "state_board_file": "state_board.json",
    "user_settings_file": "user_settings.json",
}


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
        if policy_path.exists():
            data = json.loads(policy_path.read_text(encoding="utf-8"))
        else:
            data = dict(DEFAULT_POLICY)
        data_dir = root_dir / data.get("data_dir", "local_data")
        knowledge_file = data_dir / data.get("knowledge_file", "knowledge_base.json")
        output_dir = data_dir / data.get("output_dir", "artifacts")
        state_board_file = data_dir / data.get("state_board_file", "state_board.json")
        user_settings_file = data_dir / data.get("user_settings_file", "user_settings.json")
        return cls(
            root_dir=root_dir,
            data_dir=data_dir,
            knowledge_file=knowledge_file,
            output_dir=output_dir,
            state_board_file=state_board_file,
            user_settings_file=user_settings_file,
        )
