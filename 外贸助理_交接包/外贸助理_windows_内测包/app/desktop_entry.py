from __future__ import annotations

from .main import run_cli


def run_desktop_entry() -> int:
    return run_cli(["desktop"])


if __name__ == "__main__":
    raise SystemExit(run_desktop_entry())
