from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .capsule_builder import CapsuleBuilder
from .config import AppConfig
from .contracts import CapsuleRequest
from .email_batch_importer import ingest_email_thread_directory, scan_email_thread_files
from .email_remote_connector import MailPullConfig, pull_mail_threads_to_dir
from .history_importer import ingest_history_directory, scan_history_files
from .local_store import LocalKnowledgeStore
from .state_board import StateBoard
from .update_manager import check_and_prepare_update, is_http_not_found_error, is_network_error, open_path
from .user_settings import UserSettings, UserSettingsStore
from .version import APP_VERSION


class DesktopWindow:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = LocalKnowledgeStore(config.knowledge_file)
        self.capsule_builder = CapsuleBuilder(store=self.store)
        self.state_board = StateBoard(config.state_board_file)
        self.settings_store = UserSettingsStore(config.user_settings_file)
        self.settings = self.settings_store.load()

        self.bridge_process: subprocess.Popen | None = None
        self.dashboard_process: subprocess.Popen | None = None
        self.last_failed_files: list[Path] = []
        self.last_failed_email_files: list[Path] = []
        self.last_radar_summary: str = ""
        self.last_radar_query: str = ""
        self.did_initial_self_check = False
        self.open_dashboard_after_start = False
        self.last_action_customer_id: str = ""
        self.last_action_customer_name: str = ""
        self.last_action_task_id: str = ""

        self._build_ui()

    def _build_ui(self) -> None:
        self.root = tk.Tk()
        self.root.title("外贸助理桌面版")
        self.root.geometry("1180x860")
        self.root.minsize(980, 720)
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

        frame = ttk.Frame(self.root, padding=14)
        frame.pack(fill=tk.BOTH, expand=True)

        notice = ttk.Label(
            frame,
            text="只读权限声明：导入仅扫描你选择的文件夹，不会修改或删除原始工作文件。",
            foreground="#8b5a00",
            wraplength=1120,
            justify=tk.LEFT,
        )
        notice.pack(fill=tk.X, pady=(0, 8))

        self._build_service_section(frame)
        self._build_runtime_section(frame)
        self._build_radar_section(frame)
        self._build_output_section(frame)
        self._build_import_section(frame)
        self._build_guide_section(frame)
        self._build_feedback_section(frame)
        self._apply_beginner_mode()
        self.root.after(500, self.begin_work_session)
        self.root.after(1200, self._focus_primary_entry)
        self.root.after(1500, self.refresh_runtime_status)

    def _build_service_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="1) Start Work (Recommended)", padding=10)
        box.pack(fill=tk.X, pady=6)
        self.service_section_box = box
        row = ttk.Frame(box)
        row.pack(fill=tk.X)
        self.service_status = tk.StringVar(value="Not started")
        self.start_work_button = ttk.Button(row, text="Start Work", command=self.begin_work_session)
        self.start_work_button.pack(side=tk.LEFT)
        self.open_workbench_button = ttk.Button(row, text="Open Web Workbench", command=self.open_dashboard_workbench)
        self.open_workbench_button.pack(side=tk.LEFT, padx=8)
        self.beginner_mode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            row,
            text="Beginner Mode",
            variable=self.beginner_mode_var,
            command=self._apply_beginner_mode,
        ).pack(side=tk.LEFT, padx=8)
        self.show_advanced_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            row,
            text="Show Advanced",
            variable=self.show_advanced_var,
            command=self._toggle_service_advanced,
        ).pack(side=tk.LEFT, padx=8)
        ttk.Label(row, textvariable=self.service_status).pack(side=tk.LEFT, padx=12)

        self.quick_actions_frame = ttk.Frame(box)
        self.quick_actions_frame.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(self.quick_actions_frame, text="1) One-click Start", command=self.begin_work_session).pack(side=tk.LEFT)
        ttk.Button(self.quick_actions_frame, text="2) One-click Import", command=self._beginner_quick_import).pack(side=tk.LEFT, padx=8)
        ttk.Button(
            self.quick_actions_frame,
            text="3) Start Handling Tasks",
            command=lambda: self.open_dashboard_workbench(task_status="open"),
        ).pack(side=tk.LEFT, padx=8)
        self.update_button = ttk.Button(self.quick_actions_frame, text="One-click Update", command=self.one_click_update)
        self.update_button.pack(side=tk.LEFT, padx=8)

        self.service_advanced_frame = ttk.Frame(box)
        self.service_advanced_frame.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(self.service_advanced_frame, text="Start Services Only", command=self.start_services).pack(side=tk.LEFT)
        ttk.Button(self.service_advanced_frame, text="Open Edge Extensions", command=self.open_edge_extensions_page).pack(side=tk.LEFT, padx=8)
        ttk.Button(self.service_advanced_frame, text="Health Check", command=self.run_health_check).pack(side=tk.LEFT, padx=8)
        ttk.Button(self.service_advanced_frame, text="Export Diagnostics", command=self.export_diagnostics).pack(side=tk.LEFT, padx=8)
        ttk.Button(self.service_advanced_frame, text="Feedback Inbox", command=self.open_feedback_inbox).pack(side=tk.LEFT, padx=8)
        self.service_advanced_frame.pack_forget()

    def _build_runtime_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="2) System Status (Do operations in Web Workbench)", padding=10)
        box.pack(fill=tk.BOTH, pady=6)
        self.runtime_section_box = box

        top = ttk.Frame(box)
        top.pack(fill=tk.X, pady=(0, 6))
        self.sync_status_var = tk.StringVar(value="Last sync: none")
        ttk.Label(top, textvariable=self.sync_status_var).pack(side=tk.LEFT)
        ttk.Button(top, text="Open Web Workbench", command=self.open_dashboard_workbench).pack(side=tk.RIGHT)
        ttk.Button(top, text="Refresh", command=self.refresh_runtime_status).pack(side=tk.RIGHT, padx=(0, 8))

        metrics = ttk.Frame(box)
        metrics.pack(fill=tk.X, pady=(0, 8))
        self.metric_events = tk.StringVar(value="Events: 0")
        self.metric_focus = tk.StringVar(value="Focus tasks: 0")
        self.metric_alerts = tk.StringVar(value="Critical alerts: 0")
        ttk.Label(metrics, textvariable=self.metric_events).pack(side=tk.LEFT, padx=(0, 16))
        ttk.Label(metrics, textvariable=self.metric_focus).pack(side=tk.LEFT, padx=(0, 16))
        ttk.Label(metrics, textvariable=self.metric_alerts).pack(side=tk.LEFT)

        self.runtime_hint_var = tk.StringVar(
            value="Use desktop for startup/import/sync. Use web workbench for tasks/customers/events."
        )
        ttk.Label(
            box,
            textvariable=self.runtime_hint_var,
            foreground="#475569",
            wraplength=1080,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(2, 2))

        action_row = ttk.Frame(box)
        action_row.pack(fill=tk.X, pady=(8, 0))
        self.action_input_var = tk.StringVar(value="")
        ttk.Entry(action_row, textvariable=self.action_input_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(action_row, text="Execute Action Tag", command=self.execute_action_tag).pack(side=tk.LEFT, padx=8)

    def _build_radar_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="3) 雷达检索（客户 / 产品 / 成交与历史记录）", padding=10)
        box.pack(fill=tk.BOTH, pady=6)

        top = ttk.Frame(box)
        top.pack(fill=tk.X)
        self.radar_query_var = tk.StringVar(value="")
        ttk.Entry(top, textvariable=self.radar_query_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(top, text="检索", command=self.run_radar_search).pack(side=tk.LEFT, padx=8)
        ttk.Button(top, text="一键生成胶囊", command=self.generate_radar_capsule).pack(side=tk.LEFT, padx=8)

        tips = "支持模糊词和精准词：客户名/邮箱/电话/产品名/SKU/系列词"
        ttk.Label(box, text=tips, foreground="#444").pack(anchor=tk.W, pady=(6, 4))

        wrap = ttk.Frame(box)
        wrap.pack(fill=tk.BOTH, expand=True)
        self.radar_result = tk.Text(wrap, height=10, wrap=tk.WORD)
        self.radar_result.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=self.radar_result.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.radar_result.config(yscrollcommand=scroll.set)
        self.radar_result.insert(tk.END, "输入关键词后点击“检索”。\n")
        self.radar_result.configure(state=tk.DISABLED)

    def _build_output_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="4) 输出文件夹（可自定义）", padding=10)
        box.pack(fill=tk.X, pady=6)
        self.output_section_box = box
        row = ttk.Frame(box)
        row.pack(fill=tk.X)
        self.output_var = tk.StringVar(value=self.settings.output_dir or str(self.config.output_dir))
        ttk.Entry(row, textvariable=self.output_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="选择文件夹", command=self.choose_output_dir).pack(side=tk.LEFT, padx=8)
        ttk.Button(row, text="保存", command=self.save_output_dir).pack(side=tk.LEFT)

    def _build_import_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="5) 一键导入历史（支持多模型目录）", padding=10)
        box.pack(fill=tk.BOTH, expand=True, pady=6)
        self.import_section_box = box

        top = ttk.Frame(box)
        top.pack(fill=tk.X)
        self.import_dir_var = tk.StringVar(value="")
        ttk.Entry(top, textvariable=self.import_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(top, text="选择历史文件夹", command=self.choose_import_dir).pack(side=tk.LEFT, padx=8)

        helper = (
            "可重复导入：支持每天/每周多次导入。\n"
            "自动去重：已导入内容不会重复写入。\n"
            "推荐用法：首次全量导入，后续使用“导入新增资料”。"
        )
        ttk.Label(box, text=helper, justify=tk.LEFT, foreground="#444").pack(fill=tk.X, pady=(8, 6))

        actions = ttk.Frame(box)
        actions.pack(fill=tk.X, pady=8)
        self.import_button = ttk.Button(actions, text="首次全量导入", command=lambda: self.start_import(mode="full"))
        self.import_button.pack(side=tk.LEFT)
        self.incremental_button = ttk.Button(
            actions, text="导入新增资料（推荐）", command=lambda: self.start_import(mode="incremental")
        )
        self.incremental_button.pack(side=tk.LEFT, padx=8)
        self.retry_button = ttk.Button(actions, text="重试失败文件", command=self.retry_failed, state=tk.DISABLED)
        self.retry_button.pack(side=tk.LEFT, padx=8)

        email_actions = ttk.Frame(box)
        email_actions.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(email_actions, text="邮件线程：").pack(side=tk.LEFT)
        self.email_import_button = ttk.Button(email_actions, text="批量导入邮件线程", command=self.start_email_import)
        self.email_import_button.pack(side=tk.LEFT, padx=(8, 0))
        self.email_retry_button = ttk.Button(
            email_actions, text="重试失败邮件文件", command=self.retry_failed_email, state=tk.DISABLED
        )
        self.email_retry_button.pack(side=tk.LEFT, padx=8)

        connector = ttk.Frame(box)
        connector.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(connector, text="邮箱一键拉取：").pack(side=tk.LEFT)
        self.mail_provider_var = tk.StringVar(value=self.settings.mail_provider or "gmail")
        provider_box = ttk.Combobox(
            connector,
            width=8,
            textvariable=self.mail_provider_var,
            values=["gmail", "outlook"],
            state="readonly",
        )
        provider_box.pack(side=tk.LEFT, padx=(8, 6))
        self.mail_account_var = tk.StringVar(value=self.settings.mail_account or "")
        ttk.Entry(connector, textvariable=self.mail_account_var, width=24).pack(side=tk.LEFT, padx=(0, 6))
        self.mail_password_var = tk.StringVar(value=self.settings.mail_password if self.settings.remember_mail_password else "")
        ttk.Entry(connector, textvariable=self.mail_password_var, show="*", width=20).pack(side=tk.LEFT, padx=(0, 6))
        self.mail_days_var = tk.StringVar(value=str(self.settings.mail_days or 30))
        ttk.Entry(connector, textvariable=self.mail_days_var, width=6).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(connector, text="天").pack(side=tk.LEFT, padx=(0, 6))
        self.mail_limit_var = tk.StringVar(value=str(self.settings.mail_max_messages or 200))
        ttk.Entry(connector, textvariable=self.mail_limit_var, width=7).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(connector, text="封").pack(side=tk.LEFT, padx=(0, 6))
        self.remember_mail_password_var = tk.BooleanVar(value=self.settings.remember_mail_password)
        ttk.Checkbutton(connector, text="记住密码", variable=self.remember_mail_password_var).pack(side=tk.LEFT, padx=(0, 8))
        self.pull_mail_button = ttk.Button(connector, text="一键拉取并导入", command=self.start_mail_pull)
        self.pull_mail_button.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(box, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X)
        self.import_status = tk.StringVar(value="等待导入")
        ttk.Label(box, textvariable=self.import_status).pack(fill=tk.X, pady=(6, 4))

        result_wrap = ttk.Frame(box)
        result_wrap.pack(fill=tk.BOTH, expand=True)
        self.result_text = tk.Text(result_wrap, height=8, wrap=tk.WORD)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scroll = ttk.Scrollbar(result_wrap, orient=tk.VERTICAL, command=self.result_text.yview)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=result_scroll.set)
        self.result_text.insert(tk.END, "导入结果会显示在这里。\n")
        self.result_text.configure(state=tk.DISABLED)

    def _build_guide_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="6) 扩展安装向导", padding=10)
        box.pack(fill=tk.X, pady=6)
        self.guide_section_box = box
        guide = (
            "步骤 1：点击“打开 Chrome 扩展页”（chrome://extensions）。\n"
            "步骤 2：打开右上角“开发者模式”。\n"
            "步骤 3：点击“加载已解压扩展程序”，选择项目 extension 文件夹。\n"
            "步骤 4：打开豆包/DeepSeek/Gemini 网页，刷新后输入 @ 测试。"
        )
        ttk.Label(box, text=guide, justify=tk.LEFT).pack(fill=tk.X)
        btns = ttk.Frame(box)
        btns.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btns, text="打开 Chrome 扩展页", command=self.open_chrome_extensions_page).pack(side=tk.LEFT)
        ttk.Button(btns, text="打开 extension 文件夹", command=self.open_extension_folder).pack(side=tk.LEFT, padx=8)

    def _build_feedback_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="7) Feedback", padding=10)
        box.pack(fill=tk.X, pady=6)
        self.feedback_section_box = box
        row = ttk.Frame(box)
        row.pack(fill=tk.X)
        self.feedback_var = tk.StringVar(value="")
        ttk.Entry(row, textvariable=self.feedback_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="Submit Feedback", command=self.submit_feedback).pack(side=tk.LEFT, padx=8)
        ttk.Button(row, text="Open Inbox", command=self.open_feedback_inbox).pack(side=tk.LEFT)

    def choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="选择输出文件夹")
        if selected:
            self.output_var.set(selected)

    def save_output_dir(self) -> None:
        path = Path(self.output_var.get().strip()).expanduser().resolve()
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("保存失败", str(exc))
            return
        self.settings.output_dir = str(path)
        self.settings_store.save(self.settings)
        messagebox.showinfo("已保存", f"输出文件夹已保存：\n{path}")

    def choose_import_dir(self) -> None:
        selected = filedialog.askdirectory(title="选择历史文件夹（只读扫描）")
        if selected:
            self.import_dir_var.set(selected)

    def _set_import_buttons_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.import_button.configure(state=state)
        self.incremental_button.configure(state=state)
        self.email_import_button.configure(state=state)
        self.pull_mail_button.configure(state=state)
        if busy:
            self.retry_button.configure(state=tk.DISABLED)
            self.email_retry_button.configure(state=tk.DISABLED)
            return
        self.retry_button.configure(state=tk.NORMAL if self.last_failed_files else tk.DISABLED)
        self.email_retry_button.configure(state=tk.NORMAL if self.last_failed_email_files else tk.DISABLED)

    def _save_mail_settings(self, *, remember_password: bool, password: str) -> None:
        self.settings.mail_provider = (self.mail_provider_var.get().strip().lower() or "gmail")
        self.settings.mail_account = self.mail_account_var.get().strip()
        self.settings.mail_folder = "INBOX"
        try:
            self.settings.mail_days = max(1, min(int(self.mail_days_var.get().strip() or "30"), 3650))
        except ValueError:
            self.settings.mail_days = 30
        try:
            self.settings.mail_max_messages = max(1, min(int(self.mail_limit_var.get().strip() or "200"), 5000))
        except ValueError:
            self.settings.mail_max_messages = 200
        self.settings.remember_mail_password = remember_password
        self.settings.mail_password = password if remember_password else ""
        self.settings_store.save(self.settings)

    def _toggle_service_advanced(self) -> None:
        if bool(self.show_advanced_var.get()):
            self.service_advanced_frame.pack(fill=tk.X, pady=(8, 0))
        else:
            self.service_advanced_frame.pack_forget()
        self._apply_beginner_mode()

    def _set_section_visible(
        self,
        section: ttk.LabelFrame | ttk.Frame | None,
        *,
        visible: bool,
        fill: str,
        expand: bool = False,
        pady: int = 6,
    ) -> None:
        if section is None:
            return
        mapped = bool(section.winfo_manager())
        if visible and not mapped:
            section.pack(fill=fill, expand=expand, pady=pady)
        elif not visible and mapped:
            section.pack_forget()

    def _beginner_quick_import(self) -> None:
        if not self.import_dir_var.get().strip():
            self.choose_import_dir()
        if not self.import_dir_var.get().strip():
            return
        self.start_import(mode="incremental")

    def _apply_beginner_mode(self) -> None:
        beginner = bool(self.beginner_mode_var.get()) if hasattr(self, "beginner_mode_var") else False
        if hasattr(self, "quick_actions_frame"):
            self._set_section_visible(self.quick_actions_frame, visible=beginner, fill=tk.X, pady=8)
        if hasattr(self, "output_section_box"):
            self._set_section_visible(self.output_section_box, visible=not beginner, fill=tk.X, pady=6)
        if hasattr(self, "guide_section_box"):
            self._set_section_visible(self.guide_section_box, visible=not beginner, fill=tk.X, pady=6)
        if hasattr(self, "feedback_section_box"):
            self._set_section_visible(self.feedback_section_box, visible=not beginner, fill=tk.X, pady=6)
        if hasattr(self, "import_section_box"):
            self._set_section_visible(self.import_section_box, visible=not beginner, fill=tk.BOTH, expand=True, pady=6)
        if beginner:
            self.service_advanced_frame.pack_forget()

    def _focus_primary_entry(self) -> None:
        try:
            self.open_workbench_button.focus_set()
        except tk.TclError:
            return

    def begin_work_session(self) -> None:
        self.open_dashboard_after_start = True
        self.start_services()

    def open_dashboard_workbench(
        self,
        *,
        tour: bool = True,
        task_status: str = "",
        customer_id: str = "",
        customer_name: str = "",
        task_id: str = "",
    ) -> None:
        query = {"from": "desktop"}
        if tour:
            query["tour"] = "1"
        if task_status:
            query["task_status"] = task_status
        if customer_id:
            query["customer_id"] = customer_id
        if customer_name:
            query["customer_name"] = customer_name
        if task_id:
            query["task_id"] = task_id
        if not self._ensure_services_ready(require_dashboard=True):
            messagebox.showerror("Service", "Dashboard service unavailable. Please retry.")
            return
        webbrowser.open(f"http://127.0.0.1:8787/?{urlencode(query)}")

    def open_feedback_inbox(self) -> None:
        if not self._ensure_services_ready(require_dashboard=False):
            messagebox.showerror("Feedback", "Bridge service unavailable.")
            return
        webbrowser.open("http://127.0.0.1:8765/feedback/inbox")

    def start_services(self) -> None:
        self.service_status.set("启动中...")

        def worker() -> None:
            self._start_service_processes()
            bridge_ok = self._wait_health("http://127.0.0.1:8765/health", timeout_sec=12)
            dashboard_ok = self._wait_health("http://127.0.0.1:8787/", timeout_sec=12)
            if bridge_ok and dashboard_ok:
                msg = "已启动（Bridge + Dashboard）"
            elif bridge_ok:
                msg = "Bridge 已启动，Dashboard 未就绪"
            else:
                msg = "启动失败，请重试"
            self.root.after(0, lambda: self.service_status.set(msg))
            if bridge_ok and not self.did_initial_self_check:
                self.root.after(0, self.run_health_check_silent)
            if bridge_ok and dashboard_ok and self.open_dashboard_after_start:
                self.root.after(0, self.open_dashboard_workbench)
                self.open_dashboard_after_start = False
            self.root.after(0, self.refresh_runtime_status)

        threading.Thread(target=worker, daemon=True).start()

    def _start_service_processes(self) -> None:
        kwargs: dict = {"cwd": str(self.config.root_dir)}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        self._terminate_port_processes((8765, 8787))
        if self.bridge_process and self.bridge_process.poll() is None:
            self.bridge_process.terminate()
        if self.dashboard_process and self.dashboard_process.poll() is None:
            self.dashboard_process.terminate()
        self.bridge_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "app.main",
                "serve-bridge",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
                "--allow-action-execute",
            ],
            **kwargs,
        )
        self.dashboard_process = subprocess.Popen(
            [sys.executable, "-m", "app.main", "serve-dashboard", "--host", "127.0.0.1", "--port", "8787"],
            **kwargs,
        )

    def _terminate_port_processes(self, ports: tuple[int, ...]) -> None:
        pids: set[int] = set()
        if os.name == "nt":
            try:
                proc = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=5,
                    check=False,
                )
                for line in proc.stdout.splitlines():
                    if "LISTENING" not in line:
                        continue
                    text = line.strip()
                    for port in ports:
                        if f":{port}" not in text:
                            continue
                        parts = text.split()
                        if not parts:
                            continue
                        try:
                            pid = int(parts[-1])
                        except ValueError:
                            continue
                        if pid > 0:
                            pids.add(pid)
            except (OSError, subprocess.SubprocessError):
                return
            for pid in pids:
                try:
                    subprocess.run(
                        ["taskkill", "/PID", str(pid), "/F"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False,
                    )
                except (OSError, subprocess.SubprocessError):
                    continue
            return

        for port in ports:
            try:
                proc = subprocess.run(
                    ["lsof", "-ti", f"tcp:{port}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError):
                continue
            for line in proc.stdout.splitlines():
                try:
                    pid = int(line.strip())
                except ValueError:
                    continue
                if pid > 0:
                    pids.add(pid)
        for pid in pids:
            try:
                os.kill(pid, 9)
            except OSError:
                continue

    def _wait_health(self, url: str, timeout_sec: int = 10) -> bool:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            try:
                with urlopen(url, timeout=1) as resp:  # noqa: S310
                    if resp.status == 200:
                        return True
            except (URLError, OSError):
                time.sleep(0.4)
        return False

    def _is_bridge_ready(self) -> bool:
        return self._wait_health("http://127.0.0.1:8765/health", timeout_sec=0.8)

    def _is_dashboard_ready(self) -> bool:
        return self._wait_health("http://127.0.0.1:8787/", timeout_sec=0.8)

    def _ensure_services_ready(self, *, require_dashboard: bool, timeout_sec: float = 12.0) -> bool:
        bridge_ok = self._is_bridge_ready()
        dashboard_ok = self._is_dashboard_ready() if require_dashboard else True
        if bridge_ok and dashboard_ok:
            return True
        self.open_dashboard_after_start = False
        self.start_services()
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            bridge_ok = self._is_bridge_ready()
            dashboard_ok = self._is_dashboard_ready() if require_dashboard else True
            if bridge_ok and dashboard_ok:
                return True
            time.sleep(0.2)
        return False

    def one_click_update(self) -> None:
        if hasattr(self, "update_button"):
            self.update_button.configure(state=tk.DISABLED)
        previous_status = self.service_status.get()
        self.service_status.set("Checking updates...")

        def worker() -> None:
            try:
                info, launcher, prepared_path = check_and_prepare_update(
                    current_version=APP_VERSION,
                    updates_root=self.config.data_dir / "updates",
                )
            except Exception as exc:
                err = exc

                def fail() -> None:
                    if hasattr(self, "update_button"):
                        self.update_button.configure(state=tk.NORMAL)
                    self.service_status.set(previous_status)
                    if is_http_not_found_error(err):
                        msg = "Update source not found (404). Verify release publishing first."
                    elif is_network_error(err):
                        msg = "Network error. Unable to check updates."
                    else:
                        msg = "Update failed."
                    messagebox.showerror("One-click Update", f"{msg}\n{err}")

                self.root.after(0, fail)
                return

            def done() -> None:
                if hasattr(self, "update_button"):
                    self.update_button.configure(state=tk.NORMAL)
                self.service_status.set(previous_status)
                if not info.has_update:
                    messagebox.showinfo("One-click Update", "Already the latest version.")
                    return
                prompt = (
                    f"New version found: {info.latest_version}\n"
                    f"Source: {info.source_repo}\n"
                    "Open the new launcher now?"
                )
                if launcher and messagebox.askyesno("One-click Update", prompt):
                    open_path(launcher)
                    return
                messagebox.showinfo("One-click Update", f"Update package prepared:\n{prepared_path}")

            self.root.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _post_json(self, url: str, payload: dict) -> dict:
        req = Request(
            url=url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=3) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))

    def execute_action_tag(self) -> None:
        action_text = self.action_input_var.get().strip() if hasattr(self, "action_input_var") else ""
        if not action_text:
            messagebox.showinfo("Action", "Please paste one <action> tag first.")
            return
        if "<action>" not in action_text or "</action>" not in action_text:
            messagebox.showwarning("Action", "Input must contain one complete <action>...</action> tag.")
            return
        if not self._ensure_services_ready(require_dashboard=False):
            messagebox.showerror("Action", "Bridge service unavailable.")
            return
        try:
            payload = self._post_json("http://127.0.0.1:8765/actions/execute", {"model_output": action_text})
        except (OSError, URLError, ValueError):
            messagebox.showerror("Action", "Bridge service unavailable.")
            return
        results = payload.get("results", []) if isinstance(payload.get("results", []), list) else []
        if not results:
            messagebox.showwarning("Action", "No action was executed.")
            return

        first = results[0] if isinstance(results[0], dict) else {}
        context = first.get("context", {}) if isinstance(first.get("context", {}), dict) else {}
        self.last_action_customer_id = str(context.get("customer_id", "")).strip()
        self.last_action_customer_name = str(context.get("customer_name", "")).strip()
        self.last_action_task_id = str(context.get("task_id", "")).strip()

        event = payload.get("state_event", {}) if isinstance(payload.get("state_event", {}), dict) else {}
        event_id = str(event.get("event_id", "")).strip()
        lines = [
            f"[Action executed] {datetime.now(UTC).isoformat()}",
            f"event_id={event_id}" if event_id else "event_id=<none>",
        ]
        for item in results:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status", "")).strip() or "unknown"
            message = str(item.get("message", "")).strip()
            lines.append(f"- {status}: {message}")
        self._append_result("\n" + "\n".join(lines) + "\n")
        self.action_input_var.set("")

        self.open_dashboard_workbench(
            tour=False,
            task_status="open",
            customer_id=self.last_action_customer_id,
            customer_name=self.last_action_customer_name,
            task_id=self.last_action_task_id,
        )
        self.refresh_runtime_status()

    def run_health_check(self) -> None:
        if not self._ensure_services_ready(require_dashboard=False):
            messagebox.showerror("Health Check", "Bridge service unavailable.")
            return
        try:
            data = self._post_json("http://127.0.0.1:8765/health/check", {})
        except (OSError, URLError, ValueError):
            messagebox.showerror("Health Check", "Bridge service unavailable.")
            return
        checks = data.get("checks", []) if isinstance(data.get("checks", []), list) else []
        failed = [c for c in checks if isinstance(c, dict) and c.get("status") != "ok"]
        if failed:
            lines = [f"{c.get('label')}: {c.get('detail') or c.get('status')}" for c in failed]
            messagebox.showwarning("Health Check", "Found issues:\n" + "\n".join(lines))
            return
        messagebox.showinfo("Health Check", "All checks passed.")

    def run_health_check_silent(self) -> None:
        self.did_initial_self_check = True
        try:
            data = self._post_json("http://127.0.0.1:8765/health/check", {})
        except (OSError, URLError, ValueError):
            return
        checks = data.get("checks", []) if isinstance(data.get("checks", []), list) else []
        failed = [c for c in checks if isinstance(c, dict) and c.get("status") != "ok"]
        if failed:
            self.service_status.set("Started with warnings (click Health Check)")

    def export_diagnostics(self) -> None:
        if not self._ensure_services_ready(require_dashboard=False):
            messagebox.showerror("Diagnostics", "Bridge service unavailable.")
            return
        try:
            data = self._post_json("http://127.0.0.1:8765/diagnostics/export", {})
        except (OSError, URLError, ValueError):
            messagebox.showerror("Diagnostics", "Bridge service unavailable.")
            return
        path = str(data.get("path", "")).strip()
        if not path:
            messagebox.showwarning("Diagnostics", "No diagnostics output path returned.")
            return
        messagebox.showinfo("Diagnostics", f"Diagnostics exported:\n{path}")

    def submit_feedback(self) -> None:
        text = self.feedback_var.get().strip() if hasattr(self, "feedback_var") else ""
        if not text:
            messagebox.showinfo("Feedback", "Please enter feedback first.")
            return
        if not self._ensure_services_ready(require_dashboard=False):
            messagebox.showerror("Feedback", "Bridge service unavailable.")
            return
        try:
            self._post_json("http://127.0.0.1:8765/feedback/add", {"source": "desktop", "text": text})
        except (OSError, URLError, ValueError):
            messagebox.showerror("Feedback", "Bridge service unavailable.")
            return
        self.feedback_var.set("")
        messagebox.showinfo("Feedback", "Feedback submitted.")

    def _event_action_label(self, action_name: str) -> str:
        mapping = {
            "generate_quote_draft": "已生成报价草稿",
            "generate_followup_draft": "已生成跟进草稿",
            "ingest_email_thread": "已导入邮件线程",
            "conversation_sync": "已同步对话记忆",
        }
        return mapping.get(action_name, action_name or "未知动作")

    def _extract_customer_from_event(self, event: dict) -> str:
        results = event.get("results", [])
        if not isinstance(results, list):
            return ""
        for item in results:
            if not isinstance(item, dict):
                continue
            context = item.get("context", {})
            if isinstance(context, dict):
                customer_name = str(context.get("customer_name", "")).strip()
                if customer_name:
                    return customer_name
            message = str(item.get("message", "")).strip()
            if message:
                match = re.search(r"for\s+(.+?)(?:[.;]|$)", message, flags=re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        return ""

    def _extract_product_from_event(self, event: dict) -> str:
        results = event.get("results", [])
        if not isinstance(results, list):
            return ""
        for item in results:
            if not isinstance(item, dict):
                continue
            context = item.get("context", {})
            if isinstance(context, dict):
                product = str(context.get("product", "")).strip()
                if product:
                    return product
            message = str(item.get("message", "")).strip()
            if message:
                match = re.search(r"product[:\s]+([A-Za-z0-9_.-]+)", message, flags=re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            artifacts = item.get("artifacts", [])
            if isinstance(artifacts, list):
                for art in artifacts:
                    product = self._extract_product_from_artifact(str(art))
                    if product:
                        return product
        return ""

    def _extract_product_from_artifact(self, artifact_path: str) -> str:
        path = Path(artifact_path.strip())
        if not path.exists() or not path.is_file():
            return ""
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""
        for line in text.splitlines():
            if line.lower().startswith("- product:"):
                return line.split(":", 1)[1].strip()
        return ""

    def refresh_runtime_status(self) -> None:
        try:
            events_data = self._post_json("http://127.0.0.1:8765/state/latest", {"limit": 10})
            focus_data = self._post_json("http://127.0.0.1:8765/state/focus", {"limit": 10})
            alerts_data = self._post_json("http://127.0.0.1:8765/state/alerts", {"limit": 10})
        except (OSError, URLError, ValueError):
            self.sync_status_var.set("Last sync: unavailable (service disconnected)")
            self.metric_events.set("Events: 0")
            self.metric_focus.set("Focus tasks: 0")
            self.metric_alerts.set("Critical alerts: 0")
            self.runtime_hint_var.set("Service unavailable. Click 'Start Work' to recover.")
            self.root.after(5000, self.refresh_runtime_status)
            return

        events = list(reversed(events_data.get("events", [])))
        rows = focus_data.get("rows", [])
        alerts = alerts_data.get("rows", [])
        self.metric_events.set(f"Events: {len(events)}")
        self.metric_focus.set(f"Focus tasks: {len(rows)}")
        self.metric_alerts.set(f"Critical alerts: {len(alerts)}")

        latest_sync = next((e for e in events if str(e.get("action_name", "")) == "conversation_sync"), None)
        self.sync_status_var.set(
            f"Last sync: {latest_sync.get('created_at_utc', '')}" if latest_sync else "Last sync: none"
        )
        self.runtime_hint_var.set(
            "Desktop handles startup/import/sync. Continue operations in Web Workbench (tasks/customers/events)."
        )
        self.root.after(5000, self.refresh_runtime_status)

    def _collect_radar_data(self, query: str) -> dict:
        kb = self.store.load()
        ql = query.lower()

        customer_hits = []
        for c in kb.customers.values():
            hay = " ".join([c.customer_id, c.name, c.region, " ".join(c.notes), " ".join(c.tags)]).lower()
            if ql in hay:
                customer_hits.append(c)

        product_hits = []
        for p in kb.products.values():
            hay = " ".join([p.sku, p.name]).lower()
            if ql in hay:
                product_hits.append(p)

        doc_hits = [x for x in kb.doc_facts if ql in str(x).lower()][:12]

        events = self.state_board.latest(limit=200)
        event_hits = []
        for e in events:
            text_parts = [str(e.get("action_name", ""))]
            customer = self._extract_customer_from_event(e)
            if customer:
                text_parts.append(customer)
            product = self._extract_product_from_event(e)
            if product:
                text_parts.append(product)
            for r in (e.get("results", []) if isinstance(e.get("results", []), list) else []):
                if isinstance(r, dict):
                    text_parts.append(str(r.get("message", "")))
                    for a in (r.get("artifacts", []) if isinstance(r.get("artifacts", []), list) else []):
                        text_parts.append(str(a))
            if ql in " ".join(text_parts).lower():
                event_hits.append(e)
            if len(event_hits) >= 40:
                break

        return {
            "customer_hits": customer_hits,
            "product_hits": product_hits,
            "doc_hits": doc_hits,
            "event_hits": event_hits,
        }

    def _build_radar_output(self, query: str, data: dict) -> tuple[str, str]:
        customer_hits = data["customer_hits"]
        product_hits = data["product_hits"]
        doc_hits = data["doc_hits"]
        event_hits = data["event_hits"]

        customer_stats: dict[str, dict] = defaultdict(
            lambda: {"quotes": 0, "followups": 0, "syncs": 0, "last_time": "", "products": set()}
        )
        cross_stats: dict[tuple[str, str], dict] = defaultdict(
            lambda: {"quotes": 0, "followups": 0, "last_time": ""}
        )
        event_lines: list[str] = []

        for e in event_hits:
            action = str(e.get("action_name", ""))
            action_label = self._event_action_label(action)
            created_at = str(e.get("created_at_utc", ""))
            customer = self._extract_customer_from_event(e) or "未知客户"
            product = self._extract_product_from_event(e)

            if action == "generate_quote_draft":
                customer_stats[customer]["quotes"] += 1
            elif action == "generate_followup_draft":
                customer_stats[customer]["followups"] += 1
            elif action == "conversation_sync":
                customer_stats[customer]["syncs"] += 1

            if created_at > customer_stats[customer]["last_time"]:
                customer_stats[customer]["last_time"] = created_at
            if product:
                customer_stats[customer]["products"].add(product)
                key = (customer, product)
                if action == "generate_quote_draft":
                    cross_stats[key]["quotes"] += 1
                elif action == "generate_followup_draft":
                    cross_stats[key]["followups"] += 1
                if created_at > cross_stats[key]["last_time"]:
                    cross_stats[key]["last_time"] = created_at

            event_lines.append(
                f"- {created_at} | {action_label}"
                + (f"（客户: {customer}，产品: {product}）" if product else f"（客户: {customer}）")
            )

        ranked = sorted(
            customer_stats.items(),
            key=lambda item: (item[1]["quotes"], item[1]["followups"], item[1]["last_time"]),
            reverse=True,
        )

        view_lines: list[str] = [
            f"检索词: {query}",
            "",
            f"客户命中: {len(customer_hits)}",
        ]
        for c in customer_hits[:6]:
            view_lines.append(f"- {c.name} ({c.customer_id}) | 地区: {c.region or '-'} | 币种: {c.currency}")
        view_lines.extend(["", f"产品命中: {len(product_hits)}"])
        for p in product_hits[:6]:
            view_lines.append(f"- {p.sku} | {p.name}")
        view_lines.extend(["", f"历史记忆命中: {len(doc_hits)}"])
        for d in doc_hits[:8]:
            view_lines.append(f"- {d}")
        view_lines.extend(["", f"成交/动作记录命中: {len(event_hits)}"])

        if ranked:
            view_lines.append("客户聚合摘要:")
            for customer, stats in ranked[:8]:
                products = list(stats["products"])[:3]
                product_text = f"，相关产品: {', '.join(products)}" if products else ""
                view_lines.append(
                    f"- {customer} | 报价 {stats['quotes']} 次 | 跟进 {stats['followups']} 次 | 最近 {stats['last_time']}{product_text}"
                )
        cross_ranked = sorted(
            cross_stats.items(),
            key=lambda item: (item[1]["quotes"], item[1]["followups"], item[1]["last_time"]),
            reverse=True,
        )
        if cross_ranked:
            view_lines.append("成交档案视图（客户 × 产品）:")
            for (customer, product), stats in cross_ranked[:12]:
                view_lines.append(
                    f"- {customer} × {product} | 报价 {stats['quotes']} 次 | 跟进 {stats['followups']} 次 | 最近 {stats['last_time']}"
                )
        if event_lines:
            view_lines.append("最近语义事件:")
            view_lines.extend(event_lines[:8])
        if not customer_hits and not product_hits and not doc_hits and not event_hits:
            view_lines.append("- 无命中，请更换关键词或先导入更多历史资料。")

        capsule_lines = [f"雷达检索词: {query}", "雷达摘要:"]
        for customer, stats in ranked[:6]:
            capsule_lines.append(
                f"- 客户 {customer}: 报价{stats['quotes']}次, 跟进{stats['followups']}次, 最近记录 {stats['last_time']}"
            )
        for (customer, product), stats in cross_ranked[:8]:
            capsule_lines.append(
                f"- 成交档案 {customer} × {product}: 报价{stats['quotes']}次, 跟进{stats['followups']}次, 最近 {stats['last_time']}"
            )
        for d in doc_hits[:6]:
            capsule_lines.append(f"- 历史事实: {d}")
        capsule_lines.extend(event_lines[:6])

        return "\n".join(view_lines), "\n".join(capsule_lines)

    def run_radar_search(self) -> None:
        query = self.radar_query_var.get().strip()
        if not query:
            messagebox.showinfo("提示", "请输入关键词。")
            return

        data = self._collect_radar_data(query)
        view_text, summary_text = self._build_radar_output(query, data)
        self.last_radar_query = query
        self.last_radar_summary = summary_text

        self.radar_result.configure(state=tk.NORMAL)
        self.radar_result.delete("1.0", tk.END)
        self.radar_result.insert(tk.END, view_text)
        self.radar_result.configure(state=tk.DISABLED)

    def generate_radar_capsule(self) -> None:
        query = self.radar_query_var.get().strip()
        if not query:
            messagebox.showinfo("提示", "请先输入检索词。")
            return

        data = self._collect_radar_data(query)
        view_text, summary_text = self._build_radar_output(query, data)
        self.last_radar_query = query
        self.last_radar_summary = summary_text

        capsule = self.capsule_builder.build(
            CapsuleRequest(
                user_input=f"{query}\n\n{summary_text}",
                model_name="web-llm",
                template_lang="zh",
                template_mode="standard",
            )
        )
        text = capsule.injected_prompt

        self.radar_result.configure(state=tk.NORMAL)
        self.radar_result.delete("1.0", tk.END)
        self.radar_result.insert(tk.END, view_text)
        self.radar_result.insert(tk.END, "\n\n--- 生成胶囊 ---\n")
        self.radar_result.insert(tk.END, text + "\n")
        self.radar_result.configure(state=tk.DISABLED)
        self.radar_result.see(tk.END)

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("已生成", "胶囊已复制到剪贴板，可直接粘贴到大模型输入框。")
        except tk.TclError:
            messagebox.showinfo("已生成", "胶囊已生成，请在结果区复制。")

    def start_import(self, mode: str = "full") -> None:
        source = self.import_dir_var.get().strip()
        if not source:
            messagebox.showwarning("提示", "请先选择历史文件夹。")
            return
        root_dir = Path(source).expanduser().resolve()
        if not root_dir.exists() or not root_dir.is_dir():
            messagebox.showerror("错误", "历史文件夹不存在。")
            return

        self._set_import_buttons_busy(True)
        self.progress.configure(value=0, maximum=1)
        if mode == "incremental":
            self.import_status.set("正在导入新增资料...")
            self._append_result(f"\n开始增量导入：{root_dir}\n")
            max_files = 600
        else:
            self.import_status.set("正在全量扫描...")
            self._append_result(f"\n开始全量导入：{root_dir}\n")
            max_files = 1500

        def worker() -> None:
            files = scan_history_files(root_dir, recursive=True, max_files=max_files)
            total = max(1, len(files))
            self.root.after(0, lambda: self.progress.configure(value=0, maximum=total))

            def on_progress(event: dict) -> None:
                self.root.after(
                    0,
                    lambda: (
                        self.progress.configure(value=event.get("current", 0)),
                        self.import_status.set(
                            f"处理中 {event.get('current', 0)}/{event.get('total', 0)} | 成功文件 {event.get('imported_files', 0)} | 记忆 {event.get('facts', 0)} | 失败 {event.get('failed_files', 0)}"
                        ),
                    ),
                )

            stats = ingest_history_directory(
                store=self.store,
                directory=root_dir,
                recursive=True,
                max_files=max_files,
                max_lines_per_file=80,
                progress_callback=on_progress,
                source_files=files,
            )
            self.last_failed_files = [Path(p) for p in (stats.failed_files or []) if p]
            self.root.after(0, lambda: self._finish_import(stats.to_dict(), mode=mode))

        threading.Thread(target=worker, daemon=True).start()

    def retry_failed(self) -> None:
        if not self.last_failed_files:
            messagebox.showinfo("提示", "当前没有失败文件可重试。")
            return

        self._set_import_buttons_busy(True)

        total = max(1, len(self.last_failed_files))
        self.progress.configure(value=0, maximum=total)
        self.import_status.set("正在重试失败文件...")

        def worker() -> None:
            def on_progress(event: dict) -> None:
                self.root.after(0, lambda: self.progress.configure(value=event.get("current", 0)))

            stats = ingest_history_directory(
                store=self.store,
                directory=Path(self.import_dir_var.get().strip() or "."),
                recursive=False,
                max_files=total,
                max_lines_per_file=80,
                progress_callback=on_progress,
                source_files=self.last_failed_files,
            )
            self.last_failed_files = [Path(p) for p in (stats.failed_files or []) if p]
            self.root.after(0, lambda: self._finish_import(stats.to_dict(), retry=True))

        threading.Thread(target=worker, daemon=True).start()

    def start_email_import(self) -> None:
        source = self.import_dir_var.get().strip()
        if not source:
            messagebox.showwarning("提示", "请先选择邮件文件夹。")
            return
        root_dir = Path(source).expanduser().resolve()
        if not root_dir.exists() or not root_dir.is_dir():
            messagebox.showerror("错误", "邮件文件夹不存在。")
            return

        self._set_import_buttons_busy(True)
        self.progress.configure(value=0, maximum=1)
        self.import_status.set("正在批量导入邮件线程...")
        self._append_result(f"\n开始邮件批量导入：{root_dir}\n")

        def worker() -> None:
            files = scan_email_thread_files(root_dir, recursive=True, max_files=1200)
            total = max(1, len(files))
            self.root.after(0, lambda: self.progress.configure(value=0, maximum=total))

            def on_progress(event: dict) -> None:
                self.root.after(
                    0,
                    lambda: (
                        self.progress.configure(value=event.get("current", 0)),
                        self.import_status.set(
                            f"邮件导入 {event.get('current', 0)}/{event.get('total', 0)} | 成功 {event.get('imported_files', 0)} | 记忆 {event.get('facts', 0)} | 失败 {event.get('failed_files', 0)}"
                        ),
                    ),
                )

            stats = ingest_email_thread_directory(
                store=self.store,
                state_board=self.state_board,
                directory=root_dir,
                recursive=True,
                max_files=1200,
                progress_callback=on_progress,
                source_files=files,
            )
            self.last_failed_email_files = [Path(p) for p in (stats.failed_files or []) if p]
            self.root.after(0, lambda: self._finish_email_import(stats.to_dict(), retry=False))

        threading.Thread(target=worker, daemon=True).start()

    def retry_failed_email(self) -> None:
        if not self.last_failed_email_files:
            messagebox.showinfo("提示", "当前没有失败邮件文件可重试。")
            return

        self._set_import_buttons_busy(True)
        total = max(1, len(self.last_failed_email_files))
        self.progress.configure(value=0, maximum=total)
        self.import_status.set("正在重试失败邮件文件...")

        def worker() -> None:
            def on_progress(event: dict) -> None:
                self.root.after(0, lambda: self.progress.configure(value=event.get("current", 0)))

            stats = ingest_email_thread_directory(
                store=self.store,
                state_board=self.state_board,
                directory=Path(self.import_dir_var.get().strip() or "."),
                recursive=False,
                max_files=total,
                progress_callback=on_progress,
                source_files=self.last_failed_email_files,
            )
            self.last_failed_email_files = [Path(p) for p in (stats.failed_files or []) if p]
            self.root.after(0, lambda: self._finish_email_import(stats.to_dict(), retry=True))

        threading.Thread(target=worker, daemon=True).start()

    def start_mail_pull(self) -> None:
        provider = (self.mail_provider_var.get().strip().lower() or "gmail")
        account = self.mail_account_var.get().strip()
        password = self.mail_password_var.get().strip()
        if not account:
            messagebox.showwarning("提示", "请先输入邮箱账号。")
            return
        if not password:
            messagebox.showwarning("提示", "请先输入邮箱密码（建议应用专用密码）。")
            return
        try:
            days = max(1, min(int(self.mail_days_var.get().strip() or "30"), 3650))
            max_messages = max(1, min(int(self.mail_limit_var.get().strip() or "200"), 5000))
        except ValueError:
            messagebox.showwarning("提示", "拉取天数和封数需为数字。")
            return

        remember_password = bool(self.remember_mail_password_var.get())
        self._save_mail_settings(remember_password=remember_password, password=password)
        self._set_import_buttons_busy(True)
        self.progress.configure(value=0, maximum=1)
        self.import_status.set("正在拉取邮箱邮件并导入...")
        self._append_result(f"\n开始邮箱拉取：provider={provider}, account={account}, days={days}, max={max_messages}\n")

        def worker() -> None:
            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            pull_dir = self.config.data_dir / "mail_sync" / f"{provider}_{ts}"

            def on_pull_progress(event: dict) -> None:
                self.root.after(
                    0,
                    lambda: (
                        self.progress.configure(value=event.get("current", 0), maximum=max(1, event.get("total", 1))),
                        self.import_status.set(
                            f"邮箱拉取 {event.get('current', 0)}/{event.get('total', 0)} | 成功 {event.get('pulled_messages', 0)} | 失败 {event.get('failed_messages', 0)}"
                        ),
                    ),
                )

            try:
                pull_stats = pull_mail_threads_to_dir(
                    config=MailPullConfig(
                        provider=provider,
                        account=account,
                        password=password,
                        folder=self.settings.mail_folder or "INBOX",
                        days=days,
                        max_messages=max_messages,
                    ),
                    output_dir=pull_dir,
                    progress_callback=on_pull_progress,
                )
                pulled_files = [Path(p) for p in pull_stats.exported_files]
                ingest_stats = ingest_email_thread_directory(
                    store=self.store,
                    state_board=self.state_board,
                    directory=pull_dir,
                    recursive=False,
                    max_files=max_messages,
                    source_files=pulled_files,
                )
                self.last_failed_email_files = [Path(p) for p in (ingest_stats.failed_files or []) if p]
                self.root.after(0, lambda: self._finish_mail_pull(pull_stats.to_dict(), ingest_stats.to_dict()))
            except Exception as exc:  # pragma: no cover
                self.root.after(0, lambda: self._finish_mail_pull({"error": str(exc)}, {}))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_import(self, result: dict, retry: bool = False, mode: str = "full") -> None:
        self._set_import_buttons_busy(False)

        tag = "重试完成" if retry else "导入完成"
        self.import_status.set(
            f"{tag}：扫描 {result.get('scanned_files', 0)}，成功 {result.get('imported_files', 0)}，新增记忆 {result.get('extracted_facts', 0)}，重复跳过 {result.get('duplicate_skipped', 0)}，失败 {len(result.get('failed_files', []))}"
        )
        if not retry:
            messagebox.showinfo(
                "导入完成",
                (
                    f"本次扫描 {result.get('scanned_files', 0)} 个文件\n"
                    f"新增记忆 {result.get('extracted_facts', 0)} 条\n"
                    f"重复跳过 {result.get('duplicate_skipped', 0)} 条（自动去重）\n"
                    f"失败文件 {len(result.get('failed_files', []))} 个"
                ),
            )
        self._append_result(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    def _finish_email_import(self, result: dict, retry: bool = False) -> None:
        self._set_import_buttons_busy(False)
        tag = "邮件重试完成" if retry else "邮件导入完成"
        self.import_status.set(
            f"{tag}：扫描 {result.get('scanned_files', 0)}，成功 {result.get('imported_files', 0)}，跳过 {result.get('skipped_files', 0)}，新增记忆 {result.get('extracted_facts', 0)}，重复跳过 {result.get('duplicate_skipped', 0)}，失败 {len(result.get('failed_files', []))}"
        )
        if not retry:
            messagebox.showinfo(
                "邮件导入完成",
                (
                    f"本次扫描 {result.get('scanned_files', 0)} 个邮件文件\n"
                    f"成功导入 {result.get('imported_files', 0)} 个\n"
                    f"新增记忆 {result.get('extracted_facts', 0)} 条\n"
                    f"重复跳过 {result.get('duplicate_skipped', 0)} 条\n"
                    f"失败文件 {len(result.get('failed_files', []))} 个"
                ),
            )
        self._append_result(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    def _finish_mail_pull(self, pull_result: dict, ingest_result: dict) -> None:
        self._set_import_buttons_busy(False)
        if pull_result.get("error"):
            self.import_status.set(f"邮箱拉取失败：{pull_result.get('error')}")
            messagebox.showerror("拉取失败", str(pull_result.get("error")))
            return
        self.import_status.set(
            f"邮箱拉取完成：拉取 {pull_result.get('pulled_messages', 0)} 封，导入 {ingest_result.get('imported_files', 0)} 封，失败 {len(ingest_result.get('failed_files', []))}"
        )
        messagebox.showinfo(
            "拉取并导入完成",
            (
                f"拉取邮件 {pull_result.get('pulled_messages', 0)} 封\n"
                f"导入成功 {ingest_result.get('imported_files', 0)} 封\n"
                f"新增记忆 {ingest_result.get('extracted_facts', 0)} 条\n"
                f"失败文件 {len(ingest_result.get('failed_files', []))} 个"
            ),
        )
        self._append_result(
            json.dumps({"pull": pull_result, "ingest": ingest_result}, ensure_ascii=False, indent=2) + "\n"
        )

    def _append_result(self, text: str) -> None:
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)
        self.result_text.configure(state=tk.DISABLED)

    def open_extension_folder(self) -> None:
        path = self.config.root_dir / "extension"
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def open_chrome_extensions_page(self) -> None:
        url = "chrome://extensions/"
        try:
            if os.name == "nt":
                candidates = [
                    Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
                    Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
                ]
                for exe in candidates:
                    if exe.exists():
                        subprocess.Popen([str(exe), url])
                        return
                subprocess.Popen(["cmd", "/c", "start", "chrome", url], shell=False)
                return
            if sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Google Chrome", url])
                return
            subprocess.Popen(["google-chrome", url])
            return
        except OSError:
            pass

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
        except tk.TclError:
            pass
        messagebox.showinfo("提示", "无法自动打开 Chrome 扩展页。已复制地址到剪贴板：chrome://extensions/")

    def open_edge_extensions_page(self) -> None:
        url = "edge://extensions/"
        try:
            if os.name == "nt":
                candidates = [
                    Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft/Edge/Application/msedge.exe",
                    Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft/Edge/Application/msedge.exe",
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/Application/msedge.exe",
                ]
                for exe in candidates:
                    if exe.exists():
                        subprocess.Popen([str(exe), url])
                        return
                subprocess.Popen(["cmd", "/c", "start", "msedge", url], shell=False)
                return
            if sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Microsoft Edge", url])
                return
            subprocess.Popen(["microsoft-edge", url])
            return
        except OSError:
            pass

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
        except tk.TclError:
            pass
        messagebox.showinfo("提示", "无法自动打开 Edge 扩展页。已复制地址到剪贴板：edge://extensions/")

    def run(self) -> int:
        self.root.mainloop()
        return 0


def run_desktop_window(config: AppConfig) -> int:
    app = DesktopWindow(config)
    return app.run()
