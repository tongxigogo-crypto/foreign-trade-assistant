import json
from pathlib import Path
from typing import Dict, Any


def load_store(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"customers": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_store(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
