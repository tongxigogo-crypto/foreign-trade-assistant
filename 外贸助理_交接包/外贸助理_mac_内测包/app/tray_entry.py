from __future__ import annotations

import sys
from typing import Sequence

try:
    from .tray_app import run_tray
except ImportError:
    from app.tray_app import run_tray


def run_tray_entry(argv: Sequence[str] | None = None) -> int:
    args = list(argv or [])
    if args and args[0] == "cli":
        try:
            from .main import run_cli
        except ImportError:
            from app.main import run_cli
        return run_cli(args[1:])
    return run_tray()


if __name__ == "__main__":
    raise SystemExit(run_tray_entry(sys.argv[1:]))
