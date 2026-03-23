from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _write_policy(root: Path) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    payload = {
        "data_dir": "local_data",
        "knowledge_file": "knowledge_base.json",
        "output_dir": "artifacts",
        "state_board_file": "state_board.json",
        "user_settings_file": "user_settings.json",
    }
    (root / "config" / "partner-policy.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _wait_http_ok(url: str, timeout_sec: float = 8.0) -> None:
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if 200 <= int(resp.status) < 300:
                    return
        except Exception:
            time.sleep(0.1)
    raise AssertionError(f"Service not ready: {url}")


def _http_json(url: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None) -> tuple[int, dict]:
    data = None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url=url, data=data, method=method, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            body = resp.read().decode("utf-8")
            return int(resp.status), json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return int(exc.code), json.loads(body) if body.strip() else {}


def _http_text(url: str, method: str = "GET") -> tuple[int, str]:
    req = urllib.request.Request(url=url, method=method)
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return int(resp.status), resp.read().decode("utf-8", errors="ignore")


def _spawn(cmd: list[str], cwd: Path, env: dict) -> subprocess.Popen:
    return subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _stop(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def test_bridge_and_dashboard_e2e_action_flow(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime-root"
    _write_policy(runtime_root)
    project_root = Path(__file__).resolve().parents[1]
    bridge_port = _find_free_port()
    dashboard_port = _find_free_port()
    env = os.environ.copy()
    env["TRADE_ASSISTANT_ROOT"] = str(runtime_root)

    bridge = dashboard = None
    try:
        bridge = _spawn(
            [
                sys.executable,
                "-m",
                "app.main",
                "serve-bridge",
                "--host",
                "127.0.0.1",
                "--port",
                str(bridge_port),
                "--allow-action-execute",
            ],
            cwd=project_root,
            env=env,
        )
        dashboard = _spawn(
            [
                sys.executable,
                "-m",
                "app.main",
                "serve-dashboard",
                "--host",
                "127.0.0.1",
                "--port",
                str(dashboard_port),
            ],
            cwd=project_root,
            env=env,
        )

        _wait_http_ok(f"http://127.0.0.1:{bridge_port}/health")
        _wait_http_ok(f"http://127.0.0.1:{dashboard_port}/api/state/summary")

        status, data = _http_json(
            f"http://127.0.0.1:{bridge_port}/actions/execute",
            method="POST",
            payload={
                "model_output": '<action>generate_quote_draft:{"client":"Ali Trading","product":"A100","price":13.2,"currency":"USD"}</action>'
            },
        )
        assert status == 200
        assert int(data.get("count", 0)) == 1

        status2, summary = _http_json(f"http://127.0.0.1:{dashboard_port}/api/state/summary")
        assert status2 == 200
        assert int(summary.get("summary", {}).get("tasks_total", 0)) >= 1

        status3, latest = _http_json(f"http://127.0.0.1:{dashboard_port}/api/state/latest")
        assert status3 == 200
        assert int(latest.get("count", 0)) >= 1

        status4, diag = _http_json(f"http://127.0.0.1:{dashboard_port}/api/diagnostics/status")
        assert status4 == 200
        assert diag.get("status") in {"ok", "degraded"}
        assert isinstance(diag.get("checks"), list)
        assert isinstance(diag.get("issue_logs"), list)
    finally:
        _stop(dashboard)
        _stop(bridge)


def test_bridge_rejects_forbidden_origin_when_executing(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime-root"
    _write_policy(runtime_root)
    project_root = Path(__file__).resolve().parents[1]
    bridge_port = _find_free_port()
    env = os.environ.copy()
    env["TRADE_ASSISTANT_ROOT"] = str(runtime_root)

    bridge = None
    try:
        bridge = _spawn(
            [
                sys.executable,
                "-m",
                "app.main",
                "serve-bridge",
                "--host",
                "127.0.0.1",
                "--port",
                str(bridge_port),
                "--allow-action-execute",
            ],
            cwd=project_root,
            env=env,
        )
        _wait_http_ok(f"http://127.0.0.1:{bridge_port}/health")

        status, payload = _http_json(
            f"http://127.0.0.1:{bridge_port}/actions/execute",
            method="POST",
            payload={
                "model_output": '<action>generate_quote_draft:{"client":"Ali Trading","product":"A100","price":13.2,"currency":"USD"}</action>'
            },
            headers={"Origin": "http://evil.example.com"},
        )
        assert status == 403
        assert payload.get("error") == "forbidden_origin"
    finally:
        _stop(bridge)


def test_feedback_inbox_and_list_endpoint(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime-root"
    _write_policy(runtime_root)
    project_root = Path(__file__).resolve().parents[1]
    bridge_port = _find_free_port()
    env = os.environ.copy()
    env["TRADE_ASSISTANT_ROOT"] = str(runtime_root)

    bridge = None
    try:
        bridge = _spawn(
            [
                sys.executable,
                "-m",
                "app.main",
                "serve-bridge",
                "--host",
                "127.0.0.1",
                "--port",
                str(bridge_port),
                "--allow-action-execute",
            ],
            cwd=project_root,
            env=env,
        )
        _wait_http_ok(f"http://127.0.0.1:{bridge_port}/health")

        add_status, add_payload = _http_json(
            f"http://127.0.0.1:{bridge_port}/feedback/add",
            method="POST",
            payload={"source": "desktop", "text": "Need clearer overdue action guidance"},
        )
        assert add_status == 200
        assert add_payload.get("status") == "ok"

        list_status, list_payload = _http_json(
            f"http://127.0.0.1:{bridge_port}/feedback/list",
            method="POST",
            payload={"limit": 20},
        )
        assert list_status == 200
        assert list_payload.get("status") == "ok"
        assert int(list_payload.get("count", 0)) >= 1
        assert any("overdue action guidance" in str(item.get("text", "")) for item in list_payload.get("rows", []))
        assert isinstance(list_payload.get("summary", {}), dict)

        inbox_status, inbox_html = _http_text(f"http://127.0.0.1:{bridge_port}/feedback/inbox")
        assert inbox_status == 200
        assert "Feedback Inbox" in inbox_html
    finally:
        _stop(bridge)
