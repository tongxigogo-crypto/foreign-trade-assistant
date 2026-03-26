from __future__ import annotations

import json
from pathlib import Path


def test_sample_user_settings_does_not_ship_api_key() -> None:
    settings_path = Path("local_data/user_settings.json")
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert data.get("api_key", "") == ""
