import json
from pathlib import Path
from typing import Dict, Any


def load_pricing(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))

