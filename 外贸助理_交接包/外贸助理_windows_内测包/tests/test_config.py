from __future__ import annotations

import json
from pathlib import Path

from app.config import AppConfig


def test_load_without_partner_policy_uses_defaults(tmp_path: Path) -> None:
    cfg = AppConfig.load(tmp_path)
    assert cfg.root_dir == tmp_path
    assert cfg.data_dir == tmp_path / "local_data"
    assert cfg.knowledge_file == cfg.data_dir / "knowledge_base.json"
    assert cfg.output_dir == cfg.data_dir / "artifacts"
    assert cfg.state_board_file == cfg.data_dir / "state_board.json"
    assert cfg.user_settings_file == cfg.data_dir / "user_settings.json"


def test_load_with_partner_policy_uses_overrides(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    policy_path = config_dir / "partner-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "data_dir": "data_custom",
                "knowledge_file": "kb.json",
                "output_dir": "outbox",
                "state_board_file": "state.json",
                "user_settings_file": "settings.json",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    cfg = AppConfig.load(tmp_path)
    assert cfg.data_dir == tmp_path / "data_custom"
    assert cfg.knowledge_file == cfg.data_dir / "kb.json"
    assert cfg.output_dir == cfg.data_dir / "outbox"
    assert cfg.state_board_file == cfg.data_dir / "state.json"
    assert cfg.user_settings_file == cfg.data_dir / "settings.json"
