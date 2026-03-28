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

from .api_chat import (
    ApiChatError,
    ApiChatSettings,
    build_local_context,
    default_api_url,
    default_model,
    send_chat_request,
)
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

# 中文 | 邮箱一键拉取 | 批量导入邮件线程

# 中文 | 邮箱一键拉取 | 批量导入邮件线程


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
        self.selected_import_files: list[Path] = []
        self.ui_lang: str = "zh"
        self.keep_alive_enabled = True
        self.api_basis_default_zh = "尚未使用本地上下文。"
        self.api_basis_default_en = "No local context used yet."
        self.radar_placeholder_zh = "输入关键词后点击检索。\n"
        self.radar_placeholder_en = "Enter keywords then click Search.\n"
        self.import_result_placeholder_zh = "导入结果会显示在这里。\n"
        self.import_result_placeholder_en = "Import results will appear here.\n"

        self._build_ui()

    def _build_ui(self) -> None:
        self.root = tk.Tk()
        self.root.title("\u5916\u8d38\u52a9\u7406\u684c\u9762\u7248")
        self.root.geometry("1320x860")
        self.root.minsize(980, 720)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_request)
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, pady=(0, 8))
        self.notice_label = ttk.Label(top, text="\u6743\u9650\u53ea\u8bfb\uff1a\u4ec5\u626b\u63cf\u4f60\u9009\u62e9\u7684\u6587\u4ef6\u3002", foreground="#8b5a00")
        self.notice_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lang_zh_btn = ttk.Button(top, text="\u4e2d\u6587", width=6, command=lambda: self._switch_language("zh"))
        self.lang_zh_btn.pack(side=tk.RIGHT, padx=(6, 0))
        self.lang_en_btn = ttk.Button(top, text="EN", width=6, command=lambda: self._switch_language("en"))
        self.lang_en_btn.pack(side=tk.RIGHT)

        self.main_canvas = tk.Canvas(frame, highlightthickness=0)
        self.main_scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.main_canvas.yview)
        self.main_scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.main_canvas.xview)
        self.main_canvas.configure(yscrollcommand=self.main_scroll_y.set, xscrollcommand=self.main_scroll_x.set)
        self.main_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.main_content = ttk.Frame(self.main_canvas)
        self.main_window = self.main_canvas.create_window((0, 0), window=self.main_content, anchor="nw")
        self.main_content.bind("<Configure>", self._configure_canvas_scrollregion)
        self.main_canvas.bind("<Configure>", self._on_canvas_configure)

        self.main_panes = ttk.Panedwindow(self.main_content, orient=tk.HORIZONTAL)
        self.main_panes.pack(fill=tk.BOTH, expand=True)
        self.left_panel = ttk.Frame(self.main_panes, padding=(0, 0, 6, 0))
        self.middle_panel = ttk.Frame(self.main_panes, padding=(6, 0, 6, 0))
        self.right_panel = ttk.Frame(self.main_panes, padding=(6, 0, 0, 0))
        self.main_panes.add(self.left_panel, weight=3)
        self.main_panes.add(self.middle_panel, weight=4)
        self.main_panes.add(self.right_panel, weight=3)

        self._build_service_section(self.left_panel)
        self._build_import_section(self.left_panel)
        self._build_output_section(self.left_panel)

        self._build_api_section(self.middle_panel)

        self._build_radar_section(self.left_panel)
        self._build_guide_section(self.left_panel)

        self._build_runtime_section(self.right_panel)
        self._build_feedback_section(self.right_panel)
        self._apply_language_texts()
        self._apply_beginner_mode()
        self.root.after(500, self.begin_work_session)
        self.root.after(1200, self._focus_primary_entry)
        self.root.after(1500, self.refresh_runtime_status)
        self.root.after(2500, self._service_watchdog_tick)

    def _configure_canvas_scrollregion(self, _event: tk.Event | None = None) -> None:
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.main_canvas.itemconfigure(self.main_window, width=max(event.width, 1360))
        self._configure_canvas_scrollregion()

    def _switch_language(self, lang: str) -> None:
        self.ui_lang = "en" if lang == "en" else "zh"
        self._apply_language_texts()

    def _tr(self, zh: str, en: str) -> str:
        return zh if self.ui_lang == "zh" else en

    def _apply_language_texts(self) -> None:
        is_zh = self.ui_lang == "zh"
        if is_zh:
            self.root.title("\u5916\u8d38\u52a9\u7406\u684c\u9762\u7248")
            self.notice_label.configure(text="\u6743\u9650\u53ea\u8bfb\uff1a\u4ec5\u626b\u63cf\u4f60\u9009\u62e9\u7684\u6587\u4ef6\u3002")
            self.service_section_box.configure(text="1) \u5de5\u4f5c\u5165\u53e3\uff08\u63a8\u8350\uff09")
            self.start_work_button.configure(text="\u4e00\u952e\u542f\u52a8")
            self.open_workbench_button.configure(text="\u6253\u5f00\u7f51\u9875\u770b\u677f")
            self.quick_start_button.configure(text="1) \u4e00\u952e\u542f\u52a8")
            self.quick_import_button.configure(text="2) \u4e00\u952e\u5bfc\u5165")
            self.quick_task_button.configure(text="3) \u5f00\u59cb\u5904\u7406\u4efb\u52a1")
            self.beginner_mode_check.configure(text="\u65b0\u624b\u6a21\u5f0f")
            self.show_advanced_check.configure(text="\u663e\u793a\u9ad8\u7ea7\u9879")
            self.update_button.configure(text="\u4e00\u952e\u66f4\u65b0")
            self.service_only_button.configure(text="\u4ec5\u542f\u52a8\u670d\u52a1")
            self.edge_extension_button.configure(text="\u6253\u5f00 Edge \u6269\u5c55\u9875")
            self.health_check_button.configure(text="\u5065\u5eb7\u68c0\u67e5")
            self.export_diag_button.configure(text="\u5bfc\u51fa\u8bca\u65ad")
            self.feedback_inbox_button.configure(text="\u53cd\u9988\u6536\u4ef6\u7bb1")
            self.runtime_section_box.configure(text="2) \u770b\u677f\u8f93\u51fa\uff08\u7f51\u9875\u770b\u677f\u5904\u7406\u4e1a\u52a1\uff09")
            self.runtime_hint_var.set("\u684c\u9762\u7aef\u5904\u7406\u542f\u52a8/\u5bfc\u5165/\u540c\u6b65\uff0c\u5176\u4ed6\u4e1a\u52a1\u7ee7\u7eed\u5728\u7f51\u9875\u770b\u677f\u5b8c\u6210\u3002")
            self.output_section_box.configure(text="\u8f93\u51fa\u76ee\u5f55")
            self.import_section_box.configure(text="\u5386\u53f2\u5bfc\u5165")
            self.guide_section_box.configure(text="\u6269\u5c55\u5b89\u88c5\u5411\u5bfc")
            self.feedback_section_box.configure(text="7) \u53cd\u9988")
            self.radar_section_box.configure(text="\u96f7\u8fbe\u68c0\u7d22")
            self.radar_hint_label.configure(text="\u652f\u6301\u6a21\u7cca\u8bcd\u548c\u7cbe\u786e\u8bcd\uff1a\u5ba2\u6237/\u90ae\u7bb1/\u7535\u8bdd/\u4ea7\u54c1/SKU/\u7cfb\u5217\u3002")
            self.import_hint_label.configure(text="\u53ef\u91cd\u590d\u5bfc\u5165 + \u81ea\u52a8\u53bb\u91cd\u3002\u9996\u6b21\u5168\u91cf\u5bfc\u5165\uff0c\u540e\u7eed\u589e\u91cf\u5bfc\u5165\u3002")
            self.email_thread_label.configure(text="\u90ae\u4ef6\u7ebf\u7a0b\uff1a")
            self.runtime_refresh_button.configure(text="\u5237\u65b0")
            self.runtime_open_workbench_button.configure(text="\u6253\u5f00\u7f51\u9875\u770b\u677f")
            self.action_execute_button.configure(text="\u52a8\u4f5c\u6807\u7b7e\u6267\u884c")
            self.radar_search_button.configure(text="\u68c0\u7d22")
            self.radar_capsule_button.configure(text="\u751f\u6210\u80f6\u56ca")
            self.api_box.configure(text="\u5bf9\u8bdd\u4e2d\u67a2\uff08API\uff09")
            self.api_provider_label.configure(text="\u670d\u52a1\u5546")
            self.api_key_label.configure(text="API Key")
            self.api_model_label.configure(text="\u6a21\u578b")
            self.api_url_label.configure(text="API \u5730\u5740")
            self.api_use_local_context_check.configure(text="\u4f7f\u7528\u672c\u5730\u4e0a\u4e0b\u6587")
            self.api_input_label.configure(text="\u8f93\u5165")
            self.api_reply_label.configure(text="\u56de\u590d")
            self.api_basis_label.configure(text="\u56de\u7b54\u4f9d\u636e")
            self.api_save_button.configure(text="\u4fdd\u5b58 API")
            self.api_test_button.configure(text="\u8fde\u63a5\u6d4b\u8bd5")
            self.api_send_button.configure(text="\u53d1\u9001")
            self.output_section_box.configure(text="\u8f93\u51fa\u76ee\u5f55")
            self.choose_output_dir_button.configure(text="\u9009\u62e9\u76ee\u5f55")
            self.save_output_dir_button.configure(text="\u4fdd\u5b58")
            self.import_section_box.configure(text="\u5386\u53f2\u5bfc\u5165")
            self.choose_import_dir_button.configure(text="\u9009\u62e9\u5386\u53f2\u76ee\u5f55")
            self.choose_import_files_button.configure(text="\u9009\u62e9\u6587\u4ef6")
            self.clear_import_files_button.configure(text="\u6e05\u7a7a\u6587\u4ef6\u9009\u62e9")
            self.import_button.configure(text="\u9996\u6b21\u5168\u91cf\u5bfc\u5165")
            self.incremental_button.configure(text="\u5bfc\u5165\u65b0\u589e\u8d44\u6599")
            self.retry_button.configure(text="\u91cd\u8bd5\u5931\u8d25\u6587\u4ef6")
            self.email_import_button.configure(text="\u6279\u91cf\u5bfc\u5165\u90ae\u4ef6\u7ebf\u7a0b")
            self.email_retry_button.configure(text="\u91cd\u8bd5\u5931\u8d25\u90ae\u4ef6\u6587\u4ef6")
            self.mail_provider_label.configure(text="\u90ae\u7bb1\u4e00\u952e\u62c9\u53d6\uff1a")
            self.mail_login_hint_label.configure(
                text="IMAP 登录：请填写邮箱账号 + 应用专用密码（不是邮箱登录密码）。"
            )
            self.mail_days_suffix_label.configure(text="\u5929")
            self.mail_limit_suffix_label.configure(text="\u4e0a\u9650")
            self.remember_mail_password_check.configure(text="\u8bb0\u4f4f\u5bc6\u7801")
            self.pull_mail_button.configure(text="\u4e00\u952e\u62c9\u53d6\u5e76\u5bfc\u5165")
            self.guide_section_box.configure(text="\u6269\u5c55\u5b89\u88c5\u5411\u5bfc")
            self.guide_text_var.set("\u6b65\u9aa4 1\uff1a\u6253\u5f00 chrome://extensions\n\u6b65\u9aa4 2\uff1a\u5f00\u542f\u5f00\u53d1\u8005\u6a21\u5f0f\n\u6b65\u9aa4 3\uff1a\u52a0\u8f7d extension \u76ee\u5f55")
            self.open_chrome_extensions_button.configure(text="\u6253\u5f00 Chrome \u6269\u5c55\u9875")
            self.open_extension_folder_button.configure(text="\u6253\u5f00 extension \u76ee\u5f55")
            self.feedback_section_box.configure(text="7) \u53cd\u9988")
            self.submit_feedback_button.configure(text="\u63d0\u4ea4\u53cd\u9988")
            self.open_feedback_inbox_button.configure(text="\u6253\u5f00\u53cd\u9988\u6536\u4ef6\u7bb1")
        else:
            self.root.title("Trade Assistant Desktop")
            self.notice_label.configure(text="Read-only: scans selected files only.")
            self.service_section_box.configure(text="1) Work Entry (Recommended)")
            self.start_work_button.configure(text="Start Work")
            self.open_workbench_button.configure(text="Open Web Workbench")
            self.quick_start_button.configure(text="1) Start Work")
            self.quick_import_button.configure(text="2) One-click Import")
            self.quick_task_button.configure(text="3) Start Handling Tasks")
            self.beginner_mode_check.configure(text="Beginner Mode")
            self.show_advanced_check.configure(text="Show Advanced")
            self.update_button.configure(text="One-click Update")
            self.service_only_button.configure(text="Start Service Only")
            self.edge_extension_button.configure(text="Open Edge Extensions")
            self.health_check_button.configure(text="Health Check")
            self.export_diag_button.configure(text="Export Diagnostics")
            self.feedback_inbox_button.configure(text="Feedback Inbox")
            self.runtime_section_box.configure(text="2) Workbench Output (Web Workbench handles business)")
            self.runtime_hint_var.set("Desktop handles startup/import/sync. Continue operations in Web Workbench (tasks/customers/events).")
            self.output_section_box.configure(text="Output Directory")
            self.import_section_box.configure(text="History Import")
            self.guide_section_box.configure(text="Extension Setup Guide")
            self.feedback_section_box.configure(text="7) Feedback")
            self.radar_section_box.configure(text="Radar Search")
            self.radar_hint_label.configure(text="Supports fuzzy and exact terms: customer/email/phone/product/SKU/series.")
            self.import_hint_label.configure(text="Repeatable import + auto-dedup. First full import, then incremental import.")
            self.email_thread_label.configure(text="Mail Threads:")
            self.runtime_refresh_button.configure(text="Refresh")
            self.runtime_open_workbench_button.configure(text="Open Web Workbench")
            self.action_execute_button.configure(text="Execute Action Tag")
            self.radar_search_button.configure(text="Search")
            self.radar_capsule_button.configure(text="Build Capsule")
            self.api_box.configure(text="Conversation Core (API)")
            self.api_provider_label.configure(text="Provider")
            self.api_key_label.configure(text="API Key")
            self.api_model_label.configure(text="Model")
            self.api_url_label.configure(text="API URL")
            self.api_use_local_context_check.configure(text="Use Local Context")
            self.api_input_label.configure(text="Input")
            self.api_reply_label.configure(text="Reply")
            self.api_basis_label.configure(text="Answer Basis")
            self.api_save_button.configure(text="Save API")
            self.api_test_button.configure(text="Connection Test")
            self.api_send_button.configure(text="Send")
            self.output_section_box.configure(text="Output Directory")
            self.choose_output_dir_button.configure(text="Choose Folder")
            self.save_output_dir_button.configure(text="Save")
            self.import_section_box.configure(text="History Import")
            self.choose_import_dir_button.configure(text="Choose History Folder")
            self.choose_import_files_button.configure(text="Choose Files")
            self.clear_import_files_button.configure(text="Clear File Selection")
            self.import_button.configure(text="First Full Import")
            self.incremental_button.configure(text="Incremental Import")
            self.retry_button.configure(text="Retry Failed Files")
            self.email_import_button.configure(text="Batch Import Mail Threads")
            self.email_retry_button.configure(text="Retry Failed Mail Files")
            self.mail_provider_label.configure(text="Mailbox pull:")
            self.mail_login_hint_label.configure(
                text="IMAP login: use mailbox account + app password (not your normal mailbox password)."
            )
            self.mail_days_suffix_label.configure(text="Days")
            self.mail_limit_suffix_label.configure(text="Limit")
            self.remember_mail_password_check.configure(text="Remember Password")
            self.pull_mail_button.configure(text="Mail Pull and Import")
            self.guide_section_box.configure(text="Extension Setup Guide")
            self.guide_text_var.set("Step 1: Open chrome://extensions\nStep 2: Enable Developer mode\nStep 3: Load the extension folder")
            self.open_chrome_extensions_button.configure(text="Open Chrome Extensions")
            self.open_extension_folder_button.configure(text="Open extension Folder")
            self.feedback_section_box.configure(text="7) Feedback")
            self.submit_feedback_button.configure(text="Submit Feedback")
            self.open_feedback_inbox_button.configure(text="Open Feedback Inbox")
        self._sync_localized_placeholders()

    def _sync_localized_placeholders(self) -> None:
        api_status = self.api_status_var.get().strip()
        if api_status in {"\u5f85\u8fde\u63a5", "Waiting for connection"}:
            self.api_status_var.set(self._tr("\u5f85\u8fde\u63a5", "Waiting for connection"))
        import_status = self.import_status.get().strip()
        if import_status in {"\u7b49\u5f85\u5bfc\u5165", "Waiting for import"}:
            self.import_status.set(self._tr("\u7b49\u5f85\u5bfc\u5165", "Waiting for import"))
        service_status = self.service_status.get().strip()
        if service_status in {"\u672a\u542f\u52a8", "Not started"}:
            self.service_status.set(self._tr("\u672a\u542f\u52a8", "Not started"))

        basis_value = self.api_basis_text.get("1.0", tk.END).strip()
        if basis_value in {self.api_basis_default_zh, self.api_basis_default_en}:
            self._set_text_content(self.api_basis_text, self._tr(self.api_basis_default_zh, self.api_basis_default_en))

        radar_value = self.radar_result.get("1.0", tk.END)
        radar_value_stripped = radar_value.strip()
        if radar_value in {
            self.radar_placeholder_zh,
            self.radar_placeholder_en,
        } or radar_value_stripped in {self.radar_placeholder_zh.strip(), self.radar_placeholder_en.strip()}:
            self.radar_result.configure(state=tk.NORMAL)
            self.radar_result.delete("1.0", tk.END)
            self.radar_result.insert(tk.END, self._tr(self.radar_placeholder_zh, self.radar_placeholder_en))
            self.radar_result.configure(state=tk.DISABLED)

        result_value = self.result_text.get("1.0", tk.END)
        result_value_stripped = result_value.strip()
        if result_value in {
            self.import_result_placeholder_zh,
            self.import_result_placeholder_en,
        } or result_value_stripped in {self.import_result_placeholder_zh.strip(), self.import_result_placeholder_en.strip()}:
            self.result_text.configure(state=tk.NORMAL)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, self._tr(self.import_result_placeholder_zh, self.import_result_placeholder_en))
            self.result_text.configure(state=tk.DISABLED)

    def _set_text_content(self, widget: tk.Text, text: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.see(tk.END)
        widget.configure(state=tk.NORMAL)

    def _append_text_content(self, widget: tk.Text, text: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.insert(tk.END, text)
        widget.see(tk.END)
        widget.configure(state=tk.NORMAL)

    def _build_service_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="1) \u5de5\u4f5c\u5165\u53e3\uff08\u63a8\u8350\uff09", padding=10)
        box.pack(fill=tk.X, pady=6)
        self.service_section_box = box
        row = ttk.Frame(box)
        row.pack(fill=tk.X)
        self.service_status = tk.StringVar(value="\u672a\u542f\u52a8")
        self.start_work_button = ttk.Button(row, text="\u4e00\u952e\u542f\u52a8", command=self.begin_work_session)
        self.start_work_button.pack(side=tk.LEFT)
        self.open_workbench_button = ttk.Button(row, text="\u6253\u5f00\u7f51\u9875\u770b\u677f", command=self.open_dashboard_workbench)
        self.open_workbench_button.pack(side=tk.LEFT, padx=8)
        self.beginner_mode_var = tk.BooleanVar(value=True)
        self.beginner_mode_check = ttk.Checkbutton(
            row,
            text="\u65b0\u624b\u6a21\u5f0f",
            variable=self.beginner_mode_var,
            command=self._apply_beginner_mode,
        )
        self.beginner_mode_check.pack(side=tk.LEFT, padx=8)
        self.show_advanced_var = tk.BooleanVar(value=False)
        self.show_advanced_check = ttk.Checkbutton(
            row,
            text="\u663e\u793a\u9ad8\u7ea7\u9879",
            variable=self.show_advanced_var,
            command=self._toggle_service_advanced,
        )
        self.show_advanced_check.pack(side=tk.LEFT, padx=8)
        self.service_status_label = ttk.Label(row, textvariable=self.service_status)
        self.service_status_label.pack(side=tk.LEFT, padx=12)

        self.quick_actions_frame = ttk.Frame(box)
        self.quick_actions_frame.pack(fill=tk.X, pady=(8, 0))
        self.quick_start_button = ttk.Button(self.quick_actions_frame, text="1) \u4e00\u952e\u542f\u52a8", command=self.begin_work_session)
        self.quick_start_button.pack(side=tk.LEFT)
        self.quick_import_button = ttk.Button(self.quick_actions_frame, text="2) \u4e00\u952e\u5bfc\u5165", command=self._beginner_quick_import)
        self.quick_import_button.pack(side=tk.LEFT, padx=8)
        self.quick_task_button = ttk.Button(
            self.quick_actions_frame,
            text="3) \u5f00\u59cb\u5904\u7406\u4efb\u52a1",
            command=lambda: self.open_dashboard_workbench(task_status="open"),
        )
        self.quick_task_button.pack(side=tk.LEFT, padx=8)
        self.update_button = ttk.Button(self.quick_actions_frame, text="\u4e00\u952e\u66f4\u65b0", command=self.one_click_update)
        self.update_button.pack(side=tk.LEFT, padx=8)

        self.service_advanced_frame = ttk.Frame(box)
        self.service_advanced_frame.pack(fill=tk.X, pady=(8, 0))
        self.service_only_button = ttk.Button(self.service_advanced_frame, text="\u4ec5\u542f\u52a8\u670d\u52a1", command=self.start_services)
        self.service_only_button.pack(side=tk.LEFT)
        self.edge_extension_button = ttk.Button(self.service_advanced_frame, text="\u6253\u5f00 Edge \u6269\u5c55\u9875", command=self.open_edge_extensions_page)
        self.edge_extension_button.pack(side=tk.LEFT, padx=8)
        self.health_check_button = ttk.Button(self.service_advanced_frame, text="\u5065\u5eb7\u68c0\u67e5", command=self.run_health_check)
        self.health_check_button.pack(side=tk.LEFT, padx=8)
        self.export_diag_button = ttk.Button(self.service_advanced_frame, text="\u5bfc\u51fa\u8bca\u65ad", command=self.export_diagnostics)
        self.export_diag_button.pack(side=tk.LEFT, padx=8)
        self.feedback_inbox_button = ttk.Button(self.service_advanced_frame, text="\u53cd\u9988\u6536\u4ef6\u7bb1", command=self.open_feedback_inbox)
        self.feedback_inbox_button.pack(side=tk.LEFT, padx=8)
        self.service_advanced_frame.pack_forget()

    def _build_runtime_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="2) \u770b\u677f\u8f93\u51fa\uff08\u7f51\u9875\u770b\u677f\u5904\u7406\u4e1a\u52a1\uff09", padding=10)
        box.pack(fill=tk.BOTH, pady=6)
        self.runtime_section_box = box

        top = ttk.Frame(box)
        top.pack(fill=tk.X, pady=(0, 6))
        self.sync_status_var = tk.StringVar(value="\u6700\u8fd1\u540c\u6b65\uff1a\u65e0")
        ttk.Label(top, textvariable=self.sync_status_var).pack(side=tk.LEFT)
        self.runtime_open_workbench_button = ttk.Button(top, text="\u6253\u5f00\u7f51\u9875\u770b\u677f", command=self.open_dashboard_workbench)
        self.runtime_open_workbench_button.pack(side=tk.RIGHT)
        self.runtime_refresh_button = ttk.Button(top, text="\u5237\u65b0", command=self.refresh_runtime_status)
        self.runtime_refresh_button.pack(side=tk.RIGHT, padx=(0, 8))

        metrics = ttk.Frame(box)
        metrics.pack(fill=tk.X, pady=(0, 8))
        self.metric_events = tk.StringVar(value="\u6700\u8fd1\u4e8b\u4ef6\uff1a0")
        self.metric_focus = tk.StringVar(value="\u91cd\u70b9\u4efb\u52a1\uff1a0")
        self.metric_alerts = tk.StringVar(value="\u98ce\u9669\u63d0\u9192\uff1a0")
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
        self.action_execute_button = ttk.Button(action_row, text="\u52a8\u4f5c\u6807\u7b7e\u6267\u884c", command=self.execute_action_tag)
        self.action_execute_button.pack(side=tk.LEFT, padx=8)

    def _build_api_section(self, parent: ttk.Frame) -> None:
        self.api_box = ttk.LabelFrame(parent, text="\u5bf9\u8bdd\u4e2d\u67a2\uff08API\uff09", padding=10)
        self.api_box.pack(fill=tk.BOTH, expand=True, pady=6)

        settings_row = ttk.Frame(self.api_box)
        settings_row.pack(fill=tk.X)
        self.api_provider_label = ttk.Label(settings_row, text="\u670d\u52a1\u5546")
        self.api_provider_label.pack(side=tk.LEFT)
        self.api_provider_var = tk.StringVar(value=self.settings.api_provider or "nvidia")
        provider_box = ttk.Combobox(
            settings_row,
            width=10,
            textvariable=self.api_provider_var,
            values=["nvidia", "openai", "openrouter", "deepseek", "qwen", "doubao", "google", "custom"],
            state="readonly",
        )
        provider_box.pack(side=tk.LEFT, padx=(6, 8))
        provider_box.bind("<<ComboboxSelected>>", self._on_api_provider_changed)

        self.api_key_label = ttk.Label(settings_row, text="API Key")
        self.api_key_label.pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar(value=self.settings.api_key or "")
        ttk.Entry(settings_row, textvariable=self.api_key_var, show="*", width=26).pack(side=tk.LEFT, padx=(6, 8))
        self.api_model_label = ttk.Label(settings_row, text="\u6a21\u578b")
        self.api_model_label.pack(side=tk.LEFT)
        self.api_model_var = tk.StringVar(value=self.settings.api_model or default_model(self.api_provider_var.get()))
        ttk.Entry(settings_row, textvariable=self.api_model_var, width=24).pack(side=tk.LEFT, padx=(6, 0))

        settings_row2 = ttk.Frame(self.api_box)
        settings_row2.pack(fill=tk.X, pady=(6, 0))
        self.api_url_label = ttk.Label(settings_row2, text="API \u5730\u5740")
        self.api_url_label.pack(side=tk.LEFT)
        self.api_url_var = tk.StringVar(value=self.settings.api_url or default_api_url(self.api_provider_var.get()))
        ttk.Entry(settings_row2, textvariable=self.api_url_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 8))
        self.api_save_button = ttk.Button(settings_row2, text="\u4fdd\u5b58 API", command=self.save_api_settings)
        self.api_save_button.pack(side=tk.LEFT, padx=(0, 6))
        self.api_test_button = ttk.Button(settings_row2, text="\u8fde\u63a5\u6d4b\u8bd5", command=self.test_api_connection)
        self.api_test_button.pack(side=tk.LEFT)

        self.api_use_local_context_var = tk.BooleanVar(value=bool(self.settings.api_use_local_context))
        self.api_use_local_context_check = ttk.Checkbutton(self.api_box, text="\u4f7f\u7528\u672c\u5730\u4e0a\u4e0b\u6587", variable=self.api_use_local_context_var)
        self.api_use_local_context_check.pack(anchor=tk.W, pady=(6, 0))

        self.api_input_label = ttk.Label(self.api_box, text="\u8f93\u5165")
        self.api_input_label.pack(anchor=tk.W, pady=(6, 0))
        self.api_input_text = tk.Text(self.api_box, height=4, wrap=tk.WORD)
        self.api_input_text.pack(fill=tk.X)
        self.api_input_text.bind("<Return>", self._on_api_input_return)
        self.api_input_text.bind("<KP_Enter>", self._on_api_input_return)

        send_row = ttk.Frame(self.api_box)
        send_row.pack(fill=tk.X, pady=(6, 0))
        self.api_status_var = tk.StringVar(value="\u5f85\u8fde\u63a5")
        ttk.Label(send_row, textvariable=self.api_status_var).pack(side=tk.LEFT)
        self.api_send_button = ttk.Button(send_row, text="\u53d1\u9001", command=self.send_api_message)
        self.api_send_button.pack(side=tk.RIGHT)

        self.api_result_pane = ttk.Panedwindow(self.api_box, orient=tk.VERTICAL)
        self.api_result_pane.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.api_reply_frame = ttk.Frame(self.api_result_pane)
        self.api_result_pane.add(self.api_reply_frame, weight=3)
        self.api_reply_label = ttk.Label(self.api_reply_frame, text="\u56de\u590d")
        self.api_reply_label.pack(anchor=tk.W, pady=(0, 2))
        self.api_reply_text = tk.Text(self.api_reply_frame, height=8, wrap=tk.WORD)
        self.api_reply_text.pack(fill=tk.BOTH, expand=True)

        self.api_basis_frame = ttk.Frame(self.api_result_pane)
        self.api_result_pane.add(self.api_basis_frame, weight=2)
        self.api_basis_label = ttk.Label(self.api_basis_frame, text="\u56de\u7b54\u4f9d\u636e")
        self.api_basis_label.pack(anchor=tk.W, pady=(0, 2))
        self.api_basis_text = tk.Text(self.api_basis_frame, height=4, wrap=tk.WORD)
        self.api_basis_text.pack(fill=tk.BOTH, expand=True)
        self._set_text_content(self.api_basis_text, self.api_basis_default_zh)
        self.root.after_idle(lambda: self._set_api_result_split(0.72))

    def _on_api_provider_changed(self, _event: tk.Event | None = None) -> None:
        provider = self.api_provider_var.get().strip().lower() or "nvidia"
        if provider != "custom":
            self.api_url_var.set(default_api_url(provider))
            if not self.api_model_var.get().strip():
                self.api_model_var.set(default_model(provider))

    def _collect_api_settings(self) -> ApiChatSettings:
        provider = self.api_provider_var.get().strip().lower() or "nvidia"
        api_url = self.api_url_var.get().strip() or default_api_url(provider)
        model = self.api_model_var.get().strip() or default_model(provider)
        return ApiChatSettings(
            provider=provider,
            api_key=self.api_key_var.get().strip(),
            model=model,
            api_url=api_url,
            timeout_sec=self.settings.api_timeout_sec,
        )

    def save_api_settings(self) -> None:
        settings = self._collect_api_settings()
        self.settings.api_provider = settings.provider
        self.settings.api_key = settings.api_key
        self.settings.api_model = settings.model
        self.settings.api_url = settings.api_url
        self.settings.api_use_local_context = bool(self.api_use_local_context_var.get())
        self.settings_store.save(self.settings)
        self.api_status_var.set(self._tr("\u5df2\u4fdd\u5b58", "Saved"))

    def _handle_api_error(self, exc: ApiChatError, *, title: str) -> None:
        self.api_send_button.configure(state=tk.NORMAL)
        self.api_status_var.set(self._tr("\u5931\u8d25", "Failed"))
        self._append_text_content(self.api_reply_text, f"\n[ERROR] {exc}\n")
        messagebox.showerror(title, str(exc))

    def _on_api_input_return(self, event: tk.Event) -> str | None:
        if getattr(event, "state", 0) & 0x0001:
            return None
        self.send_api_message()
        return "break"

    def _set_api_result_split(self, ratio: float) -> None:
        try:
            total_height = self.api_result_pane.winfo_height()
            if total_height <= 1:
                total_height = self.api_box.winfo_height()
            if total_height > 1:
                self.api_result_pane.sashpos(0, max(120, int(total_height * ratio)))
        except tk.TclError:
            pass

    def test_api_connection(self) -> None:
        settings = self._collect_api_settings()
        if not settings.api_key:
            messagebox.showwarning("API", "\u8bf7\u5148\u586b\u5199 API Key\u3002")
            return
        self.api_send_button.configure(state=tk.DISABLED)
        self.api_status_var.set(self._tr("\u6d4b\u8bd5\u4e2d...", "Testing..."))

        def worker() -> None:
            try:
                reply = send_chat_request(settings, "Ping")
            except ApiChatError as exc:
                self.root.after(0, lambda e=exc: self._handle_api_error(e, title="Connection Test"))
                return
            except Exception as exc:  # pragma: no cover
                self.root.after(
                    0,
                    lambda e=exc: (
                        self.api_send_button.configure(state=tk.NORMAL),
                        self.api_status_var.set(self._tr("\u5931\u8d25", "Failed")),
                        messagebox.showerror("Connection Test", str(e)),
                    ),
                )
                return
            self.root.after(
                0,
                lambda r=reply: (
                    self.api_send_button.configure(state=tk.NORMAL),
                    self.api_status_var.set(self._tr("API \u6b63\u5e38", "API Ready")),
                    self._append_text_content(self.api_reply_text, r + "\n"),
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def send_api_message(self) -> None:
        user_text = self.api_input_text.get("1.0", tk.END).strip()
        if not user_text:
            return
        settings = self._collect_api_settings()
        if not settings.api_key:
            messagebox.showwarning("API", "\u8bf7\u5148\u586b\u5199 API Key\u3002")
            return

        prompt = user_text
        if bool(self.api_use_local_context_var.get()):
            context = build_local_context(
                capsule_builder=self.capsule_builder,
                user_input=user_text,
                model_name=settings.model,
                template_lang="zh" if self.ui_lang == "zh" else "en",
            )
            prompt = context.prompt
            self._set_text_content(self.api_basis_text, context.answer_basis)
        else:
            self._set_text_content(self.api_basis_text, "Local context disabled.")

        self.api_send_button.configure(state=tk.DISABLED)
        self.api_status_var.set(self._tr("\u53d1\u9001\u4e2d...", "Sending..."))
        self._append_text_content(self.api_reply_text, "[Sending...]\n")

        def worker() -> None:
            try:
                reply = send_chat_request(settings, prompt)
            except ApiChatError as exc:
                self.root.after(0, lambda e=exc: self._handle_api_error(e, title="API Chat"))
                return
            except Exception as exc:  # pragma: no cover
                self.root.after(
                    0,
                    lambda e=exc: (
                        self.api_send_button.configure(state=tk.NORMAL),
                        self.api_status_var.set(self._tr("\u5931\u8d25", "Failed")),
                        self._append_text_content(self.api_reply_text, f"\n[ERROR] {e}\n"),
                        messagebox.showerror("API Chat", str(e)),
                    ),
                )
                return
            self.root.after(
                0,
                lambda r=reply: (
                    self.api_send_button.configure(state=tk.NORMAL),
                    self.api_status_var.set(self._tr("\u5b8c\u6210", "Done")),
                    self._append_text_content(self.api_reply_text, r + "\n"),
                    self.api_input_text.delete("1.0", tk.END),
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _build_radar_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="\u96f7\u8fbe\u68c0\u7d22", padding=10)
        box.pack(fill=tk.BOTH, pady=6)
        self.radar_section_box = box

        top = ttk.Frame(box)
        top.pack(fill=tk.X)
        self.radar_query_var = tk.StringVar(value="")
        ttk.Entry(top, textvariable=self.radar_query_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.radar_search_button = ttk.Button(top, text="\u68c0\u7d22", command=self.run_radar_search)
        self.radar_search_button.pack(side=tk.LEFT, padx=8)
        self.radar_capsule_button = ttk.Button(top, text="\u751f\u6210\u80f6\u56ca", command=self.generate_radar_capsule)
        self.radar_capsule_button.pack(side=tk.LEFT, padx=8)

        self.radar_hint_label = ttk.Label(
            box,
            text="\u652f\u6301\u6a21\u7cca\u8bcd\u548c\u7cbe\u786e\u8bcd\uff1a\u5ba2\u6237/\u90ae\u7bb1/\u7535\u8bdd/\u4ea7\u54c1/SKU/\u7cfb\u5217\u3002",
            foreground="#444",
        )
        self.radar_hint_label.pack(anchor=tk.W, pady=(6, 4))

        wrap = ttk.Frame(box)
        wrap.pack(fill=tk.BOTH, expand=True)
        self.radar_result = tk.Text(wrap, height=10, wrap=tk.WORD)
        self.radar_result.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=self.radar_result.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.radar_result.config(yscrollcommand=scroll.set)
        self.radar_placeholder = self.radar_placeholder_zh
        self.radar_result.insert(tk.END, self.radar_placeholder)
        self.radar_result.configure(state=tk.DISABLED)

    def _build_output_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="\u8f93\u51fa\u76ee\u5f55", padding=10)
        box.pack(fill=tk.X, pady=6)
        self.output_section_box = box
        row = ttk.Frame(box)
        row.pack(fill=tk.X)
        self.output_var = tk.StringVar(value=self.settings.output_dir or str(self.config.output_dir))
        ttk.Entry(row, textvariable=self.output_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.choose_output_dir_button = ttk.Button(row, text="\u9009\u62e9\u76ee\u5f55", command=self.choose_output_dir)
        self.choose_output_dir_button.pack(side=tk.LEFT, padx=8)
        self.save_output_dir_button = ttk.Button(row, text="\u4fdd\u5b58", command=self.save_output_dir)
        self.save_output_dir_button.pack(side=tk.LEFT)

    def _build_import_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="\u5386\u53f2\u5bfc\u5165", padding=10)
        box.pack(fill=tk.BOTH, expand=True, pady=6)
        self.import_section_box = box

        top = ttk.Frame(box)
        top.pack(fill=tk.X)
        self.import_dir_var = tk.StringVar(value="")
        ttk.Entry(top, textvariable=self.import_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.choose_import_dir_button = ttk.Button(top, text="\u9009\u62e9\u5386\u53f2\u76ee\u5f55", command=self.choose_import_dir)
        self.choose_import_dir_button.pack(side=tk.LEFT, padx=8)
        self.choose_import_files_button = ttk.Button(top, text="\u9009\u62e9\u6587\u4ef6", command=self.choose_import_files)
        self.choose_import_files_button.pack(side=tk.LEFT, padx=(0, 8))
        self.clear_import_files_button = ttk.Button(top, text="\u6e05\u7a7a\u6587\u4ef6\u9009\u62e9", command=self.clear_import_files)
        self.clear_import_files_button.pack(side=tk.LEFT)

        self.import_hint_label = ttk.Label(
            box,
            text="\u53ef\u91cd\u590d\u5bfc\u5165 + \u81ea\u52a8\u53bb\u91cd\u3002\u9996\u6b21\u5168\u91cf\u5bfc\u5165\uff0c\u540e\u7eed\u589e\u91cf\u5bfc\u5165\u3002",
            justify=tk.LEFT,
            foreground="#444",
        )
        self.import_hint_label.pack(fill=tk.X, pady=(8, 6))

        actions = ttk.Frame(box)
        actions.pack(fill=tk.X, pady=8)
        self.import_button = ttk.Button(actions, text="\u9996\u6b21\u5168\u91cf\u5bfc\u5165", command=lambda: self.start_import(mode="full"))
        self.import_button.pack(side=tk.LEFT)
        self.incremental_button = ttk.Button(actions, text="\u5bfc\u5165\u65b0\u589e\u8d44\u6599", command=lambda: self.start_import(mode="incremental"))
        self.incremental_button.pack(side=tk.LEFT, padx=8)
        self.retry_button = ttk.Button(actions, text="\u91cd\u8bd5\u5931\u8d25\u6587\u4ef6", command=self.retry_failed, state=tk.DISABLED)
        self.retry_button.pack(side=tk.LEFT, padx=8)

        email_actions = ttk.Frame(box)
        email_actions.pack(fill=tk.X, pady=(0, 8))
        self.email_thread_label = ttk.Label(email_actions, text="\u90ae\u4ef6\u7ebf\u7a0b\uff1a")
        self.email_thread_label.pack(side=tk.LEFT)
        self.email_import_button = ttk.Button(email_actions, text="\u6279\u91cf\u5bfc\u5165\u90ae\u4ef6\u7ebf\u7a0b", command=self.start_email_import)
        self.email_import_button.pack(side=tk.LEFT, padx=(8, 0))
        self.email_retry_button = ttk.Button(email_actions, text="\u91cd\u8bd5\u5931\u8d25\u90ae\u4ef6\u6587\u4ef6", command=self.retry_failed_email, state=tk.DISABLED)
        self.email_retry_button.pack(side=tk.LEFT, padx=8)

        connector = ttk.Frame(box)
        connector.pack(fill=tk.X, pady=(0, 8))
        self.mail_provider_label = ttk.Label(connector, text="\u90ae\u7bb1\u4e00\u952e\u62c9\u53d6\uff1a")
        self.mail_provider_label.pack(side=tk.LEFT)
        self.mail_provider_var = tk.StringVar(value=self.settings.mail_provider or "gmail")
        provider_box = ttk.Combobox(connector, width=8, textvariable=self.mail_provider_var, values=["gmail", "outlook"], state="readonly")
        provider_box.pack(side=tk.LEFT, padx=(8, 6))
        self.mail_account_var = tk.StringVar(value=self.settings.mail_account or "")
        self.mail_account_entry = ttk.Entry(connector, textvariable=self.mail_account_var, width=24)
        self.mail_account_entry.pack(side=tk.LEFT, padx=(0, 6))
        self.mail_password_var = tk.StringVar(value=self.settings.mail_password if self.settings.remember_mail_password else "")
        self.mail_password_entry = ttk.Entry(connector, textvariable=self.mail_password_var, show="*", width=20)
        self.mail_password_entry.pack(side=tk.LEFT, padx=(0, 6))
        self.mail_days_var = tk.StringVar(value=str(self.settings.mail_days or 30))
        self.mail_days_entry = ttk.Entry(connector, textvariable=self.mail_days_var, width=6)
        self.mail_days_entry.pack(side=tk.LEFT, padx=(0, 4))
        self.mail_days_suffix_label = ttk.Label(connector, text="\u5929")
        self.mail_days_suffix_label.pack(side=tk.LEFT, padx=(0, 6))
        self.mail_limit_var = tk.StringVar(value=str(self.settings.mail_max_messages or 200))
        self.mail_limit_entry = ttk.Entry(connector, textvariable=self.mail_limit_var, width=7)
        self.mail_limit_entry.pack(side=tk.LEFT, padx=(0, 4))
        self.mail_limit_suffix_label = ttk.Label(connector, text="\u4e0a\u9650")
        self.mail_limit_suffix_label.pack(side=tk.LEFT, padx=(0, 6))
        self.remember_mail_password_var = tk.BooleanVar(value=self.settings.remember_mail_password)
        self.remember_mail_password_check = ttk.Checkbutton(connector, text="\u8bb0\u4f4f\u5bc6\u7801", variable=self.remember_mail_password_var)
        self.remember_mail_password_check.pack(side=tk.LEFT, padx=(0, 8))
        self.pull_mail_button = ttk.Button(connector, text="\u4e00\u952e\u62c9\u53d6\u5e76\u5bfc\u5165", command=self.start_mail_pull)
        self.pull_mail_button.pack(side=tk.LEFT)
        self.mail_login_hint_label = ttk.Label(
            box,
            text="IMAP 登录：请填写邮箱账号 + 应用专用密码（不是邮箱登录密码）。",
            foreground="#555",
            justify=tk.LEFT,
        )
        self.mail_login_hint_label.pack(fill=tk.X, pady=(2, 6))

        self.progress = ttk.Progressbar(box, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X)
        self.import_status = tk.StringVar(value="\u7b49\u5f85\u5bfc\u5165")
        self.import_status_label = ttk.Label(box, textvariable=self.import_status)
        self.import_status_label.pack(fill=tk.X, pady=(6, 4))

        result_wrap = ttk.Frame(box)
        result_wrap.pack(fill=tk.BOTH, expand=True)
        self.result_text = tk.Text(result_wrap, height=8, wrap=tk.WORD)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scroll = ttk.Scrollbar(result_wrap, orient=tk.VERTICAL, command=self.result_text.yview)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=result_scroll.set)
        self.result_text.insert(tk.END, self.import_result_placeholder_zh)
        self.result_text.configure(state=tk.DISABLED)

    def _build_guide_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="\u6269\u5c55\u5b89\u88c5\u5411\u5bfc", padding=10)
        box.pack(fill=tk.X, pady=6)
        self.guide_section_box = box
        self.guide_text_var = tk.StringVar(
            value="\u6b65\u9aa4 1\uff1a\u6253\u5f00 chrome://extensions\n\u6b65\u9aa4 2\uff1a\u5f00\u542f\u5f00\u53d1\u8005\u6a21\u5f0f\n\u6b65\u9aa4 3\uff1a\u52a0\u8f7d extension \u76ee\u5f55"
        )
        ttk.Label(box, textvariable=self.guide_text_var, justify=tk.LEFT).pack(fill=tk.X)
        btns = ttk.Frame(box)
        btns.pack(fill=tk.X, pady=(8, 0))
        self.open_chrome_extensions_button = ttk.Button(btns, text="\u6253\u5f00 Chrome \u6269\u5c55\u9875", command=self.open_chrome_extensions_page)
        self.open_chrome_extensions_button.pack(side=tk.LEFT)
        self.open_extension_folder_button = ttk.Button(btns, text="\u6253\u5f00 extension \u76ee\u5f55", command=self.open_extension_folder)
        self.open_extension_folder_button.pack(side=tk.LEFT, padx=8)

    def _build_feedback_section(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="7) \u53cd\u9988", padding=10)
        box.pack(fill=tk.X, pady=6)
        self.feedback_section_box = box
        row = ttk.Frame(box)
        row.pack(fill=tk.X)
        self.feedback_var = tk.StringVar(value="")
        ttk.Entry(row, textvariable=self.feedback_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.submit_feedback_button = ttk.Button(row, text="\u63d0\u4ea4\u53cd\u9988", command=self.submit_feedback)
        self.submit_feedback_button.pack(side=tk.LEFT, padx=8)
        self.open_feedback_inbox_button = ttk.Button(row, text="\u6253\u5f00\u53cd\u9988\u6536\u4ef6\u7bb1", command=self.open_feedback_inbox)
        self.open_feedback_inbox_button.pack(side=tk.LEFT)

    def choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="\u9009\u62e9\u8f93\u51fa\u6587\u4ef6\u5939")
        if selected:
            self.output_var.set(selected)

    def save_output_dir(self) -> None:
        path = Path(self.output_var.get().strip()).expanduser().resolve()
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("\u4fdd\u5b58\u5931\u8d25", str(exc))
            return
        self.settings.output_dir = str(path)
        self.settings_store.save(self.settings)
        messagebox.showinfo("\u5df2\u4fdd\u5b58", f"\u8f93\u51fa\u6587\u4ef6\u5939\u5df2\u4fdd\u5b58\uff1a\n{path}")

    def choose_import_dir(self) -> None:
        selected = filedialog.askdirectory(title="\u9009\u62e9\u5386\u53f2\u6587\u4ef6\u5939\uff08\u53ea\u8bfb\u626b\u63cf\uff09")
        if selected:
            self.import_dir_var.set(selected)
            self.selected_import_files = []
            self.import_status.set(self._tr("\u7b49\u5f85\u5bfc\u5165", "Waiting for import"))

    def choose_import_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title=self._tr("\u9009\u62e9\u8981\u5bfc\u5165\u7684\u6587\u4ef6\uff08\u53ef\u591a\u9009\uff09", "Choose files to import (multi-select)"),
            multiple=True,
            filetypes=[
                (
                    self._tr("\u652f\u6301\u7684\u6587\u4ef6", "Supported files"),
                    "*.txt *.md *.json *.csv *.xlsx *.xls *.docx *.doc *.pdf *.pptx *.ppt",
                ),
                ("All files", "*.*"),
            ],
        )
        if not selected:
            return
        files = [Path(p).expanduser().resolve() for p in selected]
        files = [p for p in files if p.exists() and p.is_file()]
        if not files:
            messagebox.showwarning(self._tr("\u63d0\u793a", "Notice"), self._tr("\u672a\u9009\u4e2d\u6709\u6548\u6587\u4ef6\u3002", "No valid files were selected."))
            return
        self.selected_import_files = files
        self.import_dir_var.set(str(files[0].parent))
        self.import_status.set(
            self._tr(
                f"\u5df2\u9009\u6587\u4ef6 {len(files)} \u4e2a\uff0c\u53ef\u76f4\u63a5\u70b9\u51fb\u5bfc\u5165",
                f"Selected {len(files)} files. Ready to import.",
            )
        )
        preview = "\n".join(str(p) for p in files[:20])
        if len(files) > 20:
            preview += self._tr(f"\n... \u5171 {len(files)} \u4e2a\u6587\u4ef6", f"\n... total {len(files)} files")
        self._append_result(self._tr("\n[文件选择]\n", "\n[Selected files]\n") + preview + "\n")

    def clear_import_files(self) -> None:
        self.selected_import_files = []
        self.import_status.set(self._tr("\u5df2\u6e05\u7a7a\u6587\u4ef6\u9009\u62e9\uff0c\u53ef\u7ee7\u7eed\u9009\u62e9\u76ee\u5f55\u626b\u63cf", "File selection cleared. You can scan a folder now."))

    def _set_import_buttons_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.import_button.configure(state=state)
        self.incremental_button.configure(state=state)
        self.email_import_button.configure(state=state)
        self.pull_mail_button.configure(state=state)
        self.choose_import_dir_button.configure(state=state)
        self.choose_import_files_button.configure(state=state)
        self.clear_import_files_button.configure(state=state)
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
        self.service_status.set(self._tr("\u542f\u52a8\u4e2d...", "Starting..."))

        def worker() -> None:
            self._start_service_processes()
            bridge_ok = self._wait_health("http://127.0.0.1:8765/health", timeout_sec=12)
            dashboard_ok = self._wait_health("http://127.0.0.1:8787/", timeout_sec=12)
            if bridge_ok and dashboard_ok:
                msg = self._tr("\u5df2\u542f\u52a8\uff08Bridge + Dashboard\uff09", "Started (Bridge + Dashboard)")
            elif bridge_ok:
                msg = self._tr("Bridge \u5df2\u542f\u52a8\uff0cDashboard \u672a\u5c31\u7eea", "Bridge ready, Dashboard not ready")
            else:
                msg = self._tr("\u542f\u52a8\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5", "Start failed, please retry")
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
            self._runtime_cli_command(
                "serve-bridge",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
                "--allow-action-execute",
            ),
            **kwargs,
        )
        self.dashboard_process = subprocess.Popen(
            self._runtime_cli_command("serve-dashboard", "--host", "127.0.0.1", "--port", "8787"),
            **kwargs,
        )

    def _runtime_cli_command(self, *args: str) -> list[str]:
        if getattr(sys, "frozen", False):
            return [sys.executable, "cli", *args]
        return [sys.executable, "-m", "app.main", *args]

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

    def _service_watchdog_tick(self) -> None:
        if not self.keep_alive_enabled:
            return
        bridge_dead = self.bridge_process is not None and self.bridge_process.poll() is not None
        dashboard_dead = self.dashboard_process is not None and self.dashboard_process.poll() is not None
        bridge_ready = self._is_bridge_ready()
        dashboard_ready = self._is_dashboard_ready()
        if bridge_dead or dashboard_dead or not (bridge_ready and dashboard_ready):
            self.start_services()
        self.root.after(2500, self._service_watchdog_tick)

    def _on_close_request(self) -> None:
        if not messagebox.askyesno("Exit", "Close Trade Assistant desktop?"):
            return
        self.keep_alive_enabled = False
        try:
            if self.bridge_process and self.bridge_process.poll() is None:
                self.bridge_process.terminate()
            if self.dashboard_process and self.dashboard_process.poll() is None:
                self.dashboard_process.terminate()
        except OSError:
            pass
        self.root.destroy()

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
            "generate_quote_draft": "\u5df2\u751f\u6210\u62a5\u4ef7\u8349\u7a3f",
            "generate_followup_draft": "\u5df2\u751f\u6210\u8ddf\u8fdb\u8349\u7a3f",
            "ingest_email_thread": "\u5df2\u5bfc\u5165\u90ae\u4ef6\u7ebf\u7a0b",
            "conversation_sync": "\u5df2\u540c\u6b65\u5bf9\u8bdd\u8bb0\u5fc6",
        }
        return mapping.get(action_name, action_name or "\u672a\u77e5\u52a8\u4f5c")

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
            customer = self._extract_customer_from_event(e) or "\u672a\u77e5\u5ba2\u6237"
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
                + (f"\uff08\u5ba2\u6237: {customer}\uff0c\u4ea7\u54c1: {product}\uff09" if product else f"\uff08\u5ba2\u6237: {customer}\uff09")
            )

        ranked = sorted(
            customer_stats.items(),
            key=lambda item: (item[1]["quotes"], item[1]["followups"], item[1]["last_time"]),
            reverse=True,
        )

        view_lines: list[str] = [
            f"\u68c0\u7d22\u8bcd: {query}",
            "",
            f"\u5ba2\u6237\u547d\u4e2d: {len(customer_hits)}",
        ]
        for c in customer_hits[:6]:
            view_lines.append(f"- {c.name} ({c.customer_id}) | \u5730\u533a: {c.region or '-'} | \u5e01\u79cd: {c.currency}")
        view_lines.extend(["", f"\u4ea7\u54c1\u547d\u4e2d: {len(product_hits)}"])
        for p in product_hits[:6]:
            view_lines.append(f"- {p.sku} | {p.name}")
        view_lines.extend(["", f"\u5386\u53f2\u8bb0\u5fc6\u547d\u4e2d: {len(doc_hits)}"])
        for d in doc_hits[:8]:
            view_lines.append(f"- {d}")
        view_lines.extend(["", f"\u6210\u4ea4/\u52a8\u4f5c\u8bb0\u5f55\u547d\u4e2d: {len(event_hits)}"])

        if ranked:
            view_lines.append("\u5ba2\u6237\u805a\u5408\u6458\u8981:")
            for customer, stats in ranked[:8]:
                products = list(stats["products"])[:3]
                product_text = f"\uff0c\u76f8\u5173\u4ea7\u54c1: {', '.join(products)}" if products else ""
                view_lines.append(
                    f"- {customer} | \u62a5\u4ef7 {stats['quotes']} \u6b21 | \u8ddf\u8fdb {stats['followups']} \u6b21 | \u6700\u8fd1 {stats['last_time']}{product_text}"
                )

        cross_ranked = sorted(
            cross_stats.items(),
            key=lambda item: (item[1]["quotes"], item[1]["followups"], item[1]["last_time"]),
            reverse=True,
        )
        if cross_ranked:
            view_lines.append("\u6210\u4ea4\u6863\u6848\u89c6\u56fe\uff08\u5ba2\u6237 \u00d7 \u4ea7\u54c1\uff09:")
            for (customer, product), stats in cross_ranked[:12]:
                view_lines.append(
                    f"- {customer} \u00d7 {product} | \u62a5\u4ef7 {stats['quotes']} \u6b21 | \u8ddf\u8fdb {stats['followups']} \u6b21 | \u6700\u8fd1 {stats['last_time']}"
                )

        if event_lines:
            view_lines.append("\u6700\u8fd1\u8bed\u4e49\u4e8b\u4ef6:")
            view_lines.extend(event_lines[:8])

        if not customer_hits and not product_hits and not doc_hits and not event_hits:
            view_lines.append("- \u65e0\u547d\u4e2d\uff0c\u8bf7\u66f4\u6362\u5173\u952e\u8bcd\u6216\u5148\u5bfc\u5165\u66f4\u591a\u5386\u53f2\u8d44\u6599\u3002")

        capsule_lines = [f"\u96f7\u8fbe\u68c0\u7d22\u8bcd: {query}", "\u96f7\u8fbe\u6458\u8981:"]
        for customer, stats in ranked[:6]:
            capsule_lines.append(
                f"- \u5ba2\u6237 {customer}: \u62a5\u4ef7{stats['quotes']}\u6b21 \u8ddf\u8fdb{stats['followups']}\u6b21 \u6700\u8fd1\u8bb0\u5f55{stats['last_time']}"
            )
        for (customer, product), stats in cross_ranked[:8]:
            capsule_lines.append(
                f"- \u6210\u4ea4\u6863\u6848 {customer} \u00d7 {product}: \u62a5\u4ef7{stats['quotes']}\u6b21 \u8ddf\u8fdb{stats['followups']}\u6b21 \u6700\u8fd1{stats['last_time']}"
            )
        for d in doc_hits[:6]:
            capsule_lines.append(f"- \u5386\u53f2\u4e8b\u5b9e: {d}")
        capsule_lines.extend(event_lines[:6])

        return "\n".join(view_lines), "\n".join(capsule_lines)

    def _history_import_state_path(self) -> Path:
        return self.config.data_dir / "history_import_state.json"

    def _load_history_import_state(self) -> dict:
        path = self._history_import_state_path()
        if not path.exists():
            return {"roots": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"roots": {}}
        if not isinstance(data, dict):
            return {"roots": {}}
        roots = data.get("roots", {})
        if not isinstance(roots, dict):
            return {"roots": {}}
        return {"roots": roots}

    def _save_history_import_state(self, state: dict) -> None:
        path = self._history_import_state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _file_signature(self, path: Path) -> dict | None:
        try:
            stat = path.stat()
        except OSError:
            return None
        return {"mtime_ns": int(stat.st_mtime_ns), "size": int(stat.st_size)}

    def _filter_incremental_history_files(
        self,
        root_dir: Path,
        files: list[Path],
    ) -> tuple[list[Path], dict, dict[str, dict], int]:
        state = self._load_history_import_state()
        roots = state.setdefault("roots", {})
        root_key = str(root_dir)
        root_state = roots.get(root_key, {})
        if not isinstance(root_state, dict):
            root_state = {}
        selected: list[Path] = []
        signatures: dict[str, dict] = {}
        unchanged = 0
        for path in files:
            sig = self._file_signature(path)
            if sig is None:
                selected.append(path)
                continue
            path_key = str(path)
            signatures[path_key] = sig
            if root_state.get(path_key) != sig:
                selected.append(path)
            else:
                unchanged += 1
        roots[root_key] = root_state
        return selected, state, signatures, unchanged

    def run_radar_search(self) -> None:
        query = self.radar_query_var.get().strip()
        if not query:
            messagebox.showinfo("\u63d0\u793a", "\u8bf7\u8f93\u5165\u5173\u952e\u8bcd\u3002")
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
            messagebox.showinfo("\u63d0\u793a", "\u8bf7\u5148\u8f93\u5165\u68c0\u7d22\u8bcd\u3002")
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
        self.radar_result.insert(tk.END, "\n\n--- \u751f\u6210\u80f6\u56ca ---\n")
        self.radar_result.insert(tk.END, text + "\n")
        self.radar_result.configure(state=tk.DISABLED)
        self.radar_result.see(tk.END)

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("\u5df2\u751f\u6210", "\u80f6\u56ca\u5df2\u590d\u5236\u5230\u526a\u8d34\u677f\uff0c\u53ef\u76f4\u63a5\u7c98\u8d34\u5230\u5927\u6a21\u578b\u8f93\u5165\u6846\u3002")
        except tk.TclError:
            messagebox.showinfo("\u5df2\u751f\u6210", "\u80f6\u56ca\u5df2\u751f\u6210\uff0c\u8bf7\u5728\u7ed3\u679c\u533a\u590d\u5236\u3002")

    def start_import(self, mode: str = "full") -> None:
        source = self.import_dir_var.get().strip()
        selected_files = [p for p in self.selected_import_files if p.exists() and p.is_file()]
        if not source and not selected_files:
            messagebox.showwarning("\u63d0\u793a", "\u8bf7\u5148\u9009\u62e9\u5386\u53f2\u6587\u4ef6\u5939\u3002")
            return
        root_dir = Path(source).expanduser().resolve() if source else selected_files[0].parent
        if not selected_files and (not root_dir.exists() or not root_dir.is_dir()):
            messagebox.showerror("\u9519\u8bef", "\u5386\u53f2\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\u3002")
            return

        self._set_import_buttons_busy(True)
        self.progress.configure(value=0, maximum=1)
        if mode == "incremental":
            self.import_status.set(self._tr("\u6b63\u5728\u5bfc\u5165\u65b0\u589e\u8d44\u6599...", "Importing incremental files..."))
            if selected_files:
                self._append_result(self._tr(f"\n开始增量导入（已选文件 {len(selected_files)} 个）\n", f"\nStart incremental import (selected files: {len(selected_files)})\n"))
            else:
                self._append_result(f"\n\u5f00\u59cb\u589e\u91cf\u5bfc\u5165\uff1a{root_dir}\n")
            max_files = 600
        else:
            self.import_status.set(self._tr("\u6b63\u5728\u5168\u91cf\u626b\u63cf...", "Running full scan..."))
            if selected_files:
                self._append_result(self._tr(f"\n开始全量导入（已选文件 {len(selected_files)} 个）\n", f"\nStart full import (selected files: {len(selected_files)})\n"))
            else:
                self._append_result(f"\n\u5f00\u59cb\u5168\u91cf\u5bfc\u5165\uff1a{root_dir}\n")
            max_files = 1500

        def worker() -> None:
            try:
                scanned_files = selected_files if selected_files else scan_history_files(root_dir, recursive=True, max_files=max_files)
                files = scanned_files
                state: dict | None = None
                signatures: dict[str, dict] = {}
                unchanged_files = 0
                if mode == "incremental":
                    files, state, signatures, unchanged_files = self._filter_incremental_history_files(root_dir, scanned_files)
                    if not files:
                        result = {
                            "scanned_files": len(scanned_files),
                            "imported_files": 0,
                            "skipped_files": 0,
                            "extracted_facts": 0,
                            "duplicate_skipped": 0,
                            "failed_files": [],
                            "no_change": True,
                            "unchanged_files": unchanged_files,
                        }
                        self.root.after(0, lambda r=result: self._finish_import(r, mode=mode))
                        return
                total = max(1, len(files))
                self.root.after(0, lambda: self.progress.configure(value=0, maximum=total))

                def on_progress(event: dict) -> None:
                    self.root.after(
                        0,
                        lambda: (
                            self.progress.configure(value=event.get("current", 0)),
                            self.import_status.set(
                                self._tr(
                                    f"\u5904\u7406\u4e2d {event.get('current', 0)}/{event.get('total', 0)} | \u6210\u529f\u6587\u4ef6 {event.get('imported_files', 0)} | \u8bb0\u5fc6 {event.get('facts', 0)} | \u5931\u8d25 {event.get('failed_files', 0)}",
                                    f"Processing {event.get('current', 0)}/{event.get('total', 0)} | Imported files {event.get('imported_files', 0)} | Facts {event.get('facts', 0)} | Failed {event.get('failed_files', 0)}",
                                )
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
                if mode == "incremental" and state is not None:
                    roots = state.setdefault("roots", {})
                    root_key = str(root_dir)
                    root_state = roots.setdefault(root_key, {})
                    failed = {str(Path(p)) for p in (stats.failed_files or []) if p}
                    for path in files:
                        path_key = str(path)
                        if path_key in failed:
                            continue
                        sig = signatures.get(path_key)
                        if sig:
                            root_state[path_key] = sig
                    try:
                        self._save_history_import_state(state)
                    except OSError:
                        pass
                self.last_failed_files = [Path(p) for p in (stats.failed_files or []) if p]
                result = stats.to_dict()
                if mode == "incremental":
                    result["unchanged_files"] = unchanged_files
                self.root.after(0, lambda r=result: self._finish_import(r, mode=mode))
            except Exception as exc:  # pragma: no cover
                self.root.after(0, lambda e=exc: self._finish_import_error(e))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_import_error(self, exc: Exception) -> None:
        self._set_import_buttons_busy(False)
        self.import_status.set(self._tr("\u5bfc\u5165\u5931\u8d25", "Import failed"))
        self._append_result(self._tr("\n[错误] ", "\n[Error] ") + str(exc) + "\n")
        messagebox.showerror(self._tr("\u5bfc\u5165\u5931\u8d25", "Import failed"), str(exc))

    def retry_failed(self) -> None:
        if not self.last_failed_files:
            messagebox.showinfo("\u63d0\u793a", "\u5f53\u524d\u6ca1\u6709\u5931\u8d25\u6587\u4ef6\u53ef\u91cd\u8bd5\u3002")
            return

        self._set_import_buttons_busy(True)

        total = max(1, len(self.last_failed_files))
        self.progress.configure(value=0, maximum=total)
        self.import_status.set(self._tr("\u6b63\u5728\u91cd\u8bd5\u5931\u8d25\u6587\u4ef6...", "Retrying failed files..."))

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
            messagebox.showwarning("\u63d0\u793a", "\u8bf7\u5148\u9009\u62e9\u90ae\u4ef6\u6587\u4ef6\u5939\u3002")
            return
        root_dir = Path(source).expanduser().resolve()
        if not root_dir.exists() or not root_dir.is_dir():
            messagebox.showerror("\u9519\u8bef", "\u90ae\u4ef6\u6587\u4ef6\u5939\u4e0d\u5b58\u5728\u3002")
            return

        self._set_import_buttons_busy(True)
        self.progress.configure(value=0, maximum=1)
        self.import_status.set(self._tr("\u6b63\u5728\u6279\u91cf\u5bfc\u5165\u90ae\u4ef6\u7ebf\u7a0b...", "Batch importing mail threads..."))
        self._append_result(f"\n\u5f00\u59cb\u90ae\u4ef6\u6279\u91cf\u5bfc\u5165\uff1a{root_dir}\n")

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
                            self._tr(
                                f"\u90ae\u4ef6\u5bfc\u5165 {event.get('current', 0)}/{event.get('total', 0)} | \u6210\u529f {event.get('imported_files', 0)} | \u8bb0\u5fc6 {event.get('facts', 0)} | \u5931\u8d25 {event.get('failed_files', 0)}",
                                f"Mail import {event.get('current', 0)}/{event.get('total', 0)} | Imported {event.get('imported_files', 0)} | Facts {event.get('facts', 0)} | Failed {event.get('failed_files', 0)}",
                            )
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
            messagebox.showinfo("\u63d0\u793a", "\u5f53\u524d\u6ca1\u6709\u5931\u8d25\u90ae\u4ef6\u6587\u4ef6\u53ef\u91cd\u8bd5\u3002")
            return

        self._set_import_buttons_busy(True)
        total = max(1, len(self.last_failed_email_files))
        self.progress.configure(value=0, maximum=total)
        self.import_status.set(self._tr("\u6b63\u5728\u91cd\u8bd5\u5931\u8d25\u90ae\u4ef6\u6587\u4ef6...", "Retrying failed mail files..."))

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
            messagebox.showwarning("\u63d0\u793a", "\u8bf7\u5148\u8f93\u5165\u90ae\u7bb1\u8d26\u53f7\u3002")
            return
        if not password:
            messagebox.showwarning("\u63d0\u793a", "\u8bf7\u5148\u8f93\u5165\u90ae\u7bb1\u5bc6\u7801\uff08\u5efa\u8bae\u5e94\u7528\u4e13\u7528\u5bc6\u7801\uff09\u3002")
            return
        try:
            days = max(1, min(int(self.mail_days_var.get().strip() or "30"), 3650))
            max_messages = max(1, min(int(self.mail_limit_var.get().strip() or "200"), 5000))
        except ValueError:
            messagebox.showwarning("\u63d0\u793a", "\u62c9\u53d6\u5929\u6570\u548c\u5c01\u6570\u9700\u4e3a\u6570\u5b57\u3002")
            return

        remember_password = bool(self.remember_mail_password_var.get())
        self._save_mail_settings(remember_password=remember_password, password=password)
        self._set_import_buttons_busy(True)
        self.progress.configure(value=0, maximum=1)
        self.import_status.set(self._tr("\u6b63\u5728\u62c9\u53d6\u90ae\u7bb1\u90ae\u4ef6\u5e76\u5bfc\u5165...", "Pulling mailbox and importing..."))
        self._append_result(f"\n\u5f00\u59cb\u90ae\u7bb1\u62c9\u53d6\uff1aprovider={provider}, account={account}, days={days}, max={max_messages}\n")

        def worker() -> None:
            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            pull_dir = self.config.data_dir / "mail_sync" / f"{provider}_{ts}"

            def on_pull_progress(event: dict) -> None:
                self.root.after(
                    0,
                    lambda: (
                        self.progress.configure(value=event.get("current", 0), maximum=max(1, event.get("total", 1))),
                        self.import_status.set(
                            self._tr(
                                f"\u90ae\u7bb1\u62c9\u53d6 {event.get('current', 0)}/{event.get('total', 0)} | \u6210\u529f {event.get('pulled_messages', 0)} | \u5931\u8d25 {event.get('failed_messages', 0)}",
                                f"Mailbox pull {event.get('current', 0)}/{event.get('total', 0)} | Pulled {event.get('pulled_messages', 0)} | Failed {event.get('failed_messages', 0)}",
                            )
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
        if not retry and int(result.get("scanned_files", 0)) == 0:
            self.import_status.set(
                self._tr(
                    "导入完成：未识别到可导入文件（支持 txt/md/json/csv/xlsx/xls/docx/doc/pdf/pptx/ppt）",
                    "Import complete: no supported files found (txt/md/json/csv/xlsx/xls/docx/doc/pdf/pptx/ppt)",
                )
            )
            self._append_result(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            return
        if mode == "incremental" and not retry and bool(result.get("no_change")):
            unchanged = int(result.get("unchanged_files", 0))
            self.import_status.set(
                self._tr(
                    f"增量导入完成：未发现新增或变更文件（共检查 {unchanged} 个）",
                    f"Incremental import complete: no new or changed files (checked {unchanged})",
                )
            )
            self._append_result(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            return

        tag = self._tr("\u91cd\u8bd5\u5b8c\u6210", "Retry complete") if retry else self._tr("\u5bfc\u5165\u5b8c\u6210", "Import complete")
        self.import_status.set(
            self._tr(
                f"{tag}\uff1a\u626b\u63cf{result.get('scanned_files', 0)}\uff0c\u6210\u529f{result.get('imported_files', 0)}\uff0c\u65b0\u589e\u8bb0\u5fc6{result.get('extracted_facts', 0)}\uff0c\u91cd\u590d\u8df3\u8fc7{result.get('duplicate_skipped', 0)}\uff0c\u5931\u8d25{len(result.get('failed_files', []))}",
                f"{tag}: scanned {result.get('scanned_files', 0)}, imported {result.get('imported_files', 0)}, new facts {result.get('extracted_facts', 0)}, duplicates skipped {result.get('duplicate_skipped', 0)}, failed {len(result.get('failed_files', []))}",
            )
        )
        if not retry:
            messagebox.showinfo(
                "\u5bfc\u5165\u5b8c\u6210",
                (
                    f"\u672c\u6b21\u626b\u63cf {result.get('scanned_files', 0)} \u4e2a\u6587\u4ef6\n"
                    f"\u65b0\u589e\u8bb0\u5fc6 {result.get('extracted_facts', 0)} \u6761\n"
                    f"\u91cd\u590d\u8df3\u8fc7 {result.get('duplicate_skipped', 0)} \u6761\uff08\u81ea\u52a8\u53bb\u91cd\uff09\n"
                    f"\u5931\u8d25\u6587\u4ef6 {len(result.get('failed_files', []))} \u4e2a"
                ),
            )
        self._append_result(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    def _finish_email_import(self, result: dict, retry: bool = False) -> None:
        self._set_import_buttons_busy(False)
        tag = self._tr("\u90ae\u4ef6\u91cd\u8bd5\u5b8c\u6210", "Mail retry complete") if retry else self._tr("\u90ae\u4ef6\u5bfc\u5165\u5b8c\u6210", "Mail import complete")
        self.import_status.set(
            self._tr(
                f"{tag}\uff1a\u626b\u63cf{result.get('scanned_files', 0)}\uff0c\u6210\u529f{result.get('imported_files', 0)}\uff0c\u8df3\u8fc7{result.get('skipped_files', 0)}\uff0c\u65b0\u589e\u8bb0\u5fc6{result.get('extracted_facts', 0)}\uff0c\u91cd\u590d\u8df3\u8fc7{result.get('duplicate_skipped', 0)}\uff0c\u5931\u8d25{len(result.get('failed_files', []))}",
                f"{tag}: scanned {result.get('scanned_files', 0)}, imported {result.get('imported_files', 0)}, skipped {result.get('skipped_files', 0)}, new facts {result.get('extracted_facts', 0)}, duplicates skipped {result.get('duplicate_skipped', 0)}, failed {len(result.get('failed_files', []))}",
            )
        )
        if not retry:
            messagebox.showinfo(
                "\u90ae\u4ef6\u5bfc\u5165\u5b8c\u6210",
                (
                    f"\u672c\u6b21\u626b\u63cf {result.get('scanned_files', 0)} \u4e2a\u90ae\u4ef6\u6587\u4ef6\n"
                    f"\u6210\u529f\u5bfc\u5165 {result.get('imported_files', 0)} \u4e2a\n"
                    f"\u65b0\u589e\u8bb0\u5fc6 {result.get('extracted_facts', 0)} \u6761\n"
                    f"\u91cd\u590d\u8df3\u8fc7 {result.get('duplicate_skipped', 0)} \u6761\n"
                    f"\u5931\u8d25\u6587\u4ef6 {len(result.get('failed_files', []))} \u4e2a"
                ),
            )
        self._append_result(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    def _finish_mail_pull(self, pull_result: dict, ingest_result: dict) -> None:
        self._set_import_buttons_busy(False)
        if pull_result.get("error"):
            raw_error = str(pull_result.get("error"))
            self.import_status.set(self._tr(f"\u90ae\u7bb1\u62c9\u53d6\u5931\u8d25\uff1a{raw_error}", f"Mailbox pull failed: {raw_error}"))
            messagebox.showerror(
                "\u62c9\u53d6\u5931\u8d25",
                self._mail_login_help(raw_error),
            )
            return
        self.import_status.set(
            self._tr(
                f"\u90ae\u7bb1\u62c9\u53d6\u5b8c\u6210\uff1a\u62c9\u53d6{pull_result.get('pulled_messages', 0)} \u5c01\uff0c\u5bfc\u5165 {ingest_result.get('imported_files', 0)} \u5c01\uff0c\u5931\u8d25 {len(ingest_result.get('failed_files', []))}",
                f"Mailbox pull complete: pulled {pull_result.get('pulled_messages', 0)}, imported {ingest_result.get('imported_files', 0)}, failed {len(ingest_result.get('failed_files', []))}",
            )
        )
        messagebox.showinfo(
            "\u62c9\u53d6\u5e76\u5bfc\u5165\u5b8c\u6210",
            (
                f"\u62c9\u53d6\u90ae\u4ef6 {pull_result.get('pulled_messages', 0)} \u5c01\n"
                f"\u5bfc\u5165\u6210\u529f {ingest_result.get('imported_files', 0)} \u5c01\n"
                f"\u65b0\u589e\u8bb0\u5fc6 {ingest_result.get('extracted_facts', 0)} \u6761\n"
                f"\u5931\u8d25\u6587\u4ef6 {len(ingest_result.get('failed_files', []))} \u4e2a"
            ),
        )
        self._append_result(
            json.dumps({"pull": pull_result, "ingest": ingest_result}, ensure_ascii=False, indent=2) + "\n"
        )

    def _mail_login_help(self, raw_error: str) -> str:
        low = raw_error.lower()
        if any(k in low for k in ["authentication", "login failed", "invalid credentials", "auth", "username and password not accepted"]):
            return self._tr(
                "邮箱登录失败。\n当前为 IMAP 登录，不会弹网页登录。\n请填写：邮箱账号 + 应用专用密码（不是邮箱登录密码）。\n\n原始错误："
                + raw_error,
                "Mailbox login failed.\nThis app uses IMAP login (no web OAuth popup).\nPlease use mailbox account + app password (not your normal mailbox password).\n\nRaw error: "
                + raw_error,
            )
        return raw_error

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
