from __future__ import annotations

import sys
from typing import Sequence

try:
    from .main import run_cli
    from .tray_app import run_tray
except ImportError:  # frozen entrypoint fallback
    from app.main import run_cli
    from app.tray_app import run_tray


def run_tray_entry(argv: Sequence[str] | None = None) -> int:
    args = list(argv or [])
    if args and args[0] == "cli":
        return run_cli(args[1:])
    if args and args[0] == "tray":
        return run_tray()
    return run_cli(["desktop"])


if __name__ == "__main__":
    raise SystemExit(run_tray_entry(sys.argv[1:]))
