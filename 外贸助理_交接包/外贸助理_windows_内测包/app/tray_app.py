from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from .update_manager import (
    check_and_prepare_update,
    is_network_error,
    open_path,
    resolve_install_dir,
    schedule_windows_inplace_update,
)
from .version import APP_VERSION

@dataclass
class ServiceRuntime:
    root_dir: Path
    bridge_host: str = "127.0.0.1"
    bridge_port: int = 8765
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8787
    bridge_process: subprocess.Popen | None = None
    dashboard_process: subprocess.Popen | None = None

    def start(self) -> None:
        self.stop()
        self.bridge_process = self._spawn_service(
            [
                "serve-bridge",
                "--host",
                self.bridge_host,
                "--port",
                str(self.bridge_port),
                "--allow-action-execute",
            ]
        )
        self.dashboard_process = self._spawn_service(
            [
                "serve-dashboard",
                "--host",
                self.dashboard_host,
                "--port",
                str(self.dashboard_port),
            ]
        )

    def restart(self) -> None:
        self.start()

    def stop(self) -> None:
        for proc in (self.bridge_process, self.dashboard_process):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except OSError:
                    pass
        self.bridge_process = None
        self.dashboard_process = None

    def open_dashboard(self) -> None:
        webbrowser.open(self.dashboard_url)

    @property
    def dashboard_url(self) -> str:
        return f"http://{self.dashboard_host}:{self.dashboard_port}/?from=tray&tour=0"

    def wait_until_ready(self, timeout_sec: int = 12) -> bool:
        return self._wait_url(f"http://{self.bridge_host}:{self.bridge_port}/health", timeout_sec) and self._wait_url(
            self.dashboard_url,
            timeout_sec,
        )

    def _spawn_service(self, command: list[str]) -> subprocess.Popen:
        cmd = _service_command(command)
        env = os.environ.copy()
        env["TRADE_ASSISTANT_ROOT"] = str(self.root_dir)
        kwargs: dict = {"cwd": str(self.root_dir), "env": env}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        return subprocess.Popen(cmd, **kwargs)

    @staticmethod
    def _wait_url(url: str, timeout_sec: int) -> bool:
        end = time.time() + timeout_sec
        while time.time() < end:
            try:
                with urlopen(url, timeout=1) as resp:  # noqa: S310
                    if int(getattr(resp, "status", 0)) == 200:
                        return True
            except (OSError, URLError):
                time.sleep(0.35)
        return False


def run_tray() -> int:
    root_dir = _resolve_runtime_root()
    runtime = ServiceRuntime(root_dir=root_dir)
    runtime.start()
    ready = runtime.wait_until_ready(timeout_sec=14)
    try:
        pystray, menu, menu_item, image, draw = _load_tray_deps()
    except Exception as exc:  # pragma: no cover - fallback path for headless env
        print(f"[tray] unavailable ({exc})")
        runtime.stop()
        return 1

    icon = pystray.Icon(
        name="InVault",
        title="InVault",
        icon=_build_icon(image=image, draw=draw, healthy=ready),
        menu=menu(
            menu_item("打开控制面板 / Open Dashboard", lambda _icon, _item: runtime.open_dashboard()),
            menu_item("重启服务 / Restart Services", lambda _icon, _item: _restart_services(runtime, icon)),
            menu_item("一键更新 / Check Update", lambda _icon, _item: _check_update(runtime)),
            menu_item("退出 / Exit", lambda _icon, _item: _stop_tray(runtime, icon)),
        ),
    )
    runtime.open_dashboard()
    try:
        icon.run()
    finally:
        runtime.stop()
    return 0


def _restart_services(runtime: ServiceRuntime, icon) -> None:  # noqa: ANN001
    def worker() -> None:
        runtime.restart()
        ready = runtime.wait_until_ready(timeout_sec=14)
        icon.icon = _build_icon(**_load_pillow_types(), healthy=ready)

    threading.Thread(target=worker, daemon=True).start()


def _stop_tray(runtime: ServiceRuntime, icon) -> None:  # noqa: ANN001
    runtime.stop()
    icon.stop()


def _check_update(runtime: ServiceRuntime) -> None:
    def worker() -> None:
        try:
            info, launcher, prepared_path = check_and_prepare_update(
                current_version=APP_VERSION,
                updates_root=runtime.root_dir / "updates",
                root_dir=runtime.root_dir,
            )
        except Exception as exc:
            message = f"网络异常，更新失败：{exc}" if is_network_error(exc) else f"更新失败：{exc}"
            _show_dialog("error", "一键更新 / Check Update", message)
            return

        if not info.has_update:
            _show_dialog("info", "一键更新 / Check Update", "当前已是最新版本。")
            return

        try:
            install_dir = resolve_install_dir(runtime.root_dir)
            script_path = schedule_windows_inplace_update(
                update=info,
                prepared_dir=prepared_path,
                install_dir=install_dir,
                current_pid=os.getpid(),
                updates_root=runtime.root_dir / "updates",
            )
        except Exception as exc:
            if launcher:
                open_path(launcher)
            _show_dialog("error", "一键更新 / Check Update", f"更新启动失败：{exc}")
            return

        _show_dialog(
            "info",
            "一键更新 / Check Update",
            f"已开始更新：{info.latest_version}\n更新完成后将自动重启。\n\nUpdater: {script_path}",
        )
        runtime.stop()
        os._exit(0)  # noqa: S606 - intentional hard-exit for updater

    threading.Thread(target=worker, daemon=True).start()


def _build_icon(*, image, draw, healthy: bool):  # noqa: ANN001
    img = image.new("RGBA", (64, 64), (22, 22, 28, 255))
    d = draw.Draw(img)
    ring = (90, 200, 120, 255) if healthy else (230, 160, 40, 255)
    d.ellipse((8, 8, 56, 56), outline=ring, width=6)
    d.rectangle((29, 16, 35, 34), fill=ring)
    d.ellipse((29, 40, 35, 46), fill=ring)
    return img


def _load_tray_deps():  # noqa: ANN202
    import pystray
    from PIL import Image, ImageDraw

    return pystray, pystray.Menu, pystray.MenuItem, Image, ImageDraw


def _load_pillow_types():  # noqa: ANN202
    from PIL import Image, ImageDraw

    return {"image": Image, "draw": ImageDraw}


def _show_dialog(kind: str, title: str, message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        if kind == "error":
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)
        root.destroy()
    except Exception:
        print(f"[{title}] {message}")


def _resolve_runtime_root() -> Path:
    env_root = os.getenv("TRADE_ASSISTANT_ROOT", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _service_command(command: list[str]) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "cli", *command]
    return [sys.executable, "-m", "app.main", *command]
