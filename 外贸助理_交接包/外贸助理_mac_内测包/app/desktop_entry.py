from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

try:
    from .main import run_cli
except ImportError:
    from app.main import run_cli


def _crash_log_path() -> Path:
    env_root = os.getenv("TRADE_ASSISTANT_ROOT", "").strip()
    if env_root:
        root = Path(env_root).expanduser()
    elif getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
    else:
        root = Path(__file__).resolve().parents[1]
    return root / "local_data" / "logs" / "desktop_crash.log"


def _write_crash_log(exc: BaseException) -> None:
    try:
        path = _crash_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n=== desktop_entry crash ===\n")
            fh.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    except Exception:
        pass


def _install_exception_guards() -> None:
    def _handle(exc_type, exc, tb) -> None:  # type: ignore[override]
        if isinstance(exc, BaseException):
            _write_crash_log(exc)

    sys.excepthook = _handle
    if hasattr(sys, "unraisablehook"):
        def _handle_unraisable(unraisable) -> None:  # type: ignore[override]
            exc = getattr(unraisable, "exc_value", None)
            if isinstance(exc, BaseException):
                _write_crash_log(exc)
        sys.unraisablehook = _handle_unraisable
    if hasattr(__import__("threading"), "excepthook"):
        import threading

        def _thread_hook(args: threading.ExceptHookArgs) -> None:
            if isinstance(args.exc_value, BaseException):
                _write_crash_log(args.exc_value)
        threading.excepthook = _thread_hook


def run_desktop_entry() -> int:
    _install_exception_guards()
    try:
        return run_cli(["desktop"])
    except BaseException as exc:
        _write_crash_log(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(run_desktop_entry())
