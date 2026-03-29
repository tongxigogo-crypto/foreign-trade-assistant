from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from typing import Sequence

try:
    from .tray_app import run_tray
except ImportError:
    from app.tray_app import run_tray


def _crash_log_path() -> Path:
    env_root = os.getenv("TRADE_ASSISTANT_ROOT", "").strip()
    if env_root:
        root = Path(env_root).expanduser()
    elif getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
    else:
        root = Path(__file__).resolve().parents[1]
    return root / "local_data" / "logs" / "tray_crash.log"


def _write_crash_log(exc: BaseException) -> None:
    try:
        path = _crash_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n=== tray_entry crash ===\n")
            fh.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    except Exception:
        pass


def run_tray_entry(argv: Sequence[str] | None = None) -> int:
    args = list(argv or [])
    try:
        if args and args[0] == "cli":
            try:
                from .main import run_cli
            except ImportError:
                from app.main import run_cli
            return run_cli(args[1:])
        return run_tray()
    except BaseException as exc:
        _write_crash_log(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(run_tray_entry(sys.argv[1:]))
