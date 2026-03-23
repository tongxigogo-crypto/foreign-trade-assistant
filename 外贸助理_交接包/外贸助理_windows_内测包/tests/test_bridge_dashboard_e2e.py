import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.action_protocol import ActionExecutor
from app.bridge_server import _build_handler as build_bridge_handler
from app.capsule_builder import CapsuleBuilder
from app.config import AppConfig
from app.contracts import CustomerProfile
from app.dashboard_server import _build_handler as build_dashboard_handler
from app.local_store import LocalKnowledgeStore
from app.orchestrator import TradeAssistantOrchestrator
from app.state_board import StateBoard
from app.user_settings import UserSettingsStore


def _create_runtime(tmp_path: Path):
    root = tmp_path / "runtime"
    (root / "config").mkdir(parents=True)
    (root / "config" / "partner-policy.json").write_text(
        json.dumps(
            {
                "data_dir": "local_data",
                "knowledge_file": "knowledge_base.json",
                "output_dir": "artifacts",
                "state_board_file": "state_board.json",
                "user_settings_file": "user_settings.json",
            }
        ),
        encoding="utf-8",
    )
    config = AppConfig.load(root)
    store = LocalKnowledgeStore(config.knowledge_file)
    store.ensure_initialized()
    store.upsert_customer(CustomerProfile(customer_id="ali-001", name="Ali Trading", region="Dubai"))
    state_board = StateBoard(config.state_board_file)
    state_board.ensure_initialized()
    action_executor = ActionExecutor(store=store, output_dir=config.output_dir)
    orchestrator = TradeAssistantOrchestrator(capsule_builder=CapsuleBuilder(store=store), action_executor=action_executor)
    settings_store = UserSettingsStore(config.user_settings_file)
    return config, action_executor, orchestrator, state_board, settings_store


def _serve(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _post_json(url: str, payload: dict) -> tuple[int, dict]:
    req = Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body)


def _get_json(url: str) -> tuple[int, dict]:
    req = Request(url, method="GET")
    with urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def test_bridge_execute_updates_dashboard_state(tmp_path: Path) -> None:
    config, action_executor, orchestrator, state_board, settings_store = _create_runtime(tmp_path)
    bridge_handler = build_bridge_handler(orchestrator=orchestrator, state_board=state_board, allow_action_execute=True)
    dashboard_handler = build_dashboard_handler(state_board=state_board, action_executor=action_executor, settings_store=settings_store)
    bridge_server, _ = _serve(bridge_handler)
    dashboard_server, _ = _serve(dashboard_handler)
    try:
        bridge_url = f"http://127.0.0.1:{bridge_server.server_address[1]}"
        dashboard_url = f"http://127.0.0.1:{dashboard_server.server_address[1]}"
        execute_status, execute_data = _post_json(
            f"{bridge_url}/actions/execute",
            {"model_output": '<action>generate_quote_draft:{"client":"Ali Trading","product":"A100","price":13.2,"currency":"USD"}</action>'},
        )
        assert execute_status == 200
        assert execute_data.get("count") == 1
        assert execute_data["results"][0]["status"] == "success"
        assert (config.output_dir).exists()

        kanban_status, kanban_data = _get_json(f"{dashboard_url}/api/state/kanban")
        assert kanban_status == 200
        waiting_tasks = kanban_data.get("columns", {}).get("waiting_reply", [])
        assert any("Ali Trading" in str(task.get("customer_name", "")) for task in waiting_tasks)

        focus_status, focus_data = _get_json(f"{dashboard_url}/api/state/focus?limit=8")
        assert focus_status == 200
        assert focus_data.get("rows")
    finally:
        bridge_server.shutdown()
        bridge_server.server_close()
        dashboard_server.shutdown()
        dashboard_server.server_close()


def test_dashboard_output_dir_update_keeps_existing_settings_fields(tmp_path: Path) -> None:
    _config, action_executor, orchestrator, state_board, settings_store = _create_runtime(tmp_path)
    settings_store.settings_file.write_text(
        json.dumps(
            {
                "output_dir": "",
                "auto_open_dashboard_after_wizard": False,
                "template_lang": "zh",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    dashboard_handler = build_dashboard_handler(state_board=state_board, action_executor=action_executor, settings_store=settings_store)
    dashboard_server, _ = _serve(dashboard_handler)
    try:
        dashboard_url = f"http://127.0.0.1:{dashboard_server.server_address[1]}"
        new_output_dir = str(tmp_path / "custom-output")
        status, payload = _post_json(f"{dashboard_url}/api/settings/output-dir", {"output_dir": new_output_dir})
        assert status == 200
        assert payload.get("status") == "ok"
    finally:
        dashboard_server.shutdown()
        dashboard_server.server_close()

    saved = json.loads(settings_store.settings_file.read_text(encoding="utf-8"))
    assert saved.get("output_dir") == str((tmp_path / "custom-output").resolve())
    assert saved.get("auto_open_dashboard_after_wizard") is False
    assert saved.get("template_lang") == "zh"
